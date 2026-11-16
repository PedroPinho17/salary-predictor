import pytest

from salary_predictor.compare_radar import anos, funcao, linguagens
from salary_predictor.train import build


@pytest.mark.parametrize("texto, esperado", [
    ("Experience with JavaScript and React", ["JavaScript"]),
    ("Java 17, Spring Boot", ["Java"]),
    ("We work at Google with Go and gRPC", ["Go"]),
    ("Good communication skills, go-getter attitude", []),
    ("Trust and ownership", []),
    ("PostgreSQL, MySQL", ["SQL"]),
    ("MongoDB and other NoSQL stores", []),
    ("C# / .NET Core", ["C#"]),
    ("Python, TypeScript and Rust", ["Python", "TypeScript", "Rust"]),
    (None, []),
    ("", []),
])
def test_linguagens(texto, esperado):
    assert linguagens(texto) == esperado


@pytest.mark.parametrize("titulo, esperado", [
    ("Senior Backend Engineer", "Developer, back-end"),
    ("Front-End Developer", "Developer, front-end"),
    ("AI Engineer", "AI/ML engineer"),
    ("Email Marketing Developer", "Developer, full-stack"),  # "ai" dentro de "email" não conta
    ("QA Automation", "Developer, QA or test"),
    ("Latest Tech Developer", "Developer, full-stack"),  # "test" dentro de "latest" não conta
])
def test_funcao(titulo, esperado):
    assert funcao(titulo) == esperado


@pytest.mark.parametrize("titulo, esperado", [
    ("Júnior Developer", 1),
    ("Senior Java Developer", 7),
    ("Tech Lead", 7),
    ("Team Leadership Coach", 3),
    ("Java Developer", 3),
])
def test_anos(titulo, esperado):
    assert anos(titulo) == esperado


def test_build_modelo_desconhecido():
    with pytest.raises(ValueError):
        build("xgboost")
