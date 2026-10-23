# Auditoría geoespacial — 23 de octubre de 2026

Fuente auditada: `aaronschavez/GeoJSON`, commit
`a2a9342b0964909cccf07780c37f525ac1dff36f`.

## Sistema de coordenadas y corrección

Los cuatro archivos declaraban `urn:ogc:def:crs:EPSG::3857`, pero todos sus
valores son compatibles con longitud y latitud de Nicaragua. Por ejemplo,
el primer punto de Achuapa es `[-86.492331, 13.11322]`.
Las cuatro capas tienen límites idénticos:

`[oeste, sur, este, norte] = [-87.692167, 10.709781, -82.744659, 15.026647]`.

Interpretarlos como metros de Web Mercator situaría las capas cerca del origen
(0°, 0°). La extensión, el ejemplo conocido y la coherencia entre capas respaldan
la interpretación en grados. El archivo no aporta documentación del datum de
origen: la compatibilidad con WGS 84 no sustituye una certificación de precisión
o procedencia cartográfica.

Se retiró `crs` conforme a [RFC 7946, sección 4](https://www.rfc-editor.org/rfc/rfc7946#section-4),
que establece WGS 84 en longitud/latitud para GeoJSON. No se añadió una declaración
EPSG:4326: el sistema ya es implícito en el estándar. No se reproyectó, redondeó,
simplificó ni intercambió ninguna coordenada.

## Geometrías

| Archivo | Entidades | Polygon / MultiPolygon | Posiciones¹ | Anillos exteriores / interiores |
| --- | ---: | --- | ---: | --- |
| Municipio | 153 | 141 / 12 | 6930 | 182 / 5 |
| Departamento | 16 | 11 / 5 | 3222 | 39 / 21 |
| Nicaragua | 1 | 0 / 1 | 1668 | 23 / 30 |
| Nicaragua - Zona | 6 | 2 / 4 | 2526 | 29 / 23 |

¹ Incluye el punto repetido que cierra cada anillo.

Todos los anillos estaban cerrados, pero los 352 tenían orientación inversa
a la regla de la mano derecha. Se invirtió únicamente el recorrido: exteriores
antihorarios e interiores horarios, según RFC 7946 §3.1.6. Esto conserva cada
vértice y cada hueco y no modifica el área cubierta por la geometría.

El contrato `tests/source_contract.json` registra conteos, extensión y una huella
SHA-256 del contenido original normalizado exclusivamente para ignorar `crs`
y el sentido de recorrido. Las pruebas verifican esa huella: cualquier cambio
de valores de coordenadas, propiedades, orden de entidades o estructura se detecta.
Para una futura actualización cartográfica intencional, revise explícitamente
este contrato contra la nueva fuente.

## Resultado de la ejecución

Validación local: **13 pruebas aprobadas** en Windows con Python 3.14.4,
pytest 9.1.1, Shapely 2.2.0, GeoPandas 1.2.0, Folium 0.20.0,
PyDeck 0.9.3 y Streamlit 1.66.1. Las 176 geometrías originales son válidas
y las 176 corregidas conservan su misma superficie geométrica, comprobada con
`Shapely.equals`. No fue necesaria ninguna reparación topológica.
La matriz de GitHub Actions comprueba adicionalmente Python 3.11 y 3.12 al
publicar la propuesta; sus resultados deben consultarse en GitHub.

## Compatibilidad y límites

Las pruebas verifican JSON estricto, estructura, tipos de geometría, números
finitos, orden y rangos de coordenadas, cierre, orientación, nombres únicos,
geometrías no vacías y validez topológica con Shapely. GeoPandas debe reconocer
EPSG:4326 al abrir cada archivo, y una proyección de ida y vuelta de prueba debe
recuperar las geometrías. Folium y PyDeck deben serializar las cuatro capas sin
alterar su contenido; Streamlit debe ejecutar el ejemplo con cada selección.

La validez individual no certifica la exactitud de los límites, la ausencia de
solapamientos/huecos entre entidades ni coincidencia exacta entre escalas. No se
ajustaron fronteras ni se aplicaron reparaciones automáticas como `buffer(0)`.
La capa departamental conserva las 16 entidades originales, incluida Zelaya;
no debe asumirse una correspondencia directa con estadísticas administrativas
actuales. Los nombres no constituyen códigos oficiales de unión.

Los controles de serialización y Streamlit se ejecutan sin navegador ni red:
validan la carga y construcción del gráfico, no la disponibilidad de teselas,
la interacción visual o servicios externos de mapas.
