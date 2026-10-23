# GeoJSON de Nicaragua

Cuatro capas para visualización y análisis exploratorio. Los archivos siguen
[RFC 7946](https://www.rfc-editor.org/rfc/rfc7946): coordenadas WGS 84 en grados,
en orden **[longitud, latitud]**, sin miembro heredado `crs`.

| Archivo | Entidades | Propiedad de nombre |
| --- | ---: | --- |
| `Municipio.geojson` | 153 | `Municipio` |
| `Departamento.geojson` | 16 | `Departamento` |
| `Nicaragua.geojson` | 1 | `Pais` |
| `Nicaragua - Zona.geojson` | 6 | `Zona` |

La capa departamental contiene **Zelaya** como una sola entidad. La capa de zonas
representa una agrupación de la fuente. No se garantiza que estas capas coincidan
con una división administrativa vigente. Ver [la auditoría](AUDIT.md) antes de
unir estadísticas o asignar establecimientos a unidades administrativas.

## Instalación y validación

Recomendado: Python 3.11 o posterior, en un entorno virtual.

```sh
python -m pip install -r requirements-test.txt
python -m pytest -q
streamlit run examples/streamlit_app.py
```

GitHub Actions ejecuta las pruebas en cada push y pull request con Python 3.11 y
3.12. Las pruebas no descargan mapas ni consultan servicios externos.

## GeoPandas

```python
import geopandas as gpd

municipios = gpd.read_file('Municipio.geojson')
assert municipios.crs.to_epsg() == 4326
```

Los archivos corregidos ya se leen como EPSG:4326. No necesitan una conversión
desde EPSG:3857. Para una copia antigua con metadatos incorrectos, y solo después
de comprobar que contiene estos mismos valores en grados, se puede corregir la
etiqueta con `gdf.set_crs(4326, allow_override=True)`.
`set_crs` asigna metadatos; `to_crs` transforma números. Transformar los valores
originales como si fueran metros desplazaría los datos hacia el origen del mapa.

Para distancias, áreas o buffers, use una copia en un sistema proyectado adecuado
al área de estudio. No calcule distancias métricas sobre grados ni asuma que
EPSG:3857 es adecuado para medir áreas. Conserve los GeoJSON para intercambio
y visualización en longitud/latitud.

## Folium y PyDeck / Streamlit

```python
import json
from pathlib import Path
import folium
import pydeck as pdk
import streamlit as st

data = json.loads(Path('Municipio.geojson').read_text(encoding='utf-8'))
mapa = folium.Map(location=[12.8, -85.2], zoom_start=6)
folium.GeoJson(data).add_to(mapa)

layer = pdk.Layer('GeoJsonLayer', data=data, pickable=True)
st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=pdk.ViewState(latitude=12.8, longitude=-85.2, zoom=6),
    map_style=None,
))
```

Folium recibe su centro en **[latitud, longitud]**; las coordenadas dentro del
GeoJSON mantienen **[longitud, latitud]** tanto en Folium como en PyDeck.
El ejemplo ejecutable permite elegir las cuatro capas sin requerir una clave
de mapas. La vista de Folium puede guardarse con `mapa.save('mapa.html')`.

Referencias: [GeoPandas: proyecciones](https://geopandas.org/en/stable/docs/user_guide/projections.html),
[Streamlit: st.pydeck_chart](https://docs.streamlit.io/develop/api-reference/charts/st.pydeck_chart).
