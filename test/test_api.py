"""
Test pyradiance api
"""
from datetime import datetime
from pathlib import Path

import pyradiance as pr
from pyradiance import model, param
import pytest


@pytest.fixture
def resources_dir():
    return (Path(__file__).parent / "Resources").absolute()


def test_primitive():
    prim = pr.Primitive("void", "plastic", "white", [], [0.5, 0.6, 0.7, 0, 0])
    assert prim.ptype == "plastic"
    assert prim.bytes == b"void plastic white 0 0 5 0.5 0.6 0.7 0 0 "


def test_install():
    radiance_version = pr.rtrace(None, None, version=True)
    assert radiance_version != ""


def test_gendaylit():
    res = pr.gendaylit(datetime(2022, 2, 1, 12), 37, 122, 120, dirnorm=800, diffhor=100)
    ptypes = {p.ptype for p in pr.parse_primitive(res.decode())}
    assert ptypes == {"light", "brightfunc", "source"}


def test_load_scene(resources_dir: Path):
    """Test the load_scene function."""
    # assert load_scene('test') == 'test'
    scene = pr.Scene("test_scene")
    scene.add_surface(str(resources_dir / "floor.rad"))
    scene.add_surface(str(resources_dir / "ceiling.rad"))
    scene.add_material(str(resources_dir / "materials.mat"))
    scene.add_source(str(resources_dir / "sky.rad"))
    assert scene.sid == "test_scene"
    assert str(resources_dir / "floor.rad") in scene.surfaces
    assert str(resources_dir / "ceiling.rad") in scene.surfaces
    assert str(resources_dir / "materials.mat") in scene.materials
    assert str(resources_dir / "sky.rad") in scene.sources


def test_render(resources_dir: Path):
    """Test the render function."""
    aview = pr.View(
        position=(1, 1, 1),
        direction=(0, -1, 0),
    )
    scene = pr.Scene("test_scene")
    scene.add_surface(resources_dir / "floor.rad")
    scene.add_surface(resources_dir / "ceiling.rad")
    scene.add_material(resources_dir / "materials.mat")
    scene.add_source(resources_dir / "sky.rad")
    scene.add_view(aview)
    pr.render(scene)


def test_rfluxmtx(resources_dir: Path):
    """Test the rfluxmtx function."""
    receiver = resources_dir / "skyr4.rad"
    rays = b"1.0 1 1 0 0 1"
    scene = (
        resources_dir / "materials.mat",
        resources_dir / "floor.rad",
        resources_dir / "ceiling.rad",
    )
    result = pr.rfluxmtx(receiver, rays=rays, scene=scene)
    assert len(result) > 0


def test_read_rad(resources_dir: Path):
    """Test the read_rad function."""
    result = pr.read_rad(
        str(resources_dir / "materials.mat"),
        str(resources_dir / "floor.rad"),
        str(resources_dir / "ceiling.rad"),
    )
    assert len(result) > 0
    assert isinstance(result[0], pr.Primitive)


def test_get_view_resolu(resources_dir: Path):
    view, res = pr.get_view_resolu(str(resources_dir / "test.hdr"))
    assert view.vtype == "a"
    assert res.orient == "-Y+X"
    assert res.xr == 544
    assert res.yr == 544
    assert view.horiz == 180
    assert view.vert == 180


def test_BSDF(resources_dir: Path):
    """Test the bsdf function."""
    with pr.BSDF(str(resources_dir / "t3.xml")) as bsdf:
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


def test_ra_tiff(tmpdir: Path, resources_dir: Path):
    """Test the ra_tiff function."""
    hdr = resources_dir / "test.hdr"
    out = tmpdir / "test.tif"
    pr.ra_tiff(hdr, out=str(out))
    assert out.exists()
