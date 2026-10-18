"""Construye dashboard/dashboard.html: un único HTML con los datos incrustados.

Toma dashboard/plantilla.html (maquetación y JavaScript) y sustituye __DATOS__ por las filas de
dashboard/datos/anuncios.csv y los contornos de datos/crudos/barrios.geojson. Todas las cifras
se calculan después en el navegador a partir de esas filas.
"""

import json
import math
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ESCALA = 2000  # unidades del mapa por grado (~55 m de latitud)


def contornos(barrios):
    """Un path SVG por barrio, proyección plana (longitud corregida por cos(lat)), sin puntos repetidos."""
    geo = json.loads((RAIZ / "datos" / "crudos" / "barrios.geojson").read_text(encoding="utf-8"))
    lon0 = min(p[0] for f in geo["features"] for poli in f["geometry"]["coordinates"] for a in poli for p in a)
    lat1 = max(p[1] for f in geo["features"] for poli in f["geometry"]["coordinates"] for a in poli for p in a)
    k = math.cos(math.radians(40.4))
    paths, ancho, alto = {}, 0, 0
    for f in geo["features"]:
        d = []
        for poli in f["geometry"]["coordinates"]:
            for anillo in poli:
                pts, previo = [], None
                for lon, lat, *_ in anillo:
                    p = (round((lon - lon0) * k * ESCALA), round((lat1 - lat) * ESCALA))
                    if p != previo:
                        pts.append(p)
                        previo = p
                if len(pts) >= 3:
                    d.append("M" + "L".join(f"{x},{y}" for x, y in pts) + "Z")
                    ancho = max(ancho, max(x for x, _ in pts))
                    alto = max(alto, max(y for _, y in pts))
        paths[f["properties"]["neighbourhood"]] = "".join(d)
    assert set(paths) == set(barrios), "los barrios del mapa no coinciden con los datos"
    return paths, ancho, alto


def main():
    a = pd.read_csv(RAIZ / "dashboard" / "datos" / "anuncios.csv", encoding="utf-8-sig")
    b = pd.read_csv(RAIZ / "dashboard" / "datos" / "dim_barrios.csv", encoding="utf-8-sig")
    d = pd.read_csv(RAIZ / "dashboard" / "datos" / "dim_distritos.csv", encoding="utf-8-sig")
    t = pd.read_csv(RAIZ / "dashboard" / "datos" / "dim_tipos.csv", encoding="utf-8-sig")
    tam = pd.read_csv(RAIZ / "dashboard" / "datos" / "dim_tamano_anfitrion.csv", encoding="utf-8-sig")

    licencias = ["Nº de registro nacional", "Exenta (declarada)", "Otro", "Sin dato"]
    assert set(a["licencia"]) == set(licencias)
    paths, ancho, alto = contornos(b["barrio"])

    # Índices 0..n-1 en el orden de las tablas de apoyo.
    barrio_pos = {i: n for n, i in enumerate(b["barrio_id"])}
    tipo_pos = {i: n for n, i in enumerate(t["tipo_id"])}
    tam_pos = {i: n for n, i in enumerate(tam["tamano_id"])}
    dist_pos = {i: n for n, i in enumerate(d["distrito_id"])}

    def num(x, dec):
        return None if pd.isna(x) else round(float(x), dec)

    filas = [
        [barrio_pos[r.barrio_id], tipo_pos[r.tipo_id], num(r.precio, 2), num(r.puntuacion, 2),
         int(r.precio_extremo), int(r.es_profesional), int(r.sin_actividad_reciente),
         licencias.index(r.licencia), tam_pos[r.tamano_id]]
        for r in a.itertuples(index=False)
    ]
    datos = {
        "distritos": d["distrito"].tolist(),
        "barrios": [[n, dist_pos[i]] for n, i in zip(b["barrio"], b["distrito_id"])],
        "tipos": t["tipo"].tolist(),
        "tamanos": tam["tamano_anfitrion"].tolist(),
        "licencias": licencias,
        "mapa": {"ancho": ancho, "alto": alto, "paths": [paths[n] for n in b["barrio"]]},
        "filas": filas,
    }
    plantilla = (RAIZ / "dashboard" / "plantilla.html").read_text(encoding="utf-8")
    cuerpo = plantilla.replace("__DATOS__", json.dumps(datos, ensure_ascii=False, separators=(",", ":")))
    (RAIZ / "dashboard" / "dashboard_fragmento.html").write_text(cuerpo, encoding="utf-8")
    pagina = (
        '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n</head>\n<body>\n'
        + cuerpo + "\n</body>\n</html>\n"
    )
    (RAIZ / "dashboard" / "dashboard.html").write_text(pagina, encoding="utf-8")
    print(f"Generado: dashboard/dashboard.html ({len(pagina) / 1e6:.2f} MB, {len(filas)} anuncios)")


if __name__ == "__main__":
    main()
