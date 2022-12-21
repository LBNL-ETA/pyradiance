"""
pyradiance.data
===============
"""
from pathlib import Path
from .model import Scene, View


DATAPATH = Path(__file__).parent / "data"


def model_cubical_office():
    """Return a model of a cubical office."""
    _rootdir = DATAPATH / "model_cubical_office"
    _objpath = _rootdir / Path("Objects")
    scene = Scene("cubical_office")
    scene.add_material(_objpath / "materials.mat")
    scene.add_surface(_objpath / "model.rad")
    scene.add_view(View((17, 5.6, 4), (1, 0, 0), "a", horiz=180, vert=180))
    return scene
