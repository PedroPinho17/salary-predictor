# argparse: lê argumentos da linha de comandos (--country, --years, ...)
import argparse

import joblib  # carrega o modelo .joblib do disco

# Helpers partilhados: defaults, caminho do modelo, montar a linha e o DataFrame
from salary_predictor.features import DEFAULT_DEV_TYPE, DEFAULT_LANGS, MODEL, make_row, to_frame


def predict(country: str, years: float, dev_type: str = DEFAULT_DEV_TYPE,
            langs: list[str] | None = None, model=None) -> float:
    """Prevê o salário anual (USD) para um perfil.

    Se já tiveres o modelo em memória (ex.: na API), passa-o em `model`
    para não o carregar outra vez do disco.
    """
    # Carrega do disco só se não receberes um modelo já pronto
    model = model if model is not None else joblib.load(MODEL)
    # make_row → dict | to_frame → DataFrame 1 linha | predict → array | [0] → float
    return float(model.predict(to_frame([make_row(country, years, dev_type, langs)]))[0])


def main() -> None:
    """CLI: python -m salary_predictor.predict --years 5 --country Portugal"""
    p = argparse.ArgumentParser(description="Prevê o salário anual (USD)")
    p.add_argument("--country", default="Portugal")  # país (default Portugal)
    p.add_argument("--years", type=float, required=True)  # anos de experiência (obrigatório)
    p.add_argument("--dev-type", default=DEFAULT_DEV_TYPE)  # tipo de developer
    # Linguagens em texto separado por vírgulas → depois fazemos .split(",")
    p.add_argument("--langs", default=",".join(DEFAULT_LANGS))
    a = p.parse_args()  # lê os args que o utilizador passou
    valor = predict(a.country, a.years, a.dev_type, a.langs.split(","))
    # :g remove zeros desnecessários (5.0 → 5); :,.0f formata com milhares e sem casas
    print(f"{a.country}, {a.years:g} anos: {valor:,.0f} $/ano")


# Só corre main() se executares este ficheiro directamente (não ao importar)
if __name__ == "__main__":
    main()
