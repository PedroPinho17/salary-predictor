"""Localização de uma oferta (texto livre) → país do modelo, ou a região "Europa".

O Radar guarda a localização tal como vem de cada site: "Lisboa", "Porto, Portugal",
"Remoto (USA)", "Remoto (Anywhere)", "Berlin, Germany", ... Aqui decide-se que salário usar:

- um país conhecido → esse país;
- "Anywhere", "Worldwide", "Europe", "EMEA" (remoto sem país) → média europeia;
- vazio ou não reconhecido → Portugal (o Radar procura sobretudo ofertas portuguesas).
"""

import re
import unicodedata

import numpy as np

from salary_predictor.features import EUA, EUROPA, make_row, to_frame

PORTUGAL = "Portugal"
# Valor especial: remoto sem país definido → mediana das estimativas dos países europeus
REGIAO_EUROPA = "Europe"

# Nomes e cidades (sem acentos, minúsculas) → país do survey. Regex com fronteiras de palavra.
_PAISES = {
    "Portugal": r"portugal|lisboa|lisbon|porto|braga|coimbra|aveiro|faro|setubal|leiria|viseu|madeira|acores|azores",
    EUA: r"usa|u\.s\.a?\.?|us|united states|estados unidos|eua|new york|san francisco|seattle|boston|austin|chicago|los angeles",
    "Spain": r"spain|espanha|espana|madrid|barcelona|valencia|sevilla|seville|malaga",
    "France": r"france|franca|paris|lyon|toulouse|marseille|lille|nantes",
    "Germany": r"germany|alemanha|deutschland|berlin|berlim|munich|munchen|munique|hamburg|frankfurt|cologne|koln|stuttgart",
    "Italy": r"italy|italia|milan|milano|milao|rome|roma|turin|torino",
    "Netherlands": r"netherlands|holland|holanda|paises baixos|amsterdam|amesterdao|rotterdam|utrecht|eindhoven|the hague",
    "Belgium": r"belgium|belgica|brussels|bruxelas|antwerp|ghent",
    "Ireland": r"ireland|irlanda|dublin|cork",
    "Poland": r"poland|polonia|warsaw|varsovia|krakow|cracovia|wroclaw|gdansk",
    "United Kingdom of Great Britain and Northern Ireland":
        r"uk|u\.k\.|united kingdom|reino unido|england|inglaterra|scotland|great britain|london|londres|manchester|edinburgh|bristol|cambridge|oxford",
    "Sweden": r"sweden|suecia|stockholm|estocolmo|gothenburg|malmo",
    "Switzerland": r"switzerland|suica|schweiz|zurich|geneva|genebra|basel|lausanne|bern",
    "Austria": r"austria|vienna|viena|wien|graz|linz",
    "Denmark": r"denmark|dinamarca|copenhagen|copenhaga|aarhus",
    "Norway": r"norway|noruega|oslo|bergen",
    "Finland": r"finland|finlandia|helsinki|espoo|tampere",
    "Czech Republic": r"czech|chequia|republica checa|czechia|prague|praga|brno",
    "Romania": r"romania|bucharest|bucareste|cluj|iasi|timisoara",
    "Greece": r"greece|grecia|athens|atenas|thessaloniki",
}
_PADROES = {pais: re.compile(rf"\b(?:{p})\b") for pais, p in _PAISES.items()}
# Remoto sem país: qualquer sítio, ou só "Europa"
_REGIAO = re.compile(r"\b(?:anywhere|worldwide|global|europe|europa|emea|eu|european union|uniao europeia)\b")


def _normalizar(texto: str) -> str:
    """Minúsculas e sem acentos ("Málaga" → "malaga")."""
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acentos.lower()


def pais(location: str | None) -> str:
    """País do survey para esta localização, ou REGIAO_EUROPA, ou Portugal por omissão."""
    if not location or not location.strip():
        return PORTUGAL
    texto = _normalizar(location)
    encontrados = [p for p, padrao in _PADROES.items() if padrao.search(texto)]
    if len(encontrados) == 1:
        return encontrados[0]  # um país claro ganha a qualquer região ("Europe, Portugal" → Portugal)
    if len(encontrados) > 1 or _REGIAO.search(texto):
        return REGIAO_EUROPA  # vários países ("Spain or Portugal") ou remoto sem país
    return PORTUGAL


def prever_usd(model, base: str, years: float, dev_type: str, langs: list[str]) -> float:
    """Salário anual previsto (USD) para um país, ou a mediana europeia se base == REGIAO_EUROPA."""
    paises = EUROPA if base == REGIAO_EUROPA else [base]
    previsoes = model.predict(to_frame([make_row(p, years, dev_type, langs) for p in paises]))
    return float(np.median(previsoes))
