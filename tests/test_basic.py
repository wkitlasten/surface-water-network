# -*- coding: utf-8 -*-
import geopandas
import pandas as pd
import pytest
import os
from shapely import wkt
try:
    import rtree
except ImportError:
    rtree = False

import sys
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import swn


def test_bad_init():
    with pytest.raises(ValueError, match='lines must be a GeoDataFrame'):
        swn.SurfaceWaterNetwork(object())

    df = pd.DataFrame({
        'wkt': [
            'LINESTRING Z (40 130 15, 60 100 14)',
            'LINESTRING Z (70 130 15, 60 100 14)',
            'LINESTRING Z (60 100 14, 60 80 12)',
        ],
    })
    df['geometry'] = df['wkt'].apply(wkt.loads)
    # Don't just pass a DataFrame
    with pytest.raises(ValueError, match='lines must be a GeoDataFrame'):
        swn.SurfaceWaterNetwork(df)

    # This works
    lines = geopandas.GeoDataFrame(df, geometry='geometry')
    swn.SurfaceWaterNetwork(lines)

    # Check number of rows
    with pytest.raises(ValueError, match='one or more lines are required'):
        swn.SurfaceWaterNetwork(lines[0:0])

    # Check geom_type
    df['bad_wkt'] = df['wkt'].copy()
    df.loc[1, 'bad_wkt'] = 'MULTILINESTRING Z ((70 130 15, 60 100 14))'
    df['geometry'] = df['bad_wkt'].apply(wkt.loads)
    lines = geopandas.GeoDataFrame(df, geometry='geometry')
    with pytest.raises(ValueError, match='lines must all be LineString types'):
        swn.SurfaceWaterNetwork(lines)

    # Create 2D geometries
    df['bad_wkt'] = df['wkt']\
        .apply(wkt.loads).apply(wkt.dumps, output_dimension=2)
    df['geometry'] = df['bad_wkt'].apply(wkt.loads)
    lines = geopandas.GeoDataFrame(df, geometry='geometry')
    with pytest.raises(ValueError, match='lines must all have Z dimension'):
        swn.SurfaceWaterNetwork(lines)


def test_bad_network():
    # Match in 2D, but not in Z-dimension
    df = pd.DataFrame({
        'wkt': [
            'LINESTRING Z (40 130 15, 60 100 13)',
            'LINESTRING Z (70 130 15, 60 100 14)',
            'LINESTRING Z (60 100 14, 60 80 12)',
        ],
    })
    df['geometry'] = df['wkt'].apply(wkt.loads)
    lines = geopandas.GeoDataFrame(df, geometry='geometry')
    n = swn.SurfaceWaterNetwork(lines)
    n.evaluate_reaches()
    # shows warning, but unable to capture!
    assert n.outlets.values.tolist() == [2]

    # Lines all converge to the same place
    df = pd.DataFrame({
        'wkt': [
            'LINESTRING Z (40 130 15, 60 100 15)',
            'LINESTRING Z (70 130 14, 60 100 14)',
            'LINESTRING Z (60 80 12, 60 100 14)',
        ],
    })
    df['geometry'] = df['wkt'].apply(wkt.loads)
    lines = geopandas.GeoDataFrame(df, geometry='geometry')
    n = swn.SurfaceWaterNetwork(lines)
    n.evaluate_reaches()
    assert n.outlets.values.tolist() == [0, 1, 2]


@pytest.fixture
def basic():
    df = pd.DataFrame({
        'geometry': [
            'LINESTRING Z (40 130 15, 60 100 14)',
            'LINESTRING Z (70 130 15, 60 100 14)',
            'LINESTRING Z (60 100 14, 60 80 12)',
        ],
    })
    df['geometry'] = df['geometry'].apply(wkt.loads)
    lines = geopandas.GeoDataFrame(df, geometry='geometry')
    return swn.SurfaceWaterNetwork(lines)


def test_init(basic):
    # Check defaults
    assert basic.logger is not None
    assert len(basic) == 3
    assert basic.END_NODE is None
    assert basic.reaches is None


def test_evaluate_reaches(basic):
    basic.evaluate_reaches()
    assert basic.END_NODE == -1
    assert basic.lines_idx is None
    assert basic.reaches.index is basic.lines.index
    assert basic.reaches['to_node'].values.tolist() == [2, 2, -1]
    assert basic.outlets.values.tolist() == [2]
