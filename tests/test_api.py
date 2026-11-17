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


def test_curve_devolve_um_valor_por_ano(client):
    r = client.post("/curve", json={"years": 5})
    assert r.status_code == 200
    curva = r.json()
    assert curva["anos"] == list(range(31))
    assert len(curva["salario_anual_usd"]) == 31
    # No modelo sintético o salário sobe com a experiência
    assert curva["salario_anual_usd"][-1] > curva["salario_anual_usd"][0]


def test_curve_bate_certo_com_predict(client):
    curva = client.post("/curve", json={"years": 7, "country": "Germany"}).json()
    previsao = client.post("/predict", json={"years": 7, "country": "Germany"}).json()
    assert curva["salario_anual_usd"][7] == previsao["salario_anual_usd"]


def test_curve_valida_o_perfil(client):
    r = client.post("/curve", json={"years": 2, "country": "portugal"})
    assert r.status_code == 422


def test_meta(client):
    r = client.get("/meta")
    assert r.status_code == 200
    assert 0 < r.json()["usd_para_eur"] < 2
    assert 0 < r.json()["mae_usd_europa"] < r.json()["mae_usd_eua"]


def test_pagina_inicial(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "/static/app.js" in r.text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200


def test_estimate_sem_localizacao_usa_portugal(client):
    r = client.post("/estimate", json={"title": "Backend Developer", "years": 3})
    assert r.status_code == 200
    assert r.json()["base"] == "Portugal"
    assert r.json()["salario_anual_eur"] > 0


def test_estimate_oferta_americana_paga_mais(client):
    oferta = {"title": "Backend Developer", "years": 3}
    pt = client.post("/estimate", json={**oferta, "location": "Lisboa"}).json()
    us = client.post("/estimate", json={**oferta, "location": "Remoto (USA)"}).json()
    assert us["base"] == "United States of America"
    assert us["salario_anual_eur"] > pt["salario_anual_eur"]


def test_estimate_remoto_sem_pais_usa_media_europeia(client):
    r = client.post("/estimate", json={"title": "Backend Developer", "location": "Remoto (Anywhere)"})
    assert r.status_code == 200
    assert r.json()["base"] == "Europe"


def test_estimate_sem_localizacao_igual_ao_antigo(client):
    """Quem não envia location (versão antiga do Radar) continua a receber a estimativa portuguesa."""
    sem = client.post("/estimate", json={"title": "Java Developer"}).json()
    com = client.post("/estimate", json={"title": "Java Developer", "location": "Portugal"}).json()
    assert sem == com
