"""
Test pyradiance api
"""
import pyradiance as pr


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
    # scene = pr.load_scene(pr.cubical_office())
    # image = pr.rfluxmtx(scene)
    pass
