# -*- coding: utf-8 -*-
import geopandas
import pytest
import os
try:
    import rtree
except ImportError:
    rtree = False

import sys
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import swn

datadir = os.path.join('tests', 'data')


@pytest.fixture
def dn():
    shp_srs = os.path.join(datadir, 'DN2_Coastal_strahler1z_stream_vf.shp')
    lines = geopandas.read_file(shp_srs)
    lines.set_index('nzsegment', inplace=True)
    return swn.SurfaceWaterNetwork(lines)


def test_init(dn):
    assert len(dn) == 304
    assert dn.END_NODE == 0
    if rtree:
        assert dn.lines_idx is not None
    else:
        assert dn.lines_idx is None
    assert dn.reaches.index is dn.lines.index
    assert len(dn.headwater) == 154
    assert set(dn.headwater).issuperset([3046700, 3046802, 3050418, 3048102])
    assert list(dn.outlets) == [3046700, 3046737, 3046736]
    cat_group = dn.reaches.groupby('cat_group').count()['to_node']
    assert len(cat_group) == 3
    assert dict(cat_group) == {3046700: 1, 3046737: 173, 3046736: 130}
