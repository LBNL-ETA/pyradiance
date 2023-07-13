"""
pyradiance is a Python interface for Radiance. It is a collection of Python
modules that provide a high level interface to Radiance. It is designed to
make Radiance easier to use and accessible to Python user.
"""


import logging
import os

from .anci import BINPATH

from .cal import (
    cnt,
    rlam,
    total,
    rcalc,
)

from .cv import (
    bsdf2klems,
    bsdf2ttree,
    ies2rad,
    mgf2rad,
    obj2rad,
    pabopto2bsdf,
    pkgbsdf,
    robjutil,
)

from .gen import (
    genblinds,
    genbsdf,
    gendaylit,
    gendaymtx,
    gensky,
    mkillum,
)

# from .lib import RadianceAPI
from .lib import ABASELIST, BSDF, read_rad, get_view_resolu

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
    mkpmap,
    rcontrib,
    rpict,
    rtrace,
)


from .param import SamplingParameters

from .util import (
    dctimestep,
    evalglare,
    get_header,
    get_image_dimensions,
    getinfo,
    rcode_depth,
    rcode_ident,
    rcode_norm,
    render,
    rfluxmtx,
    rmtxop,
    rtpict,
    rsensor,
    vwrays,
    WrapBSDFInput,
    wrapbsdf,
    xform,
)

logging.getLogger(__name__).addHandler(logging.NullHandler())

os.environ["RAYPATH"] = (
    "." + os.pathsep + os.path.join(os.path.dirname(__file__), "lib")
)
os.environ["PATH"] = str(BINPATH) + os.pathsep + os.environ["PATH"]

__all__ = [
    "ABASELIST",
    "BSDF",
    "bsdf2klems",
    "bsdf2ttree",
    "cnt",
    "dctimestep",
    "evalglare",
    "genblinds",
    "genbsdf",
    "gendaylit",
    "gendaymtx",
    "gensky",
    "get_header",
    "get_image_dimensions",
    "get_view_resolu",
    "getinfo",
    "ies2rad",
    "load_views",
    "mgf2rad",
    "mkillum",
    "mkpmap",
    "obj2rad",
    "oconv",
    "pabopto2bsdf",
    "parse_primitive",
    "pkgbsdf",
    "pvalue",
    "pvaluer",
    "pcond",
    "pfilt",
    "rcalc",
    "rcode_depth",
    "rcode_ident",
    "rcode_norm",
    "rcontrib",
    "read_rad",
    "render",
    "rfluxmtx",
    "rlam",
    "rmtxop",
    "robjutil",
    "rpict",
    "rsensor",
    "rtpict",
    "rtrace",
    "RcModifier",
    "Primitive",
    "Scene",
    "Sensor",
    "SamplingParameters",
    "total",
    "View",
    "vwrays",
    "WrapBSDFInput",
    "wrapbsdf",
    "xform",
]
