# Cómo presentar el proyecto

Todas las cifras están en el `README.md` y salen de los scripts de `codigo/`. Si cambias una cifra aquí, cámbiala allí con el código.

## Pitch de 60 segundos (entrevista)

> Analicé 23.109 anuncios de alquiler turístico de Madrid con los datos públicos de Inside Airbnb. Quería responder cinco preguntas: dónde se concentran y cuánto cuestan, cuánto del mercado es profesional, cómo es la información de licencia, cuántos anuncios muestran actividad reciente y qué relación hay entre precio, tipo y puntuación.
>
> Usé Python con pandas y matplotlib: limpieza, tablas y gráficos reproducibles, con un commit por tarea. Para los precios usé la mediana y no la media, porque hay anuncios con precios muy altos, y solo calculé medianas con 30 o más anuncios con precio.
>
> Lo que encontré: el distrito Centro reúne el 41,3 % de los anuncios; el 53,8 % pertenece a anfitriones con 5 o más anuncios, aunque son solo 782 anfitriones; el 47,2 % no da información de licencia; y el 31,3 % no muestra actividad reciente. La relación entre precio y puntuación es muy débil (Spearman 0,08).
>
> Y fui explícito con los límites: no pude verificar la moneda de los precios, las reseñas son solo un indicio de actividad y todo es descriptivo, sin afirmar causas. Además preparé un tablero interactivo y los datos y la guía para montarlo en Power BI.

## Texto para LinkedIn

**Proyecto de portfolio: alquiler turístico en Madrid con datos abiertos**

He analizado 23.109 anuncios de Inside Airbnb (volcado de septiembre de 2026) con Python para responder cinco preguntas concretas sobre el mercado.

Tres cosas que me llevo:

- El 41,3 % de los anuncios está en el distrito Centro.
- El 53,8 % pertenece a anfitriones con 5 o más anuncios, pero son solo 782 anfitriones.
- El 47,2 % no da información de licencia. "Sin dato" no significa irregular: significa que no hay información.

Lo que más he aprendido no es técnico: decir qué no se puede afirmar. No pude verificar la moneda de los precios, las reseñas son solo un indicio de actividad y el análisis es descriptivo, no causal.

Incluye código reproducible, gráficos, mapas por barrio, un tablero interactivo y una guía para montarlo en Power BI.

Repositorio: https://github.com/igmartinezamador-spec/airbnb-madrid-analisis

Datos: Inside Airbnb, licencia CC BY 4.0. Análisis independiente con fines formativos.

#AnálisisDeDatos #Python #Pandas #DataPortfolio

## Preguntas que te pueden hacer

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué mediana y no media? | Los precios muy altos (164 anuncios por encima de 1.000) desplazan la media y apenas mueven la mediana. |
| ¿Por qué excluyes algunos precios de los gráficos y no del recuento? | Los anuncios extremos existen y cuentan como anuncios, pero distorsionan la escala de los gráficos de precio. |
| ¿Por qué "sin actividad reciente" y no "inactivo"? | Con estos datos no se puede demostrar que un anuncio esté inactivo; solo se ve que no tiene reseñas recientes o que tiene estancia larga. |
| ¿De dónde sale el umbral de profesional (5 anuncios)? | Es una convención mía, no una definición legal. Lo declaré en el README. |
| ¿Qué harías con más tiempo? | Comparar varios volcados para ver la evolución, y verificar la moneda y el significado de la licencia "Otro" con la documentación de la fuente. |
