"""
Test pyradiance api
"""
from datetime import datetime
import logging 

import pyradiance as pr
import pytest

LOGGER = logging.getLogger(__name__)


def test_install():
    radiance_version = pr.rtrace(None, None, version=True)
    assert radiance_version != ""


def test_gendaylit():
    res = pr.gendaylit(datetime(2022, 2, 1, 12), 37, 122, 120, dirnorm=800, diffhor=100)
    assert res != b""


def test_load_scene():
    """Test the load_scene function."""
    # assert load_scene('test') == 'test'
    scene = pr.Scene("test_scene")
    scene.add_surface("./Resources/floor.rad")
    scene.add_surface("./Resources/ceiling.rad")
    scene.add_material("./Resources/materials.mat")
    scene.add_source("./Resources/sky.rad")
    assert scene.sid == "test_scene"
    assert "./Resources/floor.rad" in scene.surfaces
    assert "./Resources/ceiling.rad" in scene.surfaces
    assert "./Resources/materials.mat" in scene.materials
    assert "./Resources/sky.rad" in scene.sources
    

def test_render():
    """Test the render function."""
    aview = pr.View(
        position = (1, 1, 1),
        direction = (0, -1, 0),
    )
    scene = pr.Scene("test_scene")
    scene.add_surface("./Resources/floor.rad")
    scene.add_surface("./Resources/ceiling.rad")
    scene.add_material("./Resources/materials.mat")
    scene.add_source("./Resources/sky.rad")
    scene.add_view(aview)
    pr.render(scene)


def test_rfluxmtx():
    """Test the rfluxmtx function."""
    receiver = "./Resources/skyr4.rad"
    rays = b"1.0 1 1 0 0 1"
    scene = ("./Resources/materials.mat", "./Resources/floor.rad", "./Resources/ceiling.rad")
    result = pr.rfluxmtx(receiver, rays=rays, scene=scene)
    assert len(result) > 0


def test_read_rad():
    """Test the read_rad function."""
    result = pr.read_rad("./Resources/materials.mat", "./Resources/floor.rad", "./Resources/ceiling.rad")
    assert len(result) > 0
    assert isinstance(result[0], pr.Primitive)

def test_get_view_resolu():
    view, res = pr.get_view_resolu("./Resources/test.hdr")
    assert view.vtype == "a"
    assert res.orient == "-Y+X"
    assert res.xr == 544
    assert res.yr == 544
    assert view.horiz == 180
    assert view.vert == 180

def test_BSDF():
    """Test the bsdf function."""
    with pr.BSDF("./Resources/t3.xml") as bsdf:
        _t = bsdf.direct_hemi(30, 0, "t")
        assert pytest.approx(_t, 0.0001) == 7.6456e-2
        _a = bsdf.size(30, 0)
        assert pytest.approx(_a[0], 0.0001) == 7.6699e-4
        _sv = bsdf.eval(0, 0, 180, 0)
        assert pytest.approx(_sv[1], 0.001) == 4.997
