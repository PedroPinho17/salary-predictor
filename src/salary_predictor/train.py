import argparse

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from salary_predictor.features import (
    CATS, DATA, DESCONHECIDO, EUROPA, FEATURES, LANGS, MODEL, PAISES,
)

MODELOS = ("rf", "gb")


def load() -> tuple[pd.DataFrame, pd.Series]:
    """Carrega o survey, limpa e devolve (X, y)."""
    df = pd.read_csv(DATA, low_memory=False)
    df = df.dropna(subset=["ConvertedCompYearly", "Country", "WorkExp"])
    # Corta outliers: salários abaixo de 5k ou acima de 400k USD são quase sempre erros de resposta
    df = df[df["ConvertedCompYearly"].between(5_000, 400_000)]
    df = df[df["Country"].isin(PAISES)]  # Europa + EUA

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


class MedianaPorPais(RegressorMixin, BaseEstimator):
    """Base de comparação: prevê a mediana do salário no país da pessoa.

    Mais exigente que a mediana global (que, com os EUA no treino, subiria muito e faria
    qualquer modelo parecer bom na Europa). Países sem dados usam a mediana global.
    """

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.medianas_ = pd.Series(np.asarray(y), index=X.index).groupby(X["Country"]).median()
        self.global_ = float(np.median(y))
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return X["Country"].map(self.medianas_).fillna(self.global_).to_numpy(dtype=float)


def cv_mae(model, X: pd.DataFrame, y: pd.Series, folds: int = 5) -> dict[str, tuple[float, float]]:
    """MAE médio e desvio padrão em validação cruzada: no total, só na Europa e só nos EUA.

    Separado por região porque os salários dos EUA são muito mais altos: um erro médio
    global misturaria as duas escalas e esconderia como o modelo se porta na Europa.
    """
    cv = KFold(n_splits=folds, shuffle=True, random_state=42)
    europa = X["Country"].isin(EUROPA).to_numpy()
    erros = {"total": [], "Europa": [], "EUA": []}
    for tr, te in cv.split(X):
        m = clone(model).fit(X.iloc[tr], y.iloc[tr])
        erro = np.abs(m.predict(X.iloc[te]) - y.iloc[te].to_numpy())
        erros["total"].append(erro.mean())
        erros["Europa"].append(erro[europa[te]].mean())
        erros["EUA"].append(erro[~europa[te]].mean())
    return {k: (float(np.mean(v)), float(np.std(v))) for k, v in erros.items()}


def main() -> None:
    p = argparse.ArgumentParser(description="Treina e guarda o modelo de salários")
    p.add_argument("--model", choices=MODELOS, default="rf", help="modelo a guardar")
    p.add_argument("--compare", action="store_true", help="avalia todos os modelos com validação cruzada")
    a = p.parse_args()

    X, y = load()
    n_europa = int(X["Country"].isin(EUROPA).sum())
    print(f"{len(X)} respostas ({n_europa} Europa, {len(X) - n_europa} EUA)")

    candidatos = {"base": MedianaPorPais()}
    candidatos |= {k: build(k) for k in (MODELOS if a.compare else (a.model,))}
    print("MAE em $/ano, validação cruzada 5-fold (média ± desvio)")
    for nome, m in candidatos.items():
        res = cv_mae(m, X, y)
        print(f"{nome:>4}: " + " | ".join(f"{k} {media:,.0f} ± {desvio:,.0f}"
                                          for k, (media, desvio) in res.items()))

    model = build(a.model).fit(X, y)
    MODEL.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL)
    print(f"Modelo '{a.model}' treinado com todos os dados e guardado em {MODEL}")


if __name__ == "__main__":
    main()
