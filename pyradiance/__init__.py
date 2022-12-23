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
    rlam,
)

from .cv import (
    obj2rad,
)

from .gen import (
    gendaymtx,
    gensky,
)

from .model import (
    Sensor,
    Scene,
    View,
    Primitive,
    parse_view_file,
    parse_primitive,
)

from .ot import (
    oconv,
)

from .px import (
    pvalue,
    pvaluer,
    pcond,
    pfilt,
)

from .rt import (
    rpict,
    rtrace,
)


from .param import SamplingParameters

from .util import (
    build_scene,
    get_header,
    get_image_dimensions,
    render,
    rfluxmtx,
    rmtxop,
)

logging.getLogger(__name__).addHandler(logging.NullHandler())

os.environ["RAYPATH"] = os.path.join(os.path.dirname(__file__), "lib")
os.environ["PATH"] = (
    os.path.join(os.path.dirname(__file__), "bin") + os.pathsep + os.environ["PATH"]
)

__all__ = [
    "build_scene",
    "cnt",
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
    "rfluxmtx",
    "rlam",
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
