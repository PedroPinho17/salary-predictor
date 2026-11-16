import argparse

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from salary_predictor.features import (
    CATS, DATA, DESCONHECIDO, EUROPA, FEATURES, LANGS, MODEL,
)

MODELOS = ("rf", "gb")


def load() -> tuple[pd.DataFrame, pd.Series]:
    """Carrega o survey, limpa e devolve (X, y)."""
    df = pd.read_csv(DATA, low_memory=False)
    df = df.dropna(subset=["ConvertedCompYearly", "Country", "WorkExp"])
    # Corta outliers: salários abaixo de 5k ou acima de 400k USD são quase sempre erros de resposta
    df = df[df["ConvertedCompYearly"].between(5_000, 400_000)]
    df = df[df["Country"].isin(EUROPA)]

    X = df[["Country", "WorkExp", "EdLevel", "RemoteWork", "DevType"]].copy()
    for col in ["EdLevel", "RemoteWork", "DevType"]:
        X[col] = X[col].fillna(DESCONHECIDO)
    langs = df["LanguageHaveWorkedWith"].fillna("").str.split(";")
    for lang in LANGS:
        X[lang] = langs.apply(lambda l: int(lang in l))
    return X[FEATURES], df["ConvertedCompYearly"]


def build(kind: str = "rf") -> TransformedTargetRegressor:
    """Pipeline OneHot → modelo, treinado sobre log(salário).

    O log porque os salários têm cauda longa à direita; min_frequency=20 agrupa
    categorias raras para não criar colunas com meia dúzia de exemplos.
    """
    if kind not in MODELOS:
        raise ValueError(f"modelo desconhecido: {kind!r} (opções: {MODELOS})")
    # O HistGradientBoosting não aceita matrizes esparsas
    encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=20, sparse_output=kind == "rf")
    prep = ColumnTransformer([("cat", encoder, CATS)], remainder="passthrough")
    if kind == "rf":
        reg = RandomForestRegressor(n_estimators=300, min_samples_leaf=5, random_state=42, n_jobs=-1)
    else:
        reg = HistGradientBoostingRegressor(max_iter=500, learning_rate=0.05, random_state=42)
    return TransformedTargetRegressor(
        regressor=Pipeline([("prep", prep), ("model", reg)]), func=np.log, inverse_func=np.exp
    )


def cv_mae(model, X: pd.DataFrame, y: pd.Series, folds: int = 5) -> tuple[float, float]:
    """MAE médio e desvio padrão em validação cruzada."""
    cv = KFold(n_splits=folds, shuffle=True, random_state=42)
    scores = -cross_val_score(model, X, y, cv=cv, scoring="neg_mean_absolute_error")
    return scores.mean(), scores.std()


def main() -> None:
    p = argparse.ArgumentParser(description="Treina e guarda o modelo de salários")
    p.add_argument("--model", choices=MODELOS, default="rf", help="modelo a guardar")
    p.add_argument("--compare", action="store_true", help="avalia todos os modelos com validação cruzada")
    a = p.parse_args()

    X, y = load()
    print(f"{len(X)} respostas")

    candidatos = {"base": DummyRegressor(strategy="median")}
    candidatos |= {k: build(k) for k in (MODELOS if a.compare else (a.model,))}
    for nome, m in candidatos.items():
        media, desvio = cv_mae(m, X, y)
        print(f"{nome:>4}: {media:,.0f} ± {desvio:,.0f} $/ano (MAE, 5-fold CV)")

    model = build(a.model).fit(X, y)
    MODEL.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL)
    print(f"Modelo '{a.model}' treinado com todos os dados e guardado em {MODEL}")


if __name__ == "__main__":
    main()
