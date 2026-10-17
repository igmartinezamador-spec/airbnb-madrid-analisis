"""Limpieza de los anuncios de Inside Airbnb (Madrid, volcado de septiembre 2026).

Entrada : datos/crudos/listings.csv      (90 columnas, 23.109 anuncios)
Salida  : datos/limpios/anuncios.csv     (columnas útiles, con nombres en español)

Cada decisión de limpieza está comentada con su motivo.
"""
import pandas as pd

crudo = pd.read_csv("datos/crudos/listings.csv", low_memory=False)

# 1. Precio: viene como texto con símbolo ("$364.75"). Se convierte a número.
#    OJO: el archivo usa el símbolo "$"; no se puede verificar si la cifra está
#    en euros o en dólares, así que se habla de "precio" sin asegurar la moneda.
precio = pd.to_numeric(crudo["price"].astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce")

# 2. Estado de la licencia. El campo mezcla textos largos con <br />.
#    Se reduce a cuatro categorías mutuamente excluyentes (en este orden de prioridad).
lic = crudo["license"].fillna("")
estado_licencia = pd.Series("Sin dato", index=crudo.index)
estado_licencia[lic.str.len() > 0] = "Otro"
estado_licencia[lic.str.contains("Exempt", case=False)] = "Exenta (declarada)"
estado_licencia[lic.str.contains("ESFCNT")] = "Nº de registro nacional"

# 3. Tamaño del anfitrión: cuántos anuncios tiene la misma persona/empresa.
n = crudo["calculated_host_listings_count"]
tamano = pd.cut(n, bins=[0, 1, 4, 19, float("inf")], labels=["1 anuncio", "2-4", "5-19", "20 o más"]).astype(str)

tipos = {"Entire home/apt": "Vivienda completa", "Private room": "Habitación privada",
         "Shared room": "Habitación compartida", "Hotel room": "Habitación de hotel"}

limpio = pd.DataFrame({
    "id": crudo["id"],
    "host_id": crudo["host_id"],               # se conserva el id, NO el nombre del anfitrión (privacidad)
    "distrito": crudo["neighbourhood_group_cleansed"],
    "barrio": crudo["neighbourhood_cleansed"],
    "latitud": crudo["latitude"],
    "longitud": crudo["longitude"],
    "tipo": crudo["room_type"].map(tipos).fillna(crudo["room_type"]),
    "personas": crudo["accommodates"],
    "dormitorios": crudo["bedrooms"],
    "precio": precio,
    "minimo_noches": crudo["minimum_nights"],
    "disponibilidad_365": crudo["availability_365"],
    "resenas": crudo["number_of_reviews"],
    "resenas_12m": crudo["number_of_reviews_ltm"],
    "puntuacion": crudo["review_scores_rating"],
    "ocupacion_estimada_dias": crudo["estimated_occupancy_l365d"],
    "ingresos_estimados": crudo["estimated_revenue_l365d"],
    "anuncios_del_anfitrion": n,
    "tamano_anfitrion": tamano,
    "licencia": estado_licencia,
})

# 4. Variables derivadas
limpio["precio_extremo"] = limpio["precio"] > 1000          # ~1 % de los anuncios; distorsionan medias
limpio["estancia_larga"] = limpio["minimo_noches"] >= 32     # >= 32 noches: alquiler de temporada, no turístico
limpio["activo_12m"] = limpio["resenas_12m"] > 0             # con alguna reseña en el último año (señal de actividad real)

# 5. Control de calidad
assert limpio["id"].is_unique, "hay ids duplicados"
assert limpio["distrito"].notna().all(), "hay anuncios sin distrito"

limpio.to_csv("datos/limpios/anuncios.csv", index=False)

print(f"Anuncios: {len(limpio):,}")
print(f"Sin precio: {limpio['precio'].isna().sum():,} ({limpio['precio'].isna().mean():.1%})")
print(f"Precio extremo (>1000): {limpio['precio_extremo'].sum():,}")
print(f"Estancia larga (>=32 noches): {limpio['estancia_larga'].sum():,}")
print(f"Activos en 12 meses: {limpio['activo_12m'].sum():,} ({limpio['activo_12m'].mean():.1%})")
print(limpio["licencia"].value_counts().to_string())
