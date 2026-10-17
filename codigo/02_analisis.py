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


def p4(df):
    """Exporta la actividad reciente total, sus componentes y los distritos."""
    resultados = RAIZ / "resultados"
    resultados.mkdir(parents=True, exist_ok=True)
    sin_resenas = ~df["activo_12m"]
    estancia_larga = df["estancia_larga"]
    sin_actividad = sin_resenas | estancia_larga
    etiqueta_sin = (
        "Sin actividad reciente (sin resenas en 12 meses o con estancia minima "
        "de 32 noches o mas)"
    )

    total = pd.DataFrame({
        "etiqueta": [etiqueta_sin, "Con actividad reciente"],
        "n_anuncios": [sin_actividad.sum(), (~sin_actividad).sum()],
    })
    total["pct"] = 100 * total["n_anuncios"] / len(df)
    total.round(2).to_csv(
        resultados / "p4_actividad_total.csv", index=False, encoding="utf-8"
    )

    componentes = pd.DataFrame([{
        "n_activo_12m_false": sin_resenas.sum(),
        "n_estancia_larga_true": estancia_larga.sum(),
        "n_ambos": (sin_resenas & estancia_larga).sum(),
        "n_sin_actividad": sin_actividad.sum(),
    }])
    componentes.round(2).to_csv(
        resultados / "p4_actividad_componentes.csv", index=False, encoding="utf-8"
    )

    distritos = df.assign(sin_actividad=sin_actividad).groupby(
        "distrito", dropna=False
    ).agg(
        n_anuncios=("sin_actividad", "size"),
        n_sin_actividad=("sin_actividad", "sum"),
    ).reset_index()
    distritos["pct_sin_actividad"] = (
        100 * distritos["n_sin_actividad"] / distritos["n_anuncios"]
    )
    distritos.sort_values("n_anuncios", ascending=False, kind="stable").round(2).to_csv(
        resultados / "p4_actividad_distritos.csv", index=False, encoding="utf-8"
    )


def p5(df):
    """Exporta precios y puntuaciones por tipo y su relación sin precios extremos."""
    resultados = RAIZ / "resultados"
    resultados.mkdir(parents=True, exist_ok=True)
    tipos = df.groupby("tipo", dropna=False).agg(
        n_anuncios=("precio", "size"),
        n_con_precio=("precio", "count"),
        mediana_precio=("precio", "median"),
        n_con_puntuacion=("puntuacion", "count"),
        mediana_puntuacion=("puntuacion", "median"),
    ).reset_index()
    for variable in ("precio", "puntuacion"):
        tipos.loc[
            tipos[f"n_con_{variable}"] < MIN_PRECIOS, f"mediana_{variable}"
        ] = float("nan")
    tipos.round(2).to_csv(resultados / "p5_tipo.csv", index=False, encoding="utf-8")

    validos = df.loc[
        df["precio"].notna() & df["puntuacion"].notna() & ~df["precio_extremo"]
    ].copy()

    def correlacion(grupo):
        # Spearman no está definida con menos de dos pares o valores constantes.
        if (len(grupo) < 2 or grupo["precio"].nunique() < 2
                or grupo["puntuacion"].nunique() < 2):
            return float("nan")
        return grupo["precio"].corr(grupo["puntuacion"], method="spearman")

    correlaciones = [{
        "tipo": "Total", "n": len(validos), "correlacion_spearman": correlacion(validos)
    }]
    for tipo, grupo in validos.groupby("tipo", dropna=False):
        if len(grupo) >= MIN_PRECIOS:
            correlaciones.append({
                "tipo": tipo, "n": len(grupo),
                "correlacion_spearman": correlacion(grupo),
            })
    pd.DataFrame(correlaciones).round(2).to_csv(
        resultados / "p5_correlacion.csv", index=False, encoding="utf-8"
    )

    tramos = ["<4.5", "4.5-4.8", ">4.8"]
    validos["tramo_puntuacion"] = "4.5-4.8"
    validos.loc[validos["puntuacion"] < 4.5, "tramo_puntuacion"] = "<4.5"
    validos.loc[validos["puntuacion"] > 4.8, "tramo_puntuacion"] = ">4.8"
    por_tramo = validos.groupby("tramo_puntuacion").agg(
        n=("precio", "size"), mediana_precio=("precio", "median")
    ).reindex(tramos)
    por_tramo["n"] = por_tramo["n"].fillna(0).astype(int)
    por_tramo.round(2).to_csv(
        resultados / "p5_precio_por_tramo_puntuacion.csv", encoding="utf-8"
    )


def main():
    df = pd.read_csv(RAIZ / "datos" / "limpios" / "anuncios.csv")
    p1(df)
    p2(df)
    p3(df)
    p4(df)
    p5(df)


if __name__ == "__main__":
    main()
