"""
Test pyradiance api
"""

import pyradiance as pr
import logging 


LOGGER = logging.getLogger(__name__)


def test_import():
    radiance_version = pr.rtrace(None, None, version=True)
    assert radiance_version != ""

def test_load_scene():
    """Test the load_scene function."""
    # assert load_scene('test') == 'test'
    pass

def test_render():
    """Test the render function."""
    # scene = pr.load_scene(pr.cubical_office())
    # image = pr.render(scene)
    pass

def test_rfluxmtx():
    """Test the rfluxmtx function."""
    receiver = "./Resources/skyr4.rad"
    rays = [[1.0, 1, 1, 0, 0, 1]]
    scene = ("./Resources/materials.mat", "./Resources/floor.rad", "./Resources/ceiling.rad")
    result = pr.rfluxmtx(receiver, rays=rays, scene=scene)
    assert len(result) > 0
