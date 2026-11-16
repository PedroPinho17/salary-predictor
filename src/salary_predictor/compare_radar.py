"""Compara as previsões do modelo com ofertas reais recolhidas pelo Radar.

Precisa de DATABASE_URL (variável de ambiente ou ficheiro .env). Para usar o .env
de outro projeto, aponta RADAR_ENV_FILE para ele.
"""

import argparse  # flags da CLI (--compare)
import os  # ler variáveis de ambiente (DATABASE_URL, RADAR_ENV_FILE)
import re  # regex para detetar função/nível/linguagens no título e descrição

import joblib  # carregar o modelo .joblib guardado
import pandas as pd
import psycopg  # ligar à base Postgres do Radar
from dotenv import load_dotenv  # carregar .env para ter DATABASE_URL

from salary_predictor.features import MODEL, make_row, to_frame
# MODELOS / build / load: para --compare treinar vários modelos no survey
from salary_predictor.train import MODELOS, build, load

USD_PARA_EUR = 0.87  # taxa aproximada (modelo prevê USD; ofertas do Radar estão em EUR)
# Abaixo disto, um "salário anual" é quase de certeza um valor mensal mal classificado
MINIMO_ANUAL_EUR = 6_000

# Mapeia palavras no título da oferta → DevType do survey Stack Overflow
# A primeira regex que bater ganha (ordem importa)
FUNCOES = [
    (r"\bdata scien", "Data scientist"),
    (r"\bdata engineer", "Data engineer"),
    (r"\b(ai|ml|machine learning)\b", "AI/ML engineer"),
    (r"\bdevops\b", "DevOps engineer or professional"),
    (r"\binfrastructure\b", "Cloud infrastructure engineer"),
    (r"\bnetwork", "System administrator"),
    (r"\bsecurity\b", "Cybersecurity or InfoSec professional"),
    (r"\barchitect", "Architect, software or solutions"),
    (r"\b(test|qa\b)", "Developer, QA or test"),
    (r"\b(ios|android|mobile)\b", "Developer, mobile"),
    (r"\bembedded\b", "Developer, embedded applications or devices"),
    (r"\bfront[- ]?end\b", "Developer, front-end"),  # front-end / frontend / front end
    (r"\bback[- ]?end\b", "Developer, back-end"),
    (r"\bconsult", "Support engineer or analyst"),
    (r"\banalyst\b", "Data or business analyst"),
]

# Regex por linguagem — com fronteiras de palavra para evitar falsos positivos
# (ex.: "Java" não apanha "JavaScript"; "Go" não apanha "Google")
LANG_PATTERNS = {
    "Python": re.compile(r"\bpython\b", re.I),  # re.I = ignora maiúsculas/minúsculas
    "JavaScript": re.compile(r"\b(javascript|js|node\.?js)\b", re.I),
    "TypeScript": re.compile(r"\btypescript\b", re.I),
    "Java": re.compile(r"\bjava\b", re.I),
    "C#": re.compile(r"(?<![\w#])c#(?!\w)|\.net\b", re.I),  # C# ou .NET
    "SQL": re.compile(r"(?<![a-z])(my|postgre|ms|t-|pl/)?sql\b", re.I),  # exclui NoSQL
    "Go": re.compile(r"\bGo\b|\b[Gg]olang\b"),  # "go" minúsculo é verbo → só Go/Golang
    "Rust": re.compile(r"\brust\b", re.I),
    "PHP": re.compile(r"\bphp\b", re.I),
}


def funcao(titulo: str) -> str:
    """Infere o DevType a partir do título da oferta (fallback: full-stack)."""
    t = titulo.lower()
    for padrao, dev_type in FUNCOES:
        if re.search(padrao, t):
            return dev_type
    return "Developer, full-stack"


def anos(titulo: str) -> float:
    """Heurística de experiência: júnior→1, sénior/lead→7, resto→3."""
    t = titulo.lower()
    if re.search(r"\bj[uú]nior\b", t):  # junior / júnior
        return 1
    if re.search(r"\b(s[eé]nior|lead)\b", t):  # senior / sénior / lead
        return 7
    return 3  # mid por omissão


def linguagens(texto: str | None) -> list[str]:
    """Extrai linguagens mencionadas na descrição (lista vazia se não houver texto)."""
    if not texto:
        return []
    return [lang for lang, pat in LANG_PATTERNS.items() if pat.search(texto)]


def ofertas() -> pd.DataFrame:
    """Lê do Postgres do Radar as ofertas que têm salário (min e/ou max)."""
    # Se RADAR_ENV_FILE estiver definido, carrega esse .env; senão o .env local
    load_dotenv(os.environ.get("RADAR_ENV_FILE"))
    sql = """
        select source, title, description, "salaryMin", "salaryMax"
        from jobs where "salaryMin" is not null or "salaryMax" is not null
    """
    # Abre ligação, lê para DataFrame, fecha automaticamente ao sair do with
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        return pd.read_sql(sql, conn)


def features(df: pd.DataFrame) -> pd.DataFrame:
    """Converte cada oferta numa linha de features no formato do modelo.

    Assume Portugal (Radar PT); anos/função do título; langs da descrição.
    """
    return to_frame([
        make_row("Portugal", anos(o.title), funcao(o.title), linguagens(o.description))
        for o in df.itertuples()  # itertuples = percorrer linhas de forma eficiente
    ])


def main() -> None:
    """Compara previsões vs salários reais das ofertas do Radar."""
    # description = primeira linha do docstring do módulo
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--compare", action="store_true",
                   help="treina todos os modelos no survey e compara-os (em vez de usar o modelo guardado)")
    a = p.parse_args()

    df = ofertas()
    # Salário "real" = média entre min e max da oferta (EUR)
    df["real_eur"] = df[["salaryMin", "salaryMax"]].mean(axis=1)

    # Filtra valores demasiado baixos (provavelmente mensais marcados como anuais)
    suspeitas = df[df["real_eur"] < MINIMO_ANUAL_EUR]
    if len(suspeitas):
        print(f"Aviso: {len(suspeitas)} ofertas com salário < {MINIMO_ANUAL_EUR:,} €/ano "
              "(provavelmente mensal) foram excluídas:")
        print(suspeitas[["source", "title", "real_eur"]].to_string(index=False), "\n")
        df = df[df["real_eur"] >= MINIMO_ANUAL_EUR].reset_index(drop=True)

    X = features(df)  # matriz de features para o modelo prever
    if a.compare:
        # Treina de novo cada modelo do survey e compara todos nas ofertas
        X_survey, y_survey = load()
        modelos = {k: build(k).fit(X_survey, y_survey) for k in MODELOS}
    else:
        # Usa só o modelo já guardado em models/salary_model.joblib
        modelos = {"guardado": joblib.load(MODEL)}

    pd.set_option("display.width", 140)  # tabelas mais largas no terminal
    for nome, model in modelos.items():
        # Modelo prevê USD → converte para EUR para comparar com o Radar
        df["previsto_eur"] = model.predict(X) * USD_PARA_EUR
        df["diferenca"] = df["previsto_eur"] - df["real_eur"]  # + = modelo acima do real
        print(f"=== {nome}")
        # Mostra tabela; título cortado a 45 chars para caber no ecrã
        print(df[["source", "title", "real_eur", "previsto_eur", "diferenca"]]
              .assign(title=df["title"].str[:45]).round(0).to_string(index=False))
        erro = df["diferenca"].abs().mean()  # MAE em €/ano
        # Mediana do rácio previsto/real: 100% = na média certo; 80% = subestima
        vies = (df["previsto_eur"] / df["real_eur"]).median()
        print(f"\n{len(df)} ofertas | erro médio: {erro:,.0f} €/ano | "
              f"o modelo prevê {vies:.0%} do valor real\n")


if __name__ == "__main__":
    main()
