# lru_cache: memoriza o resultado de get_model() (carrega o ficheiro só 1 vez)
from functools import lru_cache
# Annotated: junta um tipo com metadados (aqui: Depends do FastAPI)
from typing import Annotated

import joblib
# Depends: injecção de dependências (passa o modelo aos endpoints automaticamente)
# FastAPI: framework da API HTTP | HTTPException: erros com código HTTP (ex. 422)
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
# FileResponse: devolve um ficheiro (a página) | StaticFiles: serve CSS/JS da pasta static/
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
# BaseModel: schema de pedido/resposta | Field: validação (min/max, etc.)
from pydantic import BaseModel, Field

from salary_predictor.features import (
    CATS, DEFAULT_DEV_TYPE, DEFAULT_LANGS, DESCONHECIDO, LANGS, MODEL, make_row, to_frame,
)

from salary_predictor.compare_radar import USD_PARA_EUR, anos, funcao
from salary_predictor.localizacao import pais, prever_usd

# Cria a app; o título aparece na documentação automática (/docs)
app = FastAPI(title="Salary Predictor")

# Interface web (HTML + CSS + JS simples, sem build) — servida pela própria API
STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")

# Erro médio do Random Forest em validação cruzada 5-fold, por região (ver README e
# `train --compare`). A página usa-o para mostrar a margem típica da previsão.
MAE_USD_EUROPA = 26_139
MAE_USD_EUA = 45_325
# Anos mostrados no gráfico de evolução da página
ANOS_CURVA = list(range(0, 31))


@lru_cache
def get_model():
    """Carrega o modelo só no primeiro pedido (e não ao importar o módulo)."""
    return joblib.load(MODEL)


# Atalho de tipo: nos endpoints, `model: Model` = FastAPI chama get_model() e injeta
Model = Annotated[object, Depends(get_model)]


def opcoes(model) -> dict[str, list[str]]:
    """Valores aceites para cada campo categórico, tirados do encoder treinado."""
    # Navega no pipeline: TransformedTarget → Pipeline → ColumnTransformer → OneHotEncoder
    encoder = model.regressor_.named_steps["prep"].named_transformers_["cat"]
    # Para cada coluna em CATS, lista as categorias que o encoder viu no treino
    return {col: sorted(map(str, cats)) for col, cats in zip(CATS, encoder.categories_)}


class Perfil(BaseModel):
    """Corpo do POST /predict — o perfil da pessoa a prever."""
    country: str = "Portugal"
    years: float = Field(ge=0, le=50)  # anos de experiência entre 0 e 50
    dev_type: str = DEFAULT_DEV_TYPE
    ed_level: str = DESCONHECIDO  # educação (opcional)
    remote_work: str = DESCONHECIDO  # remoto/híbrido/presencial (opcional)
    langs: list[str] = DEFAULT_LANGS  # lista JSON, ex.: ["Python", "SQL"]


class Previsao(BaseModel):
    """Resposta do POST /predict."""
    salario_anual_usd: int
    salario_mensal_usd: int


class Curva(BaseModel):
    """Resposta do POST /curve — salário previsto para cada ano de experiência."""
    anos: list[int]
    salario_anual_usd: list[int]


class Meta(BaseModel):
    """Constantes de que a página precisa (conversão de moeda e margem de erro)."""
    usd_para_eur: float
    mae_usd_europa: int
    mae_usd_eua: int


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Página com o formulário e o salário estimado."""
    return FileResponse(STATIC / "index.html")


@app.get("/meta", response_model=Meta)
def meta() -> Meta:
    """Taxa USD→EUR e erro médio do modelo, para a página."""
    return Meta(usd_para_eur=USD_PARA_EUR, mae_usd_europa=MAE_USD_EUROPA, mae_usd_eua=MAE_USD_EUA)


@app.get("/health")
def health() -> dict:
    """Healthcheck simples: a API está de pé?"""
    return {"ok": True}


@app.get("/options")
def options(model: Model) -> dict[str, list[str]]:
    """Devolve países/níveis/etc. válidos + linguagens suportadas (para o frontend)."""
    return {**opcoes(model), "langs": LANGS}


def validar(p: Perfil, model) -> None:
    """Dá erro 422 se o perfil tiver categorias ou linguagens que o modelo não conhece."""
    validos = opcoes(model)  # categorias que o modelo conhece
    # Mapeia campos do pedido → nomes das colunas do encoder
    campos = {"Country": p.country, "EdLevel": p.ed_level,
              "RemoteWork": p.remote_work, "DevType": p.dev_type}
    # Lista de erros se algum valor categórico for desconhecido
    erros = [f"{col}: {valor!r} não é um valor conhecido (ver GET /options)"
             for col, valor in campos.items() if valor not in validos[col]]
    # Também rejeita linguagens fora da lista LANGS
    erros += [f"langs: {l!r} não é suportada (opções: {', '.join(LANGS)})"
              for l in p.langs if l not in LANGS]
    if erros:
        # 422 = Unprocessable Entity (dados inválidos)
        raise HTTPException(status_code=422, detail=erros)


@app.post("/predict", response_model=Previsao)
def predict(p: Perfil, model: Model) -> Previsao:
    """Recebe um perfil, valida categorias/langs e devolve salário anual e mensal."""
    validar(p, model)
    # Monta a linha no formato do treino e pede a previsão
    row = make_row(p.country, p.years, p.dev_type, p.langs, p.ed_level, p.remote_work)
    anual = float(model.predict(to_frame([row]))[0])
    # round() → inteiros limpos para a resposta JSON
    return Previsao(salario_anual_usd=round(anual), salario_mensal_usd=round(anual / 12))


@app.post("/curve", response_model=Curva)
def curve(p: Perfil, model: Model) -> Curva:
    """Salário previsto de 0 a 30 anos de experiência para o mesmo perfil (o campo years é ignorado)."""
    validar(p, model)
    # Uma só chamada ao modelo com 21 linhas, em vez de 21 pedidos
    rows = [make_row(p.country, a, p.dev_type, p.langs, p.ed_level, p.remote_work)
            for a in ANOS_CURVA]
    previsoes = model.predict(to_frame(rows))
    return Curva(anos=ANOS_CURVA, salario_anual_usd=[round(float(v)) for v in previsoes])


# Estimativa de salário para uma oferta do Radar
class Oferta(BaseModel):
    """Corpo do POST /estimate — uma oferta do Radar e o perfil de quem a vê."""
    title: str
    years: float | None = Field(default=None, ge=0, le=50)  # se faltar, deduz do título
    skills: list[str] = []  # skills do CV; só contam as que estão em LANGS
    # Localização da oferta em texto livre ("Lisboa", "Remoto (USA)", "Remoto (Anywhere)"...).
    # Sem localização ou não reconhecida → Portugal. Ver localizacao.py.
    location: str | None = Field(default=None, max_length=200)

# Resposta do POST /estimate
class Estimativa(BaseModel):
    salario_anual_eur: int
    # País usado na estimativa, ou "Europe" (mediana dos países europeus) para remoto sem país
    base: str

# Endpoint para estimar o salário para uma oferta do Radar
@app.post("/estimate", response_model=Estimativa)
def estimate(o: Oferta, model: Model) -> Estimativa:
    """Salário anual estimado (€) para uma oferta, no país indicado pela localização."""
    skills = {s.lower() for s in o.skills}
    langs = [lang for lang in LANGS if lang.lower() in skills]
    years = o.years if o.years is not None else anos(o.title)
    base = pais(o.location)
    eur = prever_usd(model, base, years, funcao(o.title), langs) * USD_PARA_EUR
    return Estimativa(salario_anual_eur=int(round(eur, -3)), base=base)
