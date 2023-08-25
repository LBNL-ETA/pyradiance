"""
Test pyradiance api
"""
from datetime import datetime
from pathlib import Path
import os

import pyradiance as pr
from pyradiance import model, param
import pytest



@pytest.fixture
def resdir():
    return Path(os.path.dirname(os.path.abspath(__file__))) / "Resources"

def test_primitive():
    prim = pr.Primitive("void", "plastic", "white", [], [0.5, 0.6, 0.7, 0, 0])
    assert prim.ptype == "plastic"
    assert prim.bytes == b"void plastic white 0 0 5 0.5 0.6 0.7 0 0 "

def test_install():
    radiance_version = pr.rtrace(None, None, version=True)
    assert radiance_version != ""


def test_gendaylit():
    res = pr.gendaylit(datetime(2022, 2, 1, 12), 37, 122, 120, dirnorm=800, diffhor=100)
    assert res != b""


def test_load_scene(resdir: Path):
    """Test the load_scene function."""
    # assert load_scene('test') == 'test'
    scene = pr.Scene("test_scene")
    scene.add_surface(str(resdir / "floor.rad"))
    scene.add_surface(str(resdir / "ceiling.rad"))
    scene.add_material(str(resdir / "materials.mat"))
    scene.add_source(str(resdir / "sky.rad"))
    assert scene.sid == "test_scene"
    assert str(resdir / "floor.rad") in scene.surfaces
    assert str(resdir / "ceiling.rad") in scene.surfaces
    assert str(resdir / "materials.mat") in scene.materials
    assert str(resdir / "sky.rad") in scene.sources


def test_render(resdir: Path):
    """Test the render function."""
    aview = pr.View(
        position = (1, 1, 1),
        direction = (0, -1, 0),
    )
    scene = pr.Scene("test_scene")
    scene.add_surface(resdir / "floor.rad")
    scene.add_surface(resdir / "ceiling.rad")
    scene.add_material(resdir / "materials.mat")
    scene.add_source(resdir / "sky.rad")
    scene.add_view(aview)
    pr.render(scene)


def test_rfluxmtx(resdir: Path):
    """Test the rfluxmtx function."""
    receiver = resdir / "skyr4.rad"
    rays = b"1.0 1 1 0 0 1"
    scene = (resdir / "materials.mat", resdir / "floor.rad", resdir / "ceiling.rad")
    result = pr.rfluxmtx(receiver, rays=rays, scene=scene)
    assert len(result) > 0


def test_read_rad(resdir: Path):
    """Test the read_rad function."""
    result = pr.read_rad(
        str(resdir / "materials.mat"),
        str(resdir / "floor.rad"),
        str(resdir / "ceiling.rad")
    )
    assert len(result) > 0
    assert isinstance(result[0], pr.Primitive)

def test_get_view_resolu(resdir: Path ):
    view, res = pr.get_view_resolu(str(resdir/ "test.hdr"))
    assert view.vtype == "a"
    assert res.orient == "-Y+X"
    assert res.xr == 544
    assert res.yr == 544
    assert view.horiz == 180
    assert view.vert == 180

def test_BSDF(resdir: Path):
    """Test the bsdf function."""
    with pr.BSDF(str(resdir / "t3.xml")) as bsdf:
        _t = bsdf.direct_hemi(30, 0, "t")
        assert pytest.approx(_t, 0.0001) == 7.6456e-2
        _a = bsdf.size(30, 0)
        assert pytest.approx(_a[0], 0.0001) == 7.6699e-4
        _sv = bsdf.eval(0, 0, 180, 0)
        assert pytest.approx(_sv[1], 0.001) == 4.997

def test_parse_view():
    inp_str = "-vta -vv 180 -vh 180 -vp 0 0 0 -vd 0 -1 0"
    res = model.parse_view(inp_str)
    assert res.position == [0, 0, 0]
    assert res.direction == [0, -1, 0]
    assert res.vtype == "a"
    assert res.horiz == 180


def test_parse_opt():
    inp_str = "-ab 8 -ad 1024 -I+ -u- -c 8 -aa .1 -lw 1e-8"
    res = param.parse_rcontrib_args(inp_str)
    answer = {
        "ab": 8,
        "ad": 1024,
        "I": True,
        "u": False,
        "c": 8,
        "aa": 0.1,
        "lw": 1e-8,
    }
    assert res == answer


def test_ra_tiff(tmp_path: Path, resdir: Path):
    """Test the ra_tiff function."""
    hdr = resdir / "test.hdr"
    out = tmp_path / "test.tif"
    pr.ra_tiff(hdr, out=str(out))
    assert out.exists()
