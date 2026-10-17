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


UMBRAL_PROFESIONAL = 5  # convención propia: anfitrión con 5 o más anuncios
MIN_PRECIOS = 30


def p2(df):
    """Mercado profesional (5 o más anuncios del anfitrión) frente a particular."""
    df = df.assign(
        perfil=df["anuncios_del_anfitrion"].ge(UMBRAL_PROFESIONAL).map(
            {True: "Profesional (5 o más)", False: "Particular (1-4)"}
        )
    )
    total = len(df)

    def resumen(g):
        con_precio = g["precio"].notna().sum()
        return pd.Series({
            "n_anuncios": len(g),
            "pct_anuncios": 100 * len(g) / total,
            "n_anfitriones": g["host_id"].nunique(),
            "n_con_precio": con_precio,
            "mediana_precio": g["precio"].median() if con_precio >= MIN_PRECIOS else float("nan"),
        })

    por_perfil = df.groupby("perfil").apply(resumen, include_groups=False).round(2)
    por_perfil.to_csv(RAIZ / "resultados" / "p2_perfil.csv", encoding="utf-8")

    por_tamano = df.groupby("tamano_anfitrion").apply(resumen, include_groups=False).round(2)
    por_tamano = por_tamano.reindex(["1 anuncio", "2-4", "5-19", "20 o más"])
    por_tamano.to_csv(RAIZ / "resultados" / "p2_tamano_anfitrion.csv", encoding="utf-8")

    por_distrito = (
        df.groupby("distrito")
        .agg(n_anuncios=("id", "size"),
             n_profesional=("perfil", lambda s: (s == "Profesional (5 o más)").sum()))
    )
    por_distrito["pct_profesional"] = 100 * por_distrito["n_profesional"] / por_distrito["n_anuncios"]
    por_distrito = por_distrito.sort_values("n_anuncios", ascending=False).round(2)
    por_distrito.to_csv(RAIZ / "resultados" / "p2_distritos.csv", encoding="utf-8")

    print("\nP2 perfil:\n", por_perfil[["n_anuncios", "pct_anuncios", "n_anfitriones"]])


def p3(df):
    """Licencia: distribución total y por distrito (categorías tal como vienen en los datos)."""
    total = (
        df["licencia"].value_counts().rename("n_anuncios").to_frame()
        .assign(pct=lambda t: 100 * t["n_anuncios"] / len(df)).round(2)
    )
    total.index.name = "licencia"
    total.to_csv(RAIZ / "resultados" / "p3_licencia_total.csv", encoding="utf-8")

    n = pd.crosstab(df["distrito"], df["licencia"])
    pct = (100 * n.div(n.sum(axis=1), axis=0)).round(2).add_prefix("pct_")
    tabla = n.add_prefix("n_").join(pct)
    tabla.insert(0, "n_anuncios", n.sum(axis=1))
    tabla.sort_values("n_anuncios", ascending=False).to_csv(
        RAIZ / "resultados" / "p3_licencia_distritos.csv", encoding="utf-8")

    print("\nP3 licencia total:\n", total)


def main():
    df = pd.read_csv(RAIZ / "datos" / "limpios" / "anuncios.csv")
    p1(df)
    p2(df)
    p3(df)


if __name__ == "__main__":
    main()
