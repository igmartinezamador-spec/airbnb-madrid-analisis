"""Análisis de los anuncios limpios de Madrid por distrito y barrio."""

from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]


def p1(df):
    """Exporta la distribución de anuncios y la mediana del precio por zona."""
    resultados = RAIZ / "resultados"
    resultados.mkdir(parents=True, exist_ok=True)

    for zonas, nombre in (
        (["distrito"], "p1_distritos.csv"),
        (["distrito", "barrio"], "p1_barrios.csv"),
    ):
        # Se incluyen todos los anuncios y precios extremos; count y median
        # omiten únicamente los precios nulos. dropna=False conserva las zonas nulas.
        resumen = df.groupby(zonas, dropna=False).agg(
            n_anuncios=("precio", "size"),
            n_con_precio=("precio", "count"),
            mediana_precio=("precio", "median"),
        ).reset_index()
        resumen["pct_total"] = resumen["n_anuncios"] / len(df) * 100
        resumen.loc[resumen["n_con_precio"] < 30, "mediana_precio"] = float("nan")
        resumen = resumen[
            zonas + ["n_anuncios", "pct_total", "n_con_precio", "mediana_precio"]
        ].sort_values("n_anuncios", ascending=False, kind="stable").round(2)
        resumen.to_csv(resultados / nombre, index=False, encoding="utf-8")

        if nombre == "p1_distritos.csv":
            print("P1 — Top 5 de distritos por número de anuncios:")
            print(resumen.head(5).to_string(index=False))


def main():
    df = pd.read_csv(RAIZ / "datos" / "limpios" / "anuncios.csv")
    p1(df)


if __name__ == "__main__":
    main()
