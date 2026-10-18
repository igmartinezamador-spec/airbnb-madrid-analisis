"""Genera un proyecto de Power BI (.pbip) en dashboard/powerbi/ a partir de dashboard/datos/.

Crea el modelo semántico en formato TMDL (5 tablas, 4 relaciones, medidas DAX) y un informe en formato PBIR
con una página de visuales básicos. Los formatos siguen la documentación y los esquemas JSON públicos de
Microsoft. NO se ha podido abrir en Power BI Desktop desde esta máquina (macOS): ver dashboard/powerbi/LEEME.md.
"""

import json
import shutil
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "dashboard" / "datos"
SALIDA = RAIZ / "dashboard" / "powerbi"
NOMBRE = "airbnb_madrid"
RUTA_DEFECTO = r"C:\airbnb-madrid-analisis\dashboard\datos"

ESQ = "https://developer.microsoft.com/json-schemas/fabric"
ENTIDADES = {
    "anuncios": "anuncios.csv",
    "dim_distritos": "dim_distritos.csv",
    "dim_barrios": "dim_barrios.csv",
    "dim_tipos": "dim_tipos.csv",
    "dim_tamano_anfitrion": "dim_tamano_anfitrion.csv",
}
CLAVES = {"id", "barrio_id", "tipo_id", "tamano_id", "distrito_id"}
ENTEROS = {
    "id", "barrio_id", "tipo_id", "tamano_id", "distrito_id", "personas", "precio_extremo", "disponibilidad_365",
    "resenas", "resenas_12m", "es_profesional", "estancia_larga", "activo_12m", "sin_actividad_reciente",
    "n_anuncios", "n_con_precio",
}
DECIMALES = {
    "latitud", "longitud", "dormitorios", "precio", "minimo_noches", "puntuacion", "latitud_centro", "longitud_centro",
}

MEDIDAS = [
    ("Anuncios", "COUNTROWS(anuncios)", "#,0"),
    ("Anuncios con precio", "COUNT(anuncios[precio])", "#,0"),
    ("Mediana precio", "MEDIAN(anuncios[precio])", "#,0.00"),
    ("Mediana precio (n>=30)", "IF([Anuncios con precio] >= 30, [Mediana precio])", "#,0.00"),
    ("% profesionales", "DIVIDE(CALCULATE([Anuncios], anuncios[es_profesional] = 1), [Anuncios])", "0.0%"),
    ("% sin actividad reciente",
     "DIVIDE(CALCULATE([Anuncios], anuncios[sin_actividad_reciente] = 1), [Anuncios])", "0.0%"),
    ("% licencia sin dato", 'DIVIDE(CALCULATE([Anuncios], anuncios[licencia] = "Sin dato"), [Anuncios])', "0.0%"),
    ("Mediana puntuación", "MEDIAN(anuncios[puntuacion])", "0.00"),
]

RELACIONES = [
    ("anuncios", "barrio_id", "dim_barrios", "barrio_id"),
    ("dim_barrios", "distrito_id", "dim_distritos", "distrito_id"),
    ("anuncios", "tipo_id", "dim_tipos", "tipo_id"),
    ("anuncios", "tamano_id", "dim_tamano_anfitrion", "tamano_id"),
]


def tipo_columna(nombre):
    if nombre in ENTEROS:
        return "int64", "Int64.Type"
    if nombre in DECIMALES:
        return "double", "type number"
    return "string", "type text"


def escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8", newline="\n")  # UTF-8 sin BOM, como pide la documentación


def tmdl_tabla(entidad, archivo):
    cols = list(pd.read_csv(DATOS / archivo, encoding="utf-8-sig", nrows=1).columns)
    tipos_m = ",".join(f'{{"{c}", {tipo_columna(c)[1]}}}' for c in cols)
    t = [f"table {entidad}", ""]
    if entidad == "anuncios":
        for nombre, dax, fmt in MEDIDAS:
            t += [f"\tmeasure '{nombre}' = {dax}", f"\t\tformatString: {fmt}", ""]
    for c in cols:
        dt = tipo_columna(c)[0]
        t.append(f"\tcolumn {c}")
        t.append(f"\t\tdataType: {dt}")
        if c in CLAVES:
            t.append("\t\tisHidden")
        t.append("\t\tformatString: " + ("0" if dt == "int64" else "General" if dt == "string" else "0.00"))
        t.append("\t\tsummarizeBy: " + ("none" if (c in CLAVES or dt == "string" or c.startswith("lat") or c.startswith("lon")) else "sum"))
        if c.startswith("latitud"):
            t.append("\t\tdataCategory: Latitude")
        if c.startswith("longitud"):
            t.append("\t\tdataCategory: Longitude")
        if entidad == "dim_tamano_anfitrion" and c == "tamano_anfitrion":
            t.append("\t\tsortByColumn: tamano_id")
        t.append(f"\t\tsourceColumn: {c}")
        t.append("")
    t += [
        f"\tpartition {entidad} = m",
        "\t\tmode: import",
        "\t\tsource =",
        "\t\t\tlet",
        f'\t\t\t    Origen = Csv.Document(File.Contents(RutaDatos & "\\{archivo}"), [Delimiter=",", Columns={len(cols)}, Encoding=65001, QuoteStyle=QuoteStyle.None]),',
        "\t\t\t    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),",
        f'\t\t\t    Tipos = Table.TransformColumnTypes(Encabezados, {{{tipos_m}}}, "en-US")',
        "\t\t\tin",
        "\t\t\t    Tipos",
        "",
    ]
    return "\n".join(t)


def modelo():
    base = SALIDA / f"{NOMBRE}.SemanticModel"
    escribir(base / "definition.pbism", json.dumps(
        {"$schema": f"{ESQ}/item/semanticModel/definitionProperties/1.0.0/schema.json", "version": "4.0", "settings": {}},
        indent=2))
    d = base / "definition"
    escribir(d / "database.tmdl", "database\n\tcompatibilityLevel: 1600\n")
    refs = "\n".join(f"ref table {e}" for e in ENTIDADES)
    escribir(d / "model.tmdl", (
        "model Model\n\tculture: es-ES\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
        "\tsourceQueryCulture: es-ES\n\n" + refs + "\n\nref expression RutaDatos\n"))
    escribir(d / "expressions.tmdl", (
        f'expression RutaDatos = "{RUTA_DEFECTO}" meta [IsParameterQuery=true, IsParameterQueryRequired=true, Type="Text"]\n'
        "\tlineageTag: 5b1c3c1e-6a53-4d57-9d0a-0c0f0b1a7e01\n"))
    rel = []
    for i, (d1, c1, d2, c2) in enumerate(RELACIONES, 1):
        rel += [f"relationship 7c1d2e3f-0000-4000-8000-00000000000{i}", f"\tfromColumn: {d1}.{c1}", f"\ttoColumn: {d2}.{c2}", ""]
    escribir(d / "relationships.tmdl", "\n".join(rel))
    for entidad, archivo in ENTIDADES.items():
        escribir(d / "tables" / f"{entidad}.tmdl", tmdl_tabla(entidad, archivo))


# ---------- Informe (PBIR) ----------
def campo(tipo, tabla, prop):
    return {tipo: {"Expression": {"SourceRef": {"Entity": tabla}}, "Property": prop}}


def proy(tipo, tabla, prop):
    return {"field": campo(tipo, tabla, prop), "queryRef": f"{tabla}.{prop}", "nativeQueryRef": prop}


def titulo(texto):
    return {"title": [{"properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "text": {"expr": {"Literal": {"Value": "'" + texto.replace("'", "''") + "'"}}},
    }}]}


def visual(nombre, x, y, w, h, tipo, roles, texto, orden=None):
    q = {"queryState": {r: {"projections": p} for r, p in roles.items()}}
    if orden:
        q["sortDefinition"] = {"sort": [{"field": orden, "direction": "Descending"}]}
    return nombre, {
        "$schema": f"{ESQ}/item/report/definition/visualContainer/2.13.0/schema.json",
        "name": nombre,
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": {"visualType": tipo, "query": q, "visualContainerObjects": titulo(texto), "drillFilterOtherVisuals": True},
    }


def informe():
    base = SALIDA / f"{NOMBRE}.Report"
    escribir(base / "definition.pbir", json.dumps({
        "$schema": f"{ESQ}/item/report/definitionProperties/2.0.0/schema.json", "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NOMBRE}.SemanticModel"}}}, indent=2))
    d = base / "definition"
    escribir(d / "version.json", json.dumps(
        {"$schema": f"{ESQ}/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"}, indent=2))
    escribir(d / "report.json", json.dumps({
        "$schema": f"{ESQ}/item/report/definition/report/3.3.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY24SU10",
                                          "reportVersionAtImport": {"visual": "1.8.0", "report": "2.0.0", "page": "1.3.0"},
                                          "type": "SharedResources"}}}, indent=2))
    pagina = "a1b2c3d4e5f6a7b8c9d0"
    escribir(d / "pages" / "pages.json", json.dumps({
        "$schema": f"{ESQ}/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": [pagina], "activePageName": pagina}, indent=2))
    escribir(d / "pages" / pagina / "page.json", json.dumps({
        "$schema": f"{ESQ}/item/report/definition/page/2.1.0/schema.json", "name": pagina,
        "displayName": "Alquiler turístico en Madrid", "displayOption": "FitToPage", "height": 720, "width": 1280}, indent=2))

    m = lambda p: proy("Measure", "anuncios", p)
    med_tipo = campo("Measure", "anuncios", "Mediana precio (n>=30)")
    anuncios = campo("Measure", "anuncios", "Anuncios")
    vis = [
        visual("b1c2d3e4f5a6b7c8d901", 16, 16, 200, 470, "slicer",
               {"Values": [proy("Column", "dim_distritos", "distrito")]}, "Distrito"),
        visual("b1c2d3e4f5a6b7c8d902", 16, 498, 200, 206, "slicer",
               {"Values": [proy("Column", "dim_tipos", "tipo")]}, "Tipo de alojamiento"),
        visual("b1c2d3e4f5a6b7c8d903", 232, 16, 249, 96, "card", {"Values": [m("Anuncios")]}, "Anuncios"),
        visual("b1c2d3e4f5a6b7c8d904", 493, 16, 249, 96, "card", {"Values": [m("Mediana precio (n>=30)")]},
               "Mediana de precio publicado ($, moneda no verificada)"),
        visual("b1c2d3e4f5a6b7c8d905", 754, 16, 249, 96, "card", {"Values": [m("% profesionales")]},
               "Anuncios de profesionales (5 o más)"),
        visual("b1c2d3e4f5a6b7c8d906", 1015, 16, 249, 96, "card", {"Values": [m("% sin actividad reciente")]},
               "Sin actividad reciente"),
        visual("b1c2d3e4f5a6b7c8d907", 232, 124, 510, 285, "clusteredBarChart",
               {"Category": [proy("Column", "dim_distritos", "distrito")], "Y": [m("Anuncios")]},
               "Anuncios por distrito", orden=anuncios),
        visual("b1c2d3e4f5a6b7c8d908", 754, 124, 510, 285, "hundredPercentStackedBarChart",
               {"Category": [proy("Column", "dim_distritos", "distrito")],
                "Series": [proy("Column", "anuncios", "licencia")], "Y": [m("Anuncios")]},
               "Licencia por distrito (% de anuncios)"),
        visual("b1c2d3e4f5a6b7c8d909", 232, 421, 510, 283, "hundredPercentStackedBarChart",
               {"Category": [proy("Column", "dim_distritos", "distrito")],
                "Series": [proy("Column", "anuncios", "actividad")], "Y": [m("Anuncios")]},
               "Actividad reciente por distrito (% de anuncios)"),
        visual("b1c2d3e4f5a6b7c8d910", 754, 421, 510, 283, "clusteredBarChart",
               {"Category": [proy("Column", "dim_tipos", "tipo")], "Y": [m("Mediana precio (n>=30)")]},
               "Mediana de precio por tipo ($, moneda no verificada)", orden=med_tipo),
    ]
    for nombre, cuerpo in vis:
        escribir(d / "pages" / pagina / "visuals" / nombre / "visual.json", json.dumps(cuerpo, indent=2, ensure_ascii=False))


def main():
    if SALIDA.exists():
        shutil.rmtree(SALIDA / f"{NOMBRE}.SemanticModel", ignore_errors=True)
        shutil.rmtree(SALIDA / f"{NOMBRE}.Report", ignore_errors=True)
    modelo()
    informe()
    escribir(SALIDA / f"{NOMBRE}.pbip", json.dumps({
        "$schema": f"{ESQ}/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0",
        "artifacts": [{"report": {"path": f"{NOMBRE}.Report"}}], "settings": {"enableAutoRecovery": True}}, indent=2))
    escribir(SALIDA / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
    print(f"Generado: dashboard/powerbi/{NOMBRE}.pbip")


if __name__ == "__main__":
    main()
