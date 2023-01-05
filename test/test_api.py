"""
Test pyradiance api
"""

import pyradiance as pr
import logging 

LOGGER = logging.getLogger(__name__)


def test_install():
    radiance_version = pr.rtrace(None, None, version=True)
    assert radiance_version != ""


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
