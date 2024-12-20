"""
Test pyradiance api
"""

from datetime import datetime
from pathlib import Path

import pytest

import pyradiance as pr
from pyradiance import bsdf


@pytest.fixture
def resources_dir():
    return (Path(__file__).parent / "Resources").absolute()


def test_primitive():
    prim = pr.Primitive("void", "plastic", "white", [], [0.5, 0.6, 0.7, 0, 0])
    assert prim.ptype == "plastic"
    assert prim.bytes == b"void plastic white 0 0 5 0.5 0.6 0.7 0 0 "


def test_gendaylit():
    res = pr.gendaylit(datetime(2022, 2, 1, 12), 37, 122, 120, dirnorm=800, diffhor=100)
    print(res.decode())
    ptypes = {p.ptype for p in pr.parse_primitive(res.decode())}
    assert ptypes == {"light", "brightfunc", "source"}


def test_load_scene(resources_dir: Path):
    """Test the load_scene function."""
    # assert load_scene('test') == 'test'
    scene = pr.Scene("test_scene")
    scene.add_surface(str(resources_dir / "floor 1.rad"))
    scene.add_surface(str(resources_dir / "ceiling.rad"))
    scene.add_material(str(resources_dir / "materials.mat"))
    scene.add_source(str(resources_dir / "sky.rad"))
    assert scene.sid == "test_scene"
    assert str(resources_dir / "floor 1.rad") in scene.surfaces
    assert str(resources_dir / "ceiling.rad") in scene.surfaces
    assert str(resources_dir / "materials.mat") in scene.materials
    assert str(resources_dir / "sky.rad") in scene.sources


def test_load_scene_at_once(resources_dir: Path):
    """Test the load_scene function."""
    # assert load_scene('test') == 'test'
    scene = pr.Scene(
        "test_scene2",
        surfaces=[str(resources_dir / "floor 1.rad")],
        materials=[str(resources_dir / "materials.mat")],
        sources=[str(resources_dir / "sky.rad")],
    )
    assert scene.sid == "test_scene2"
    assert str(resources_dir / "floor 1.rad") in scene.surfaces
    assert str(resources_dir / "materials.mat") in scene.materials
    assert str(resources_dir / "sky.rad") in scene.sources


# def test_render(resources_dir: Path):
#     """Test the render function."""
#     aview = pr.View(
#         position=(1, 1, 1),
#         direction=(0, -1, 0),
#     )
#     scene = pr.Scene("test_scene")
#     scene.add_surface(resources_dir / "floor 1.rad")
#     scene.add_surface(resources_dir / "ceiling.rad")
#     scene.add_material(resources_dir / "materials.mat")
#     scene.add_source(resources_dir / "sky.rad")
#     scene.add_view(aview)
#     pr.render(scene)


def test_rfluxmtx(resources_dir: Path):
    """Test the rfluxmtx function."""
    receiver = resources_dir / "skyr4.rad"
    rays = b"1.0 1 1 0 0 1"
    scene = (
        resources_dir / "materials.mat",
        resources_dir / "floor 1.rad",
        resources_dir / "ceiling.rad",
    )
    result = pr.rfluxmtx(receiver, rays=rays, scene=scene)
    assert len(result) > 0


# def test_read_rad(resources_dir: Path):
#     """Test the read_rad function."""
#     result = pr.read_rad(
#         str(resources_dir / "materials.mat"),
#         str(resources_dir / "floor 1.rad"),
#         str(resources_dir / "ceiling.rad"),
#     )
#     assert len(result) > 0
#     assert isinstance(result[0], pr.Primitive)


# def test_get_view_resolu(resources_dir: Path):
#     view, res = pr.get_view_resolu(str(resources_dir / "test.hdr"))
#     assert view.vtype == "a"
#     assert res.orient == "-Y+X"
#     assert res.xr == 544
#     assert res.yr == 544
#     assert view.horiz == 180
#     assert view.vert == 180


def test_BSDF(resources_dir: Path):
    """Test the bsdf function."""
    sddata = bsdf.load_file(str(resources_dir / "t3.xml"))
    _t = bsdf.direct_hemi(sddata, 30, 0, bsdf.SAMPLE_ALL & ~bsdf.SAMPLE_R)
    assert pytest.approx(_t, 0.0001) == 7.6456e-2
    _a = bsdf.size(sddata, 30.0, 0.0, bsdf.QUERY_MIN + bsdf.QUERY_MAX)
    assert pytest.approx(_a[0], 0.0001) == 7.6699e-4
    _sv = bsdf.query(sddata, 0, 0, 180, 0)
    assert pytest.approx(_sv[1], 0.001) == 4.997


def test_parse_view():
    inp_str = "-vta -vv 180 -vh 180 -vp 0 0 0 -vd 0 -1 0"
    res = pr.parse_view(inp_str)
    assert res.vp == (0, 0, 0)
    assert res.vdir == (0, -1, 0)
    assert res.type == "a"
    assert res.horiz == 180


def test_parse_opt():
    inp_str = "-ab 8 -ad 1024 -I+ -u- -c 8 -aa .1 -lw 1e-8"
    pr.set_render_option(inp_str.split())
    print(pr.get_ab())
    print(pr.get_ad())
    assert pr.get_ab() == 8
    assert pr.get_ad() == 1024


# def test_param():
#     params = param.SamplingParameters()
#     params.aa = 2
#     assert params.aa == 2
#     with pytest.raises(ValueError):
#         params.ab = 0.1
#     with pytest.raises(ValueError):
#         params.av = (0.1, 0.2)
#     params.i = True
#     params.co = True
#     params.u = True
#     assert params.args() == ["-aa", "2", "-i+", "-co+", "-u+"]
#     params2 = param.SamplingParameters(aa=2, i=True, co=True, u=True)
#     assert params2.args() == ["-aa", "2.0", "-i+", "-co+", "-u+"]


def test_ra_tiff(tmpdir: Path, resources_dir: Path):
    """Test the ra_tiff function."""
    hdr = resources_dir / "test.hdr"
    out = tmpdir / "test.tif"
    pr.ra_tiff(hdr, out=str(out))
    assert out.exists()


def test_genbox():
    out_bytes = pr.genbox("mat", "name", 1, 2, 3)
    out_str = out_bytes.decode()
    prims = pr.parse_primitive(out_str)
    assert prims[0] == pr.Primitive(
        "mat", "polygon", "name.1540", [], [1, 0, 0, 1, 0, 3, 0, 0, 3, 0, 0, 0]
    )


def test_genrev():
    out_bytes = pr.genrev("steel", "torus", "sin(2*PI*t)", "2+cos(2*PI*t)", 2)
    out_str = out_bytes.decode()
    prims = pr.parse_primitive(out_str)
    assert prims[0] == pr.Primitive(
        "steel", "ring", "torus.1", [], [0, 0, 1.22464679915e-16, 0, 0, 1, 3, 1]
    )
