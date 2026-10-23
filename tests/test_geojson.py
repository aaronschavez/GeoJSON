"""Dataset contracts and real library integration, without network requests."""
import copy
import hashlib
import json
import math
from pathlib import Path

import folium
import geopandas as gpd
import pydeck as pdk
import pytest
from shapely.geometry import shape
from shapely.validation import explain_validity

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / 'tests/source_contract.json').read_text(encoding='utf-8'))
FILES = sorted(CONTRACT['files'])


def strict_load(path):
    def reject(value):
        raise ValueError(f'Non-finite JSON number: {value}')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON member: {key}')
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), parse_constant=reject,
                      object_pairs_hook=unique)


def polygons(geometry):
    assert geometry['type'] in ('Polygon', 'MultiPolygon')
    return [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']


def source_fingerprint(data):
    """Ignore only the retired CRS and ring direction; retain every value."""
    data = copy.deepcopy(data)
    data.pop('crs', None)
    for feature in data['features']:
        for polygon in polygons(feature['geometry']):
            for i, ring in enumerate(polygon):
                polygon[i] = min(ring, ring[::-1])
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


@pytest.mark.parametrize('filename', FILES)
def test_structure_coordinates_topology_and_source_preservation(filename):
    data = strict_load(ROOT / filename)
    contract = CONTRACT['files'][filename]
    assert data['type'] == 'FeatureCollection'
    assert 'crs' not in data
    assert len(data['features']) == contract['features']
    assert source_fingerprint(data) == contract['fingerprint']
    labels, points = [], []
    for feature in data['features']:
        assert feature['type'] == 'Feature' and 'crs' not in feature
        assert isinstance(feature['properties'], dict)
        label = feature['properties'][contract['label']]
        assert isinstance(label, str) and label.strip()
        labels.append(label)
        geometry = feature['geometry']
        assert 'crs' not in geometry
        parts = polygons(geometry)
        assert parts
        for polygon in parts:
            assert polygon
            for i, ring in enumerate(polygon):
                assert len(ring) >= 4 and ring[0] == ring[-1]
                assert len({tuple(p) for p in ring}) >= 3
                for point in ring:
                    assert len(point) == 2
                    assert all(type(v) in (int, float) and math.isfinite(v) for v in point)
                    lon, lat = point
                    assert -180 <= lon <= 180 and -90 <= lat <= 90
                    assert -88 <= lon <= -82 and 10 <= lat <= 16, (filename, label, point)
                points.extend(ring)
                area2 = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring, ring[1:]))
                assert area2 > 0 if i == 0 else area2 < 0
        geom = shape(geometry)
        assert not geom.is_empty
        assert geom.is_valid, (filename, label, explain_validity(geom))
    assert len(labels) == len(set(labels))
    assert len(points) == contract['positions']
    bounds = [min(p[0] for p in points), min(p[1] for p in points),
              max(p[0] for p in points), max(p[1] for p in points)]
    assert bounds == contract['bounds']


@pytest.mark.parametrize('filename', FILES)
def test_geopandas_read_and_projection_roundtrip(filename):
    data = strict_load(ROOT / filename)
    frame = gpd.read_file(ROOT / filename)
    assert frame.crs.to_epsg() == 4326
    assert len(frame) == len(data['features'])
    assert frame.is_valid.all() and not frame.is_empty.any()
    assert frame.total_bounds.tolist() == pytest.approx(CONTRACT['files'][filename]['bounds'])
    # This explicit round trip is a test, never a rewrite of the source data.
    restored = frame.to_crs(3857).to_crs(4326)
    for original, result in zip(frame.geometry, restored.geometry):
        assert original.equals_exact(result, tolerance=1e-10)


@pytest.mark.parametrize('filename', FILES)
def test_folium_and_pydeck_serialization(filename):
    data = strict_load(ROOT / filename)
    layer = folium.GeoJson(data)
    assert layer.data == data
    map_ = folium.Map(location=[12.8, -85.2], tiles=None)
    layer.add_to(map_)
    assert 'L.geoJson' in map_.get_root().render()
    deck = pdk.Deck(layers=[pdk.Layer('GeoJsonLayer', data=data, pickable=True)],
                    initial_view_state=pdk.ViewState(latitude=12.8, longitude=-85.2, zoom=6),
                    map_style=None)
    assert json.loads(deck.to_json())['layers'][0]['data'] == data


def test_streamlit_dashboard_runs():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(ROOT / 'examples/streamlit_app.py')).run(timeout=30)
    assert not app.exception
    for name in FILES:
        app.selectbox[0].select(name).run(timeout=30)
        assert not app.exception
        assert app.get('deck_gl_json_chart')
