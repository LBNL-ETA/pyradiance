"""
# Python interface for Radiance

pyradiance is a Python interface for Radiance. It is a collection of Python
modules that provide a high level interface to Radiance. It is designed to
make Radiance easier to use and accessible to Python user.

"""


import logging
import os


from .cal import (
    BINPATH,
    cnt,
    rlam,
)

from .cv import (
    obj2rad,
)

from .gen import (
    genbsdf,
    gendaymtx,
    gensky,
)

from .model import (
    Sensor,
    Scene,
    View,
    Primitive,
    load_views,
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
    Modifier,
    rcontrib,
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
    wrapbsdf,
    xform,
)

logging.getLogger(__name__).addHandler(logging.NullHandler())

os.environ["RAYPATH"] = os.path.join(os.path.dirname(__file__), "lib")
os.environ["PATH"] = str(BINPATH) + os.pathsep + os.environ["PATH"]

__all__ = [
    "build_scene",
    "cnt",
    "genbsdf",
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
    "rcontrib",
    "render",
    "rfluxmtx",
    "rlam",
    "rmtxop",
    "rpict",
    "rtrace",
    "Modifier",
    "Primitive",
    "Scene",
    "Sensor",
    "SamplingParameters",
    "View",
    "load_views",
    "parse_primitive",
    "wrapbsdf",
    "xform",
    "Scene",
    "Sensor",
    "View",
    "Primitive",
    "SamplingParameters",
    "load_views",
    "parse_primitive",
    "wrapbsdf",
    "xform",
]
