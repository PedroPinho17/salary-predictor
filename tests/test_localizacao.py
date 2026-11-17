import numpy as np
import pytest

from salary_predictor.features import EUA, EUROPA, make_row, to_frame
from salary_predictor.localizacao import PORTUGAL, REGIAO_EUROPA, pais, prever_usd


@pytest.mark.parametrize("location, esperado", [
    # Sem localização ou não reconhecida → Portugal
    (None, PORTUGAL),
    ("", PORTUGAL),
    ("Remoto", PORTUGAL),            # sites portugueses: remoto em Portugal
    ("Híbrido", PORTUGAL),
    # Portugal
    ("Lisboa", PORTUGAL),
    ("Porto, Portugal", PORTUGAL),
    ("Setúbal", PORTUGAL),
    ("Remoto (Portugal)", PORTUGAL),
    # EUA
    ("Remoto (USA)", EUA),
    ("United States", EUA),
    ("New York, NY", EUA),
    ("US only", EUA),
    # Outros países europeus, em inglês e português
    ("Berlin, Germany", "Germany"),
    ("Alemanha", "Germany"),
    ("Málaga", "Spain"),
    ("London", "United Kingdom of Great Britain and Northern Ireland"),
    ("Remote (UK)", "United Kingdom of Great Britain and Northern Ireland"),
    ("Zürich", "Switzerland"),
    # Remoto sem país → média europeia
    ("Remoto (Anywhere)", REGIAO_EUROPA),
    ("Remoto (Europe)", REGIAO_EUROPA),
    ("Remoto (EMEA)", REGIAO_EUROPA),
    ("Worldwide", REGIAO_EUROPA),
    # Um país claro ganha à região; vários países → média europeia
    ("Europe, Portugal", PORTUGAL),
    ("Spain or Portugal", REGIAO_EUROPA),
    # Palavras parecidas não contam
    ("Business park", PORTUGAL),     # "us" dentro de "business"
    ("Austin", EUA),                 # cidade americana, não "Austria"
])
def test_pais(location, esperado):
    assert pais(location) == esperado


def test_prever_usd_europa_e_mediana_dos_paises(fake_model):
    linhas = [make_row(p, 5, "Developer, back-end", ["Python"]) for p in EUROPA]
    esperado = float(np.median(fake_model.predict(to_frame(linhas))))
    assert prever_usd(fake_model, REGIAO_EUROPA, 5, "Developer, back-end", ["Python"]) == pytest.approx(esperado)
