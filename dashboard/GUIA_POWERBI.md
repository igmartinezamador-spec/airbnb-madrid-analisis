# Guía: dashboard en Power BI Desktop (Windows)

Esta guía es para alguien que usa Power BI por primera vez. Los datos están en `dashboard/datos/` y se generan con `codigo/04_dashboard.py`.

## Qué está verificado y qué no

| Estado | Qué |
|---|---|
| **Verificado por código** | Contenido y estructura de los CSV, claves de relación, que ningún anuncio pierda su clave, que no haya datos de anfitriones, que los 128 nombres de barrio del mapa coincidan con `dim_barrios.csv`, y las cifras de control de la sección 6 (`valores_control.csv`). |
| **NO verificado** | Todo lo que ocurre dentro de Power BI: nombres exactos de menús (cambian según versión e idioma), las fórmulas DAX (no se han ejecutado, solo se han contrastado con las cifras de control calculadas en Python), el aspecto de los visuales y el archivo `barrios.topojson` en el visual "Shape map". |

Si algo no coincide con tu pantalla, busca la opción equivalente. La comprobación definitiva es que las tarjetas de la sección 6 muestren las mismas cifras de control.

**Moneda:** el precio es el "precio publicado" con símbolo "$" en el volcado. No se ha podido verificar la moneda. En Power BI **no** pongas formato de euros ni de dólares: usa número con 2 decimales y rotula "precio publicado ($, moneda no verificada)".

## 1. Archivos que se generan

| Archivo | Qué es | Filas |
|---|---|---|
| `anuncios.csv` | Tabla principal, un anuncio por fila. Sin `host_id` ni datos del anfitrión. | 23.109 |
| `dim_distritos.csv` | Clave `distrito_id` y nombre del distrito. | 21 |
| `dim_barrios.csv` | Clave `barrio_id`, `distrito_id`, recuentos, `muestra_anuncios` y `muestra_precio` ("n suficiente" o "n insuficiente" con menos de 30), y coordenadas del centro del barrio. | 128 |
| `dim_tipos.csv` | Clave `tipo_id` y tipo de alojamiento. | 4 |
| `dim_tamano_anfitrion.csv` | Clave `tamano_id`, tamaño del anfitrión (1 anuncio, 2-4, 5-19, 20 o más) y perfil (particular o profesional). | 4 |
| `barrios.topojson` | Contorno de los barrios, para el visual "Shape map" (**no verificado**). | 128 |
| `valores_control.csv` | Cifras de control para comprobar tu dashboard. No hace falta importarlo. | 7 |

Formato: UTF-8 con marca BOM (para que Windows reconozca bien las tildes), separador coma y punto decimal.

Variables en `anuncios.csv` que conviene entender:

- `es_profesional`: 1 si el anfitrión tiene 5 o más anuncios (convención propia del proyecto), 0 si no.
- `sin_actividad_reciente`: 1 si el anuncio no tiene reseñas en 12 meses **o** tiene estancia mínima de 32 noches o más. `actividad` es el mismo dato en texto.
- `precio_extremo`: 1 si el precio es superior a 1.000. Estos anuncios cuentan en los recuentos.
- Los campos vacíos (anuncios sin precio o sin puntuación) se importan como vacío. Power BI los ignora en las medianas, que es lo que queremos.

## 2. Importar los CSV

1. Abre Power BI Desktop → **Inicio → Obtener datos → Texto o CSV**.
2. Elige `anuncios.csv`. En la vista previa comprueba que **Origen del archivo** sea `65001: Unicode (UTF-8)` y el **delimitador** sea coma. Pulsa **Transformar datos**.
3. En Power Query, comprueba los tipos de columna (icono a la izquierda del nombre):
   - `id`, `*_id`, `personas`, `precio_extremo`, `es_profesional`, `estancia_larga`, `activo_12m`, `sin_actividad_reciente`, `resenas`, `resenas_12m`, `disponibilidad_365` → **Número entero**.
   - `precio`, `puntuacion`, `dormitorios`, `minimo_noches`, `latitud`, `longitud` → **Número decimal**.
   - `licencia`, `actividad` → **Texto**.
4. Repite con los otros cuatro archivos `dim_*.csv`. Después pulsa **Cerrar y aplicar**.
5. (Opcional) Importa también `valores_control.csv` en una tabla aparte para comparar. No la relaciones con nada.

Antes de seguir, en la vista **Datos** selecciona estas columnas, y en la pestaña **Herramientas de columna** ajusta:

- `latitud`, `longitud` (en `anuncios`) y `latitud_centro`, `longitud_centro` (en `dim_barrios`): **Categoría de datos** = Latitud o Longitud, y **Resumir por** = No resumir.
- Todas las columnas `*_id` y `id`: **Resumir por** = No resumir (si no, Power BI las suma).

## 3. Modelo de datos (relaciones)

Ve a la vista **Modelo** (el icono de tres tablas, a la izquierda). Power BI puede crear relaciones solo; **bórralas y revísalas**. Crea estas cuatro arrastrando la clave de una tabla a la otra:

| Desde (muchos) | Hacia (uno) | Cardinalidad | Dirección del filtro |
|---|---|---|---|
| `anuncios[barrio_id]` | `dim_barrios[barrio_id]` | Varios a uno (\*:1) | Única (de dimensión a anuncios) |
| `dim_barrios[distrito_id]` | `dim_distritos[distrito_id]` | Varios a uno (\*:1) | Única |
| `anuncios[tipo_id]` | `dim_tipos[tipo_id]` | Varios a uno (\*:1) | Única |
| `anuncios[tamano_id]` | `dim_tamano_anfitrion[tamano_id]` | Varios a uno (\*:1) | Única |

**Por qué así:**

- **Claves numéricas y no nombres.** Un nombre mal escrito rompería la relación y ocupa más espacio. Cada nombre vive una sola vez, en su tabla de apoyo.
- **`anuncios` no tiene `distrito_id`, a propósito.** El distrito se alcanza por `anuncios → dim_barrios → dim_distritos`. Así hay **un solo camino** entre distrito y anuncios. Con dos caminos (directo y por barrio), Power BI marca la relación como ambigua y deja una inactiva.
- **Dirección única.** Un filtro (por ejemplo, elegir "Centro" en una segmentación) baja desde la dimensión hacia los anuncios y los cuenta. Es lo normal y lo más fácil de entender.
- **Aviso:** las columnas `n_anuncios` y `n_con_precio` de `dim_barrios` son **fijas** y no reaccionan a las segmentaciones. Para cifras que cambian al filtrar, usa siempre las **medidas** de la sección 4.

## 4. Medidas DAX

Para crear una: **Inicio → Nueva medida** (o clic derecho sobre la tabla `anuncios` → Nueva medida) y pega la fórmula. Guárdalas todas en la tabla `anuncios`.

> **No verificado:** si Power BI marca error con las comas, prueba a sustituirlas por punto y coma. El separador depende de la configuración regional.

```dax
Anuncios = COUNTROWS(anuncios)
```
Cuenta filas, es decir, anuncios. Es la base de todas las demás y respeta las segmentaciones. Incluye los anuncios de precio extremo.

```dax
Anuncios con precio = COUNT(anuncios[precio])
```
Cuenta solo los anuncios que tienen precio (los vacíos no cuentan). Sirve para saber en qué tamaño de muestra se apoya una mediana.

```dax
Mediana precio = MEDIAN(anuncios[precio])
```
La mediana es el valor central: la mitad de los precios queda por debajo y la mitad por encima. Se usa en lugar de la media porque unos pocos precios muy altos (hay 164 por encima de 1.000) desplazan la media. `MEDIAN` ignora los vacíos y **no** excluye los precios extremos, igual que las tablas del README.

```dax
Mediana precio (n>=30) =
IF([Anuncios con precio] >= 30, [Mediana precio])
```
Igual que la anterior, pero devuelve vacío si el grupo tiene menos de 30 anuncios con precio, porque una mediana con tan pocos datos engaña. Es la regla del análisis (el beige "n insuficiente" del mapa). Úsala siempre en mapas y tablas por barrio.

```dax
% profesionales =
DIVIDE(CALCULATE([Anuncios], anuncios[es_profesional] = 1), [Anuncios])
```
Proporción de anuncios cuyo anfitrión tiene 5 o más anuncios. `CALCULATE` cuenta solo los anuncios con `es_profesional = 1` y `DIVIDE` entre el total evita el error de dividir por cero. Formato: porcentaje con 1 decimal.

```dax
% sin actividad reciente =
DIVIDE(CALCULATE([Anuncios], anuncios[sin_actividad_reciente] = 1), [Anuncios])
```
Proporción de anuncios sin reseñas en 12 meses o con estancia mínima de 32 noches o más. Es un indicio, no una prueba de que el anuncio no funcione. Formato: porcentaje con 1 decimal.

```dax
% licencia sin dato =
DIVIDE(CALCULATE([Anuncios], anuncios[licencia] = "Sin dato"), [Anuncios])
```
Proporción de anuncios sin información de licencia. "Sin dato" significa que no hay información, no que el anuncio sea irregular.

```dax
Mediana puntuación = MEDIAN(anuncios[puntuacion])
```
Mediana de la puntuación (los anuncios sin puntuación se ignoran).

**Formato:** selecciona la medida → **Herramientas de medida** → para `% ...` elige Porcentaje; para las medianas, número con 2 decimales y **sin símbolo de moneda**.

## 5. Visuales para las 5 preguntas

Haz una página y añade estos visuales (**Visualizaciones** en el panel derecho). El campo "Eje" es la columna que agrupa y "Valores" es la medida.

| Pregunta | Visual | Campos |
|---|---|---|
| **1. Distritos y barrios** | Gráfico de **barras horizontales** | Eje: `dim_distritos[distrito]`, Valores: `[Anuncios]`. Ordena de mayor a menor. |
| | **Tabla** | `dim_distritos[distrito]`, `[Anuncios]`, `[Anuncios con precio]`, `[Mediana precio (n>=30)]`. |
| | **Mapa de burbujas** (ver más abajo) | Barrios, tamaño = `[Anuncios]`. |
| **2. Profesional frente a particular** | **Tarjeta** | `[% profesionales]`. |
| | Gráfico de **barras 100 % apiladas** | Eje: `dim_distritos[distrito]`, Leyenda: `dim_tamano_anfitrion[perfil_anfitrion]`, Valores: `[Anuncios]`. |
| **3. Licencia** | Barras **100 % apiladas** | Eje: `dim_distritos[distrito]`, Leyenda: `anuncios[licencia]`, Valores: `[Anuncios]`. |
| **4. Actividad reciente** | **Tarjeta** | `[% sin actividad reciente]`. |
| | Barras 100 % apiladas | Eje: `dim_distritos[distrito]`, Leyenda: `anuncios[actividad]`, Valores: `[Anuncios]`. |
| **5. Precio, tipo y puntuación** | Barras | Eje: `dim_tipos[tipo]`, Valores: `[Mediana precio (n>=30)]`. |
| | **Dispersión** (por barrio) | Eje X: `[Mediana puntuación]`, Eje Y: `[Mediana precio (n>=30)]`, Detalles: `dim_barrios[barrio]`, Tamaño: `[Anuncios]`. |

Notas por pregunta:

- **Pregunta 5:** el gráfico de dispersión es solo descriptivo. Una relación débil entre precio y puntuación no indica que una cause la otra. En el análisis en Python la correlación de Spearman es 0,08 (calculada sin los precios extremos). Si quieres que un visual de distribución de precios los excluya, pon un **filtro de nivel de visual** `anuncios[precio_extremo]` = 0 y rotúlalo ("se excluyen los anuncios con precio superior a 1.000").
- **Rótulos:** pon títulos con la conclusión y los ejes con unidades ("Anuncios (n)", "Mediana del precio publicado ($, moneda no verificada)"). Para la actividad usa siempre la redacción "Sin actividad reciente (sin reseñas en 12 meses o con estancia mínima de 32 noches o más)".

### Mapa de burbujas (camino principal)

1. Añade el visual **Mapa** (el de burbujas, con icono de globo).
2. **Latitud:** `dim_barrios[latitud_centro]`. **Longitud:** `dim_barrios[longitud_centro]`. **Detalles de la burbuja o Ubicación:** `dim_barrios[barrio]`.
3. **Tamaño de la burbuja:** `[Anuncios]`. **Información sobre herramientas:** `[Mediana precio (n>=30)]` y `[Anuncios con precio]`.
4. Una burbuja por barrio (128), que reacciona a las segmentaciones. Si prefieres un punto por anuncio, usa `anuncios[latitud]` y `anuncios[longitud]` (son 23.109 puntos y pesa más).

> **No verificado:** el visual "Mapa" necesita conexión a internet y, según la versión, activar los visuales de mapa en **Archivo → Opciones → Seguridad → Usar visuales de Mapa y Mapa coroplético**.

### Visual "Shape map" con `barrios.topojson` (no verificado)

El archivo `dashboard/datos/barrios.topojson` es una conversión mínima de `barrios.geojson` hecha con código propio, sin librerías externas (un arco por contorno, sin cuantizar). Cada barrio tiene la propiedad `barrio` con el mismo nombre que `dim_barrios[barrio]` (el código comprobó que los 128 coinciden). **No se ha podido comprobar que Power BI lo cargue ni que el visual coloree bien.**

Si quieres probarlo:

1. Añade el visual **Shape map** (si no aparece, actívalo en **Archivo → Opciones → Características en versión preliminar**).
2. Ubicación: `dim_barrios[barrio]`. Valor de color: `[Mediana precio (n>=30)]`.
3. **Formato → Forma → Agregar mapa** y elige `barrios.topojson`.
4. Si no se colorea, revisa que la clave de coincidencia sea la propiedad `barrio`.

Si falla, no pierdes nada: el mapa de burbujas es el camino principal. La alternativa verificada para ver el mapa coroplético es `graficos/g8_mapa_anuncios_barrio.png` y `graficos/g9_mapa_mediana_precio_barrio.png`, hechos con matplotlib.

### Segmentaciones

Añade el visual **Segmentación de datos** (embudo) y pon:

- `dim_distritos[distrito]` (estilo lista desplegable).
- `dim_tipos[tipo]`.
- Opcional: `dim_tamano_anfitrion[tamano_anfitrion]`.

Al elegir un distrito, todos los visuales se recalculan gracias a las relaciones de la sección 3. Ten en cuenta que, con un solo distrito, los barrios pequeños pueden caer bajo el mínimo de 30 precios y mostrar la mediana vacía: es lo esperado.

## 6. Cifras de control

Crea una **Tarjeta** por medida, sin filtros ni segmentaciones. Deben coincidir con `dashboard/datos/valores_control.csv`, que genera el código:

| Medida | Valor esperado |
|---|---|
| `[Anuncios]` | 23.109 |
| `[Anuncios con precio]` | 18.785 |
| `[Mediana precio]` | 151 |
| `[% profesionales]` | 53,8 % |
| `[% sin actividad reciente]` | 31,3 % |

Además, `dim_barrios` marca 27 barrios con menos de 30 anuncios y 32 con menos de 30 anuncios con precio. Esta segunda cifra es la que decide el "n insuficiente" de las medianas. Si una tarjeta no coincide, revisa en este orden: tipo de la columna (decimal frente a texto), relaciones y que no haya filtros activos.

## 7. Diseño de la página

Una sola página en horizontal (16:9), de arriba a abajo:

```
+--------------------------------------------------------------+
| Título: Alquiler turístico en Madrid (Inside Airbnb, 2026-09-17) |
+--------+--------+--------+--------+-------------+------------+
| Tarjeta| Tarjeta| Tarjeta| Tarjeta| Segment.    | Segment.   |
|Anuncios|Mediana |% prof. |% sin   | Distrito    | Tipo       |
|        |precio  |        |activ.  |             |            |
+--------+--------+--------+--------+-------------+------------+
| Mapa de burbujas (barrios)        | Barras: anuncios por     |
|                                   | distrito (P1)            |
+-----------------------------------+--------------------------+
| Barras 100 %: perfil (P2) | Licencia (P3) | Actividad (P4)   |
+-----------------------------------+--------------------------+
| Mediana precio por tipo (P5)      | Dispersión precio/punt.  |
+--------------------------------------------------------------+
| Nota: precio publicado ($, moneda no verificada); medianas con |
| n >= 30; descriptivo, no causal.                             |
+--------------------------------------------------------------+
```

Recomendaciones:

- **Colores:** un solo color base (gris azulado) y uno de énfasis (naranja) para lo que quieras destacar, como en los gráficos de Python. Evita arcoíris.
- **Títulos que dicen la conclusión.** En los visuales activa el título y escribe la frase (por ejemplo, "Centro concentra el 41 % de los anuncios"). Como los títulos de Power BI son texto fijo, **escribe la cifra solo después de comprobarla** en el visual, o usa un título dinámico con una medida.
- **Nota al pie** con la moneda no verificada, el mínimo de 30 anuncios con precio y la advertencia de que el análisis es descriptivo y no causal.
- **Límites:** las reseñas son solo un indicio de actividad; la licencia "Sin dato" significa que no hay información; el umbral de profesional (5 anuncios) es una convención de este proyecto.
