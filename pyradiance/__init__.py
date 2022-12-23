"""
# Python interface for Radiance

pyradiance is a Python interface for Radiance. It is a collection of Python
modules that provide a high level interface to Radiance. It is designed to
make Radiance easier to use and accessible to Python user.

"""


import logging
import os


from .cal import (
    cnt,
)

from .util import (
    get_header,
    get_image_dimensions,
    rmtxop,
)

from .gen import (
    gendaymtx,
    gensky,
)

from .px import (
    pvalue,
    pvaluer,
    pcond,
    pfilt,
)

from .rt import (
    build_scene,
    oconv,
    render,
    rpict,
    rtrace,
)

from .cv import (
    obj2rad,
)

from .model import (
    Sensor, 
    Scene, 
    View, 
    Primitive, 
    parse_view_file, 
    parse_primitive,
)

from .param import SamplingParameters

logging.getLogger(__name__).addHandler(logging.NullHandler())

os.environ["RAYPATH"] = os.path.join(os.path.dirname(__file__), "lib")
os.environ["PATH"] = (
    os.path.join(os.path.dirname(__file__), "bin") + os.pathsep + os.environ["PATH"]
)

__all__ = [
    "cnt",
    "build_scene",
    "gendaymtx",
    "gensky",
    "get_header",
    "get_image_dimensions",
    "obj2rad",
    "oconv",
    "pvalue",
    "pvaluer",
    "pcond",
    "pfilt",
    "render",
    "rmtxop",
    "rpict",
    "rtrace",
    "Scene",
    "Sensor",
    "View",
    "Primitive",
    "SamplingParameters",
    "parse_view_file",
    "parse_primitive",
]
