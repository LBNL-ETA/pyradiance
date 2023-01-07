"""
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
    bsdf2klems,
    bsdf2ttree,
    ies2rad,
    mgf2rad,
    obj2rad,
    pabopto2bsdf,
    pkgbsdf,
)

from .gen import (
    genbsdf,
    gendaylit,
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
    RcModifier,
    rcontrib,
    rpict,
    rtrace,
)


from .param import SamplingParameters

from .util import (
    get_header,
    get_image_dimensions,
    rcode_depth,
    rcode_norm,
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
    "bsdf2klems",
    "bsdf2ttree",
    "cnt",
    "genbsdf",
    "gendaylit",
    "gendaymtx",
    "gensky",
    "get_header",
    "get_image_dimensions",
    "ies2rad",
    "mgf2rad",
    "obj2rad",
    "oconv",
    "pabopto2bsdf",
    "pkgbsdf",
    "pvalue",
    "pvaluer",
    "pcond",
    "pfilt",
    "rcode_depth",
    "rcode_norm",
    "rcontrib",
    "render",
    "rfluxmtx",
    "rlam",
    "rmtxop",
    "rpict",
    "rtrace",
    "RcModifier",
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
