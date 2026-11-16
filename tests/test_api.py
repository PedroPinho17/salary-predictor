def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_predict_portugal(client):
    r = client.post("/predict", json={"years": 2})
    assert r.status_code == 200
    anual = r.json()["salario_anual_usd"]
    assert 10_000 < anual < 100_000


def test_mais_experiencia_ganha_mais(client):
    junior = client.post("/predict", json={"years": 1}).json()["salario_anual_usd"]
    senior = client.post("/predict", json={"years": 10}).json()["salario_anual_usd"]
    assert senior > junior


def test_anos_negativos_da_erro(client):
    r = client.post("/predict", json={"years": -1})
    assert r.status_code == 422


def test_pais_desconhecido_da_erro(client):
    r = client.post("/predict", json={"years": 2, "country": "portugal"})
    assert r.status_code == 422
    assert "Country" in r.json()["detail"][0]


def test_dev_type_desconhecido_da_erro(client):
    r = client.post("/predict", json={"years": 2, "dev_type": "Backend"})
    assert r.status_code == 422


def test_linguagem_desconhecida_da_erro(client):
    r = client.post("/predict", json={"years": 2, "langs": ["Cobol"]})
    assert r.status_code == 422


def test_options_lista_valores_aceites(client):
    r = client.get("/options")
    assert r.status_code == 200
    assert "Portugal" in r.json()["Country"]
    assert "Python" in r.json()["langs"]
