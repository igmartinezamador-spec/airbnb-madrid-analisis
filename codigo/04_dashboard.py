"""Prepara los datos para un dashboard en Power BI Desktop (carpeta dashboard/datos/)."""

import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "dashboard" / "datos"
UMBRAL_PROFESIONAL = 5
MIN_N = 30
ETIQUETA_SIN = "Sin actividad reciente (sin reseñas en 12 meses o con estancia mínima de 32 noches o más)"
ETIQUETA_CON = "Con actividad reciente"


def guardar(df, nombre):
    """CSV en UTF-8 con BOM (Power BI Desktop en Windows detecta bien las tildes), coma y punto decimal."""
    df.to_csv(SALIDA / nombre, index=False, encoding="utf-8-sig", sep=",", decimal=".")
    print(f"Generado: dashboard/datos/{nombre} ({len(df)} filas)")


def tablas(df):
    # --- Tablas de apoyo (dimensiones) ---
    distritos = (
        df[["distrito"]].drop_duplicates().sort_values("distrito").reset_index(drop=True)
    )
    distritos.insert(0, "distrito_id", range(1, len(distritos) + 1))

    barrios = (
        df.groupby(["barrio", "distrito"])
        .agg(n_anuncios=("id", "size"), n_con_precio=("precio", "count"),
             latitud_centro=("latitud", "mean"), longitud_centro=("longitud", "mean"))
        .reset_index()
        .merge(distritos, on="distrito")
        .sort_values(["distrito_id", "barrio"])
        .reset_index(drop=True)
    )
    barrios.insert(0, "barrio_id", range(1, len(barrios) + 1))
    barrios["muestra_anuncios"] = barrios["n_anuncios"].map(
        lambda n: "n suficiente" if n >= MIN_N else "n insuficiente")
    barrios["muestra_precio"] = barrios["n_con_precio"].map(
        lambda n: "n suficiente" if n >= MIN_N else "n insuficiente")
    barrios[["latitud_centro", "longitud_centro"]] = barrios[["latitud_centro", "longitud_centro"]].round(6)
    barrios = barrios[["barrio_id", "barrio", "distrito_id", "n_anuncios", "n_con_precio",
                       "muestra_anuncios", "muestra_precio", "latitud_centro", "longitud_centro"]]

    tipos = df[["tipo"]].drop_duplicates().sort_values("tipo").reset_index(drop=True)
    tipos.insert(0, "tipo_id", range(1, len(tipos) + 1))

    orden = ["1 anuncio", "2-4", "5-19", "20 o más"]
    tamanos = pd.DataFrame({"tamano_anfitrion": orden})
    tamanos.insert(0, "tamano_id", range(1, len(orden) + 1))
    tamanos["perfil_anfitrion"] = ["Particular (1-4)", "Particular (1-4)",
                                   "Profesional (5 o más)", "Profesional (5 o más)"]

    # --- Tabla principal (hechos): sin host_id ni ningún dato del anfitrión ---
    sin_actividad = (~df["activo_12m"]) | df["estancia_larga"]
    es_prof = df["anuncios_del_anfitrion"] >= UMBRAL_PROFESIONAL
    anuncios = (
        df.merge(barrios[["barrio_id", "barrio", "distrito_id"]], on="barrio")
        .merge(tipos, on="tipo")
        .merge(tamanos[["tamano_id", "tamano_anfitrion"]], on="tamano_anfitrion")
    )
    # los merges conservan el orden de df; recalculamos las banderas alineadas por id
    anuncios = anuncios.set_index("id")
    anuncios["sin_actividad_reciente"] = sin_actividad.groupby(df["id"]).first().astype(int)
    anuncios["es_profesional"] = es_prof.groupby(df["id"]).first().astype(int)
    anuncios["actividad"] = anuncios["sin_actividad_reciente"].map({1: ETIQUETA_SIN, 0: ETIQUETA_CON})
    anuncios["precio_extremo"] = anuncios["precio_extremo"].astype(int)
    anuncios["estancia_larga"] = anuncios["estancia_larga"].astype(int)
    anuncios["activo_12m"] = anuncios["activo_12m"].astype(int)
    anuncios = anuncios.reset_index()[[
        "id", "barrio_id", "tipo_id", "tamano_id", "latitud", "longitud", "personas", "dormitorios",
        "precio", "precio_extremo", "minimo_noches", "disponibilidad_365", "resenas", "resenas_12m",
        "puntuacion", "licencia", "es_profesional", "estancia_larga", "activo_12m",
        "sin_actividad_reciente", "actividad",
    ]].sort_values("id")
    return anuncios, distritos, barrios, tipos, tamanos


def ring_a_arco(anillo):
    """Un anillo de GeoJSON como arco TopoJSON (coordenadas absolutas, sin cuantizar)."""
    return [[round(x, 6), round(y, 6)] for x, y in (p[:2] for p in anillo)]


def geojson_a_topojson(ruta_geo, ruta_topo):
    """Conversión mínima GeoJSON -> TopoJSON: un arco por anillo, sin compartir aristas entre barrios.

    Es TopoJSON válido por estructura, pero NO se ha probado en Power BI (ver GUIA_POWERBI.md).
    """
    geo = json.loads(ruta_geo.read_text(encoding="utf-8"))
    arcos, geometrias = [], []
    for f in geo["features"]:
        g = f["geometry"]
        polis = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        poligonos = []
        for poli in polis:
            anillos = []
            for anillo in poli:
                arcos.append(ring_a_arco(anillo))
                anillos.append([len(arcos) - 1])
            poligonos.append(anillos)
        geometrias.append({
            "type": "MultiPolygon",
            "arcs": poligonos,
            "properties": {"barrio": f["properties"]["neighbourhood"],
                           "distrito": f["properties"]["neighbourhood_group"]},
        })
    topo = {"type": "Topology",
            "objects": {"barrios": {"type": "GeometryCollection", "geometries": geometrias}},
            "arcs": arcos}
    ruta_topo.write_text(json.dumps(topo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Generado: {ruta_topo.relative_to(RAIZ)} ({len(geometrias)} barrios, {len(arcos)} arcos)")
    return topo


def comprobar(df, anuncios, barrios, tamanos, topo):
    """Comprobaciones de integridad y cifras de control para la guía."""
    assert len(anuncios) == len(df), "se han perdido o duplicado anuncios"
    assert anuncios["id"].is_unique
    for col in ("barrio_id", "tipo_id", "tamano_id"):
        assert anuncios[col].notna().all(), f"{col} sin clave"
    assert "host_id" not in anuncios.columns
    assert barrios["n_anuncios"].sum() == len(df)
    nombres_topo = {g["properties"]["barrio"] for g in topo["objects"]["barrios"]["geometries"]}
    assert nombres_topo == set(barrios["barrio"]), "los nombres del mapa no coinciden con dim_barrios"

    sin = anuncios["sin_actividad_reciente"].sum()
    control = pd.DataFrame([
        ("Anuncios", len(anuncios)),
        ("Anuncios con precio", int(anuncios["precio"].notna().sum())),
        ("Mediana de precio ($ publicado)", round(float(anuncios["precio"].median()), 2)),
        ("% anuncios de profesionales (5 o más)", round(100 * anuncios["es_profesional"].mean(), 1)),
        ("% sin actividad reciente", round(100 * sin / len(anuncios), 1)),
        ("Barrios con n insuficiente (menos de 30 anuncios)",
         int((barrios["muestra_anuncios"] == "n insuficiente").sum())),
        ("Barrios con n insuficiente (menos de 30 precios)",
         int((barrios["muestra_precio"] == "n insuficiente").sum())),
    ], columns=["medida", "valor"])
    guardar(control, "valores_control.csv")
    print(control.to_string(index=False))


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RAIZ / "datos" / "limpios" / "anuncios.csv")
    anuncios, distritos, barrios, tipos, tamanos = tablas(df)
    guardar(anuncios, "anuncios.csv")
    guardar(distritos, "dim_distritos.csv")
    guardar(barrios, "dim_barrios.csv")
    guardar(tipos, "dim_tipos.csv")
    guardar(tamanos, "dim_tamano_anfitrion.csv")
    topo = geojson_a_topojson(RAIZ / "datos" / "crudos" / "barrios.geojson", SALIDA / "barrios.topojson")
    comprobar(df, anuncios, barrios, tamanos, topo)


if __name__ == "__main__":
    main()
