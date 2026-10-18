# Proyecto de Power BI (.pbip)

Proyecto listo para abrir en **Power BI Desktop (Windows)**. Lo genera `codigo/06_pbip.py` a partir de `dashboard/datos/`.

## Estado: generado y validado, pero no abierto en Power BI

| Estado | Qué |
|---|---|
| **Verificado** | Los 17 archivos JSON (informe, página, 10 visuales, versión, `.pbip`, `.pbir`, `.pbism`) cumplen los **esquemas JSON oficiales de Microsoft** (se comprobó también que el validador detecta errores a propósito). La estructura sigue la documentación de Microsoft sobre proyectos PBIP, TMDL y PBIR. Las cifras de las medidas DAX son las de `dashboard/datos/valores_control.csv`, calculadas en Python. |
| **NO verificado** | Que Power BI Desktop abra el proyecto sin quejas. No se ha podido ejecutar Power BI Desktop desde donde se generó. Los archivos de modelo (`.tmdl`) no tienen un esquema JSON que validar, así que su sintaxis solo la comprobará Power BI al abrirlo. Tampoco se ha verificado el aspecto de los visuales ni que las medidas DAX den las cifras esperadas. |

Si Power BI marca un error al abrir, indica el archivo y la línea. Mándame esa captura y lo corrijo. Si prefieres no depender de esto, la importación manual de `dashboard/GUIA_POWERBI.md` sigue siendo válida.

## Qué incluye

- **Modelo (`airbnb_madrid.SemanticModel`):** 5 tablas (`anuncios`, `dim_distritos`, `dim_barrios`, `dim_tipos`, `dim_tamano_anfitrion`), las 4 relaciones de la guía y 8 medidas DAX en la tabla `anuncios`.
- **Informe (`airbnb_madrid.Report`):** una página con 2 segmentaciones (distrito y tipo), 4 tarjetas (anuncios, mediana de precio, % de profesionales y % sin actividad reciente) y 4 gráficos (anuncios por distrito, licencia por distrito, actividad reciente por distrito y mediana de precio por tipo).
- **No incluye el mapa:** no pude comprobar con el esquema los nombres de los campos del visual de mapa, así que se añade a mano (ver abajo).

## Cómo abrirlo

1. Copia **todo el repositorio** a una carpeta de Windows con ruta corta, por ejemplo `C:\airbnb-madrid-analisis` (Windows limita las rutas a 260 caracteres y un proyecto PBIP genera muchas subcarpetas). Puedes descargarlo con **Code → Download ZIP** en GitHub.
2. Abre `dashboard\powerbi\airbnb_madrid.pbip` con Power BI Desktop (doble clic, o **Abrir** en la pantalla de inicio).
3. Si no abre o se queja del formato, activa en **Archivo → Opciones y configuración → Opciones → Características en versión preliminar** las opciones relacionadas con **proyectos de Power BI (.pbip)** y **TMDL**. Reinicia y vuelve a abrir. (Los nombres exactos dependen de tu versión.)
4. **Ajusta la ruta de los datos.** El modelo lee los CSV desde un parámetro llamado `RutaDatos`, que por defecto es `C:\airbnb-madrid-analisis\dashboard\datos`. Si copiaste el repositorio a otra carpeta: **Inicio → Transformar datos → Administrar parámetros → Editar parámetros**, cambia `RutaDatos` por tu ruta (sin barra final) y pulsa **Aceptar** y luego **Cerrar y aplicar**.
5. Pulsa **Actualizar** para cargar los datos.

## Comprobar que los datos son correctos

Con el informe cargado y sin filtros, las tarjetas deben mostrar:

| Tarjeta | Valor esperado |
|---|---|
| Anuncios | 23.109 |
| Mediana de precio publicado | 151,00 (moneda no verificada) |
| Anuncios de profesionales | 53,8 % |
| Sin actividad reciente | 31,3 % |

Si no coinciden, revisa primero la ruta de `RutaDatos` y el tipo de las columnas en Power Query.

## Añadir el mapa de burbujas (a mano, 1 minuto)

1. Inserta el visual **Mapa** en un hueco libre de la página.
2. **Ubicación:** `dim_barrios[barrio]`. **Latitud:** `dim_barrios[latitud_centro]`. **Longitud:** `dim_barrios[longitud_centro]`. **Tamaño de la burbuja:** medida `Anuncios`.
3. En **Información sobre herramientas**, añade `Mediana precio (n>=30)`.

Puede que tengas que activar los visuales de mapa en **Opciones → Seguridad**.

## Regenerar el proyecto

```
python codigo/04_dashboard.py   # datos de dashboard/datos/
python codigo/06_pbip.py        # proyecto de dashboard/powerbi/
```

No edites los `.tmdl` a la vez que Power BI tiene el proyecto abierto sin guardar: Power BI avisa de cambios externos y puede sobrescribir los no guardados.
