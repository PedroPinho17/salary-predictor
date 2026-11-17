"""Definição das features: partilhada entre treino, CLI, API e comparação com o Radar."""

from pathlib import Path

import pandas as pd

# Raiz do projeto (sobe 2 pastas a partir deste ficheiro)
ROOT = Path(__file__).resolve().parents[2]
# Dataset do survey: usa o CSV descomprimido se existir, senão o .gz que vem no repositório
DATA = ROOT / "data" / "results.csv"
if not DATA.exists():
    DATA = ROOT / "data" / "results.csv.gz"
MODEL = ROOT / "models" / "salary_model.joblib"  # modelo treinado

# Países europeus usados no treino (e na "média europeia" das ofertas remotas)
EUROPA = ["Portugal", "Spain", "France", "Germany", "Italy", "Netherlands", "Belgium",
          "Ireland", "Poland", "United Kingdom of Great Britain and Northern Ireland",
          "Sweden", "Switzerland", "Austria", "Denmark", "Norway", "Finland",
          "Czech Republic", "Romania", "Greece"]
# EUA: para as ofertas remotas americanas não serem estimadas com salários europeus
EUA = "United States of America"
# Todos os países do treino
PAISES = [*EUROPA, EUA]
# Linguagens → cada uma vira uma coluna 0/1
LANGS = ["Python", "JavaScript", "TypeScript", "Java", "C#", "SQL", "Go", "Rust", "PHP"]
# Colunas de texto que o OneHotEncoder trata
CATS = ["Country", "EdLevel", "RemoteWork", "DevType"]
# Ordem exacta das colunas que o modelo espera (tem de bater com o treino)
FEATURES = ["Country", "WorkExp", "EdLevel", "RemoteWork", "DevType", *LANGS]

DESCONHECIDO = "Desconhecido"  # valor usado quando EdLevel/RemoteWork não são indicados
DEFAULT_DEV_TYPE = "Developer, full-stack"  # tipo de dev por omissão na CLI/API
DEFAULT_LANGS = ["JavaScript", "TypeScript", "Python", "Java", "SQL"]  # stack por omissão


def make_row(
    country: str,
    years: float,
    dev_type: str = DEFAULT_DEV_TYPE,
    langs: list[str] | None = None,
    ed_level: str = DESCONHECIDO,
    remote_work: str = DESCONHECIDO,
) -> dict:
    """Uma linha de features no formato que o modelo espera."""
    # Se não passares langs, usa a stack por omissão
    langs = DEFAULT_LANGS if langs is None else langs
    return {
        "Country": country,
        "WorkExp": years,  # anos de experiência
        "EdLevel": ed_level,
        "RemoteWork": remote_work,
        "DevType": dev_type,
        # Expande: Python=1, JavaScript=0, ... conforme a lista langs
        **{lang: int(lang in langs) for lang in LANGS},
    }


def to_frame(rows: list[dict]) -> pd.DataFrame:
    """Lista de dicts → DataFrame com as colunas na ordem FEATURES (o que o modelo pede)."""
    return pd.DataFrame(rows, columns=FEATURES)
