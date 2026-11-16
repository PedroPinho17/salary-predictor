"""Modelo pequeno treinado com dados sintéticos, para os testes não precisarem do survey."""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from salary_predictor.api import app, get_model
from salary_predictor.features import DESCONHECIDO, LANGS, make_row, to_frame
from salary_predictor.train import build

PAISES = {"Portugal": 1.0, "Germany": 2.0}
DEV_TYPES = ["Developer, full-stack", "Developer, back-end"]


@pytest.fixture(scope="session")
def fake_model():
    rng = np.random.default_rng(0)
    n = 600
    paises = rng.choice(list(PAISES), n)
    anos = rng.uniform(0, 30, n)
    rows = [
        make_row(
            country=pais,
            years=a,
            dev_type=rng.choice(DEV_TYPES),
            langs=list(rng.choice(LANGS, 3, replace=False)),
            ed_level=rng.choice([DESCONHECIDO, "Master's degree"]),
            remote_work=rng.choice([DESCONHECIDO, "Remote"]),
        )
        for pais, a in zip(paises, anos)
    ]
    y = 20_000 * np.array([PAISES[p] for p in paises]) * (1 + 0.08 * anos) * rng.uniform(0.9, 1.1, n)
    return build("rf").fit(to_frame(rows), y)


@pytest.fixture
def client(fake_model):
    app.dependency_overrides[get_model] = lambda: fake_model
    yield TestClient(app)
    app.dependency_overrides.clear()
