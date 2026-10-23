"""Run from any directory: streamlit run /path/to/examples/streamlit_app.py."""
import json
from pathlib import Path

import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
FILES = ['Municipio.geojson', 'Departamento.geojson', 'Nicaragua.geojson', 'Nicaragua - Zona.geojson']

st.title('Capas geográficas de Nicaragua')
filename = st.selectbox('Capa', FILES)
data = json.loads((ROOT / filename).read_text(encoding='utf-8'))
st.caption(f"{len(data['features'])} entidades · WGS 84 · longitud, latitud")
layer = pdk.Layer('GeoJsonLayer', data=data, pickable=True, filled=True,
                 stroked=True, get_fill_color=[38, 140, 160, 80],
                 get_line_color=[20, 80, 100], line_width_min_pixels=1)
st.pydeck_chart(pdk.Deck(layers=[layer], map_style=None,
                       initial_view_state=pdk.ViewState(latitude=12.8, longitude=-85.2, zoom=6)))
st.caption('La capa departamental conserva la agrupación histórica Zelaya; consulte la auditoría antes de unir estadísticas actuales.')
