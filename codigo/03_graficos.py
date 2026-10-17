"""Genera siete gráficos descriptivos a partir de los resultados del análisis."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "graficos"
BASE = "#647889"
ENFASIS = "#B65D3B"
TEXTO = "#26333D"
EJE_PRECIO = "Mediana del precio publicado ($, moneda no verificada)"
TOP = 10


def numero(valor, decimales=0):
    """Formato español para las etiquetas de los datos."""
    return f"{valor:,.{decimales}f}".translate(str.maketrans({",": ".", ".": ","}))


def configurar():
    plt.rcParams.update({
        "figure.figsize": (9, 5.5),
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "text.color": TEXTO,
        "axes.labelcolor": TEXTO,
        "xtick.color": TEXTO,
        "ytick.color": TEXTO,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.edgecolor": "#D5DADF",
        "axes.grid": False,
        "legend.frameon": False,
    })


def top_distritos(df):
    return df.sort_values("n_anuncios", ascending=False, kind="stable").head(TOP).copy()


def lienzo(titulo, subtitulo=None, inferior=0.18):
    fig, ax = plt.subplots()
    titulo_largo = "\n" in titulo and subtitulo is not None
    fig.subplots_adjust(left=0.23, right=0.95, bottom=inferior,
                        top=0.75 if titulo_largo else 0.79)
    fig.text(0.04, 0.95, titulo, fontsize=15, weight="bold", va="top")
    if subtitulo:
        fig.text(0.04, 0.81 if titulo_largo else 0.85, subtitulo, fontsize=10, color=BASE)
    return fig, ax


def barras(ax, nombres, valores, destacado, decimales=0, porcentaje=False):
    colores = [ENFASIS if i == destacado else BASE for i in range(len(valores))]
    posiciones = range(len(nombres))
    rectangulos = ax.barh(posiciones, valores.fillna(0), color=colores, height=0.65)
    ax.set_yticks(list(posiciones), nombres)
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0, pad=8)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: numero(x)))
    maximo = valores.max()
    ax.set_xlim(0, 100 if porcentaje else maximo * 1.22)
    etiquetas = [
        "Sin mediana publicada" if pd.isna(v)
        else f"{numero(v, decimales)}{' %' if porcentaje else ''}"
        for v in valores
    ]
    ax.bar_label(rectangulos, labels=etiquetas, padding=5, fontsize=9)
    return rectangulos


def guardar(fig, nombre):
    ruta = SALIDA / nombre
    fig.savefig(ruta, dpi=150, facecolor="white")
    plt.close(fig)
    print(f"Generado: {ruta.relative_to(RAIZ)}")
    return ruta


def g1(df):
    datos = top_distritos(df).reset_index(drop=True)
    lider = datos.iloc[0]
    cuota = 100 * lider["n_anuncios"] / df["n_anuncios"].sum()
    fig, ax = lienzo(
        f"{lider['distrito']} concentra el {numero(cuota, 1)} % de los anuncios",
        f"Los {len(datos)} distritos con más anuncios · ordenados por volumen",
    )
    barras(ax, datos["distrito"], datos["n_anuncios"], 0)
    ax.set_xlabel("Anuncios (n)")
    return guardar(fig, "g1_anuncios_por_distrito.png")


def g2(df):
    datos = top_distritos(df).sort_values("mediana_precio", ascending=False).reset_index(drop=True)
    lider = datos.iloc[0]
    fig, ax = lienzo(
        f"{lider['distrito']} tiene la mayor mediana de precio\n"
        f"entre los {len(datos)} distritos con más anuncios: {numero(lider['mediana_precio'], 2)} $",
    )
    barras(ax, datos["distrito"], datos["mediana_precio"], 0, decimales=2)
    ax.set_xlabel(EJE_PRECIO)
    fig.text(0.04, 0.04, "Excluye anuncios sin precio", fontsize=9)
    return guardar(fig, "g2_mediana_precio_distrito.png")


def g3(perfiles, distritos):
    perfiles = perfiles.reset_index(drop=True)
    indice = perfiles.index[perfiles["perfil"].str.startswith("Profesional")][0]
    profesional = perfiles.loc[indice]
    datos = top_distritos(distritos).reset_index(drop=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5.5), gridspec_kw={"width_ratios": [1, 1.5]})
    fig.subplots_adjust(left=0.19, right=0.97, top=0.77, bottom=0.18, wspace=0.95)
    fig.text(0.04, 0.95,
             f"El perfil profesional reúne el {numero(profesional['pct_anuncios'], 1)} %\n"
             "de los anuncios de Madrid", fontsize=15, weight="bold", va="top")
    nombres = perfiles["perfil"].str.replace(" (", "\n(", regex=False)
    barras(ax1, nombres, perfiles["pct_anuncios"], indice, decimales=1, porcentaje=True)
    barras(ax2, datos["distrito"], datos["pct_profesional"], datos["pct_profesional"].idxmax(),
           decimales=1, porcentaje=True)
    ax1.set_xlabel("% de anuncios por perfil")
    ax2.set_xlabel("% de anuncios de perfil profesional")
    fig.text(0.04, 0.04,
             f"Panel derecho: los {len(datos)} distritos con más anuncios. "
             "Énfasis en el mayor porcentaje.", fontsize=9)
    return guardar(fig, "g3_profesional_vs_particular.png")


def apiladas(ax, distritos, series, estilos):
    izquierda = pd.Series(0.0, index=series.index)
    for (etiqueta, valores), estilo in zip(series.items(), estilos):
        color, alfa, trama = estilo
        rectangulos = ax.barh(distritos, valores, left=izquierda, height=0.65,
                             label=etiqueta, color=color, alpha=alfa,
                             hatch=trama, edgecolor="white", linewidth=0.6)
        ax.bar_label(rectangulos, labels=[f"{numero(v, 1)} %" for v in valores],
                     label_type="center", fontsize=8,
                     color="white" if alfa == 1 else TEXTO)
        izquierda += valores
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("% de anuncios")
    ax.tick_params(axis="y", length=0, pad=8)


def g4(df):
    datos = top_distritos(df)
    categorias = [col.removeprefix("pct_") for col in df if col.startswith("pct_")]
    if len(categorias) != 4:
        raise ValueError("Se esperaban cuatro categorías de licencia en el CSV.")
    # Recalcular desde los recuentos evita que el redondeo supere el 100 %.
    porcentajes = pd.DataFrame({
        categoria: 100 * datos[f"n_{categoria}"] / datos["n_anuncios"]
        for categoria in categorias
    })
    cuota = 100 * datos["n_Sin dato"].sum() / datos["n_anuncios"].sum()
    fig, ax = lienzo(
        f"El {numero(cuota, 1)} % no tiene dato de licencia\n"
        f"en los {len(datos)} distritos con más anuncios", inferior=0.24,
    )
    estilos_base = iter([(BASE, 0.35, "//"), (BASE, 1, ""), (BASE, 0.65, "..")])
    estilos = [(ENFASIS, 1, "") if c == "Sin dato" else next(estilos_base) for c in categorias]
    apiladas(ax, datos["distrito"], porcentajes, estilos)
    fig.legend(*ax.get_legend_handles_labels(), loc="lower center", ncol=2,
               bbox_to_anchor=(0.5, 0.015), fontsize=9)
    return guardar(fig, "g4_licencia_distritos.png")


def g5(total, distritos):
    sin = total.loc[total["etiqueta"].str.startswith("Sin actividad reciente")].iloc[0]
    con = total.loc[total["etiqueta"].str.startswith("Con actividad reciente")].iloc[0]
    # Conservar el texto del CSV; sustituir solo un espacio por un salto de línea.
    etiqueta_sin = sin["etiqueta"].replace(" o con estancia", "\no con estancia", 1)
    datos = top_distritos(distritos)
    pct_sin = 100 * datos["n_sin_actividad"] / datos["n_anuncios"]
    porcentajes = pd.DataFrame({con["etiqueta"]: 100 - pct_sin, etiqueta_sin: pct_sin})
    fig, ax = lienzo(
        f"El {numero(sin['pct'], 1)} % de los anuncios de Madrid\n"
        "se clasifica sin actividad reciente",
        f"Los {len(datos)} distritos con más anuncios · porcentajes dentro de cada distrito",
        inferior=0.29,
    )
    apiladas(ax, datos["distrito"], porcentajes, [(BASE, 1, ""), (ENFASIS, 1, "")])
    fig.legend(*ax.get_legend_handles_labels(), loc="lower left",
               bbox_to_anchor=(0.035, 0.005), fontsize=9, labelspacing=0.8)
    return guardar(fig, "g5_actividad_reciente.png")


def g6(tipos, anuncios):
    datos = tipos.sort_values("mediana_precio", ascending=False, na_position="last").reset_index(drop=True)
    lider = datos.iloc[0]
    fig, ax = lienzo(
        f"{lider['tipo']} presenta la mayor mediana publicada:\n"
        f"{numero(lider['mediana_precio'], 2)} $ entre los tipos con dato",
    )
    barras(ax, datos["tipo"], datos["mediana_precio"], 0, decimales=2)
    ax.set_xlabel(EJE_PRECIO)
    sin_precio = anuncios["precio"].isna().sum()
    fig.text(0.04, 0.04,
             f"Medianas del CSV de resultados; excluyen {numero(sin_precio)} anuncios sin precio.",
             fontsize=9)
    return guardar(fig, "g6_precio_por_tipo.png")


def g7(df):
    # Mantener el orden de los tramos del CSV, sin ordenarlos por precio.
    datos = df.reset_index(drop=True)
    indice = datos["mediana_precio"].idxmax()
    lider = datos.loc[indice]
    fig, ax = lienzo(
        f"El tramo {lider['tramo_puntuacion']} tiene la mayor mediana:\n"
        f"{numero(lider['mediana_precio'], 2)} $", inferior=0.25,
    )
    barras(ax, datos["tramo_puntuacion"], datos["mediana_precio"], indice, decimales=2)
    ax.set_ylabel("Tramo de puntuación (puntos)")
    ax.set_xlabel(EJE_PRECIO)
    fig.text(0.04, 0.09, "Relacion descriptiva, no causal", fontsize=9)
    fig.text(0.04, 0.045,
             "Con precio y puntuación disponibles; sin precios extremos, según el análisis previo.",
             fontsize=9)
    return guardar(fig, "g7_precio_vs_puntuacion.png")


def main():
    configurar()
    SALIDA.mkdir(parents=True, exist_ok=True)
    nombres = (
        "p1_distritos", "p2_perfil", "p2_distritos", "p3_licencia_distritos",
        "p4_actividad_total", "p4_actividad_distritos", "p5_tipo",
        "p5_precio_por_tramo_puntuacion",
    )
    tablas = {nombre: pd.read_csv(RAIZ / "resultados" / f"{nombre}.csv") for nombre in nombres}
    anuncios = pd.read_csv(RAIZ / "datos" / "limpios" / "anuncios.csv")
    if tablas["p1_distritos"]["n_anuncios"].sum() != len(anuncios):
        raise ValueError("Los resultados y anuncios.csv no corresponden al mismo total de anuncios.")
    rutas = [
        g1(tablas["p1_distritos"]),
        g2(tablas["p1_distritos"]),
        g3(tablas["p2_perfil"], tablas["p2_distritos"]),
        g4(tablas["p3_licencia_distritos"]),
        g5(tablas["p4_actividad_total"], tablas["p4_actividad_distritos"]),
        g6(tablas["p5_tipo"], anuncios),
        g7(tablas["p5_precio_por_tramo_puntuacion"]),
    ]
    for ruta in rutas:
        if not ruta.is_file() or ruta.stat().st_size == 0:
            raise RuntimeError(f"No se ha generado correctamente: {ruta}")
    print(f"Comprobados {len(rutas)} PNG en {SALIDA}")


if __name__ == "__main__":
    main()
