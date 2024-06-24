"""
pyradiance is a Python interface for Radiance. It is a collection of Python
modules that provide a high level interface to Radiance. It is designed to
make Radiance easier to use and accessible to Python user.
"""

import logging
import os

from .anci import BINPATH, write
from .cal import cnt, rcalc, rlam, total
from .cv import (
    bsdf2klems,
    bsdf2ttree,
    ies2rad,
    mgf2rad,
    obj2mesh,
    obj2rad,
    pabopto2bsdf,
    pkgbsdf,
    robjutil,
)
from .gen import genblinds, genbsdf, gendaylit, gendaymtx, gensky, mkillum
from .lib import ABASELIST, BSDF, get_view_resolu, read_rad, spec_xyz, xyz_rgb
from .model import (
    Primitive,
    Scene,
    Sensor,
    View,
    load_views,
    parse_primitive,
    parse_view,
)
from .ot import oconv
from .param import SamplingParameters
from .px import falsecolor, pcond, pfilt, pvalue, pvaluer, ra_tiff
from .rt import RcModifier, mkpmap, rcontrib, rpict, rtrace
from .util import (
    WrapBSDFInput,
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
    rsensor,
    rtpict,
    vwrays,
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
    "falsecolor",
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
    "obj2mesh",
    "oconv",
    "pabopto2bsdf",
    "parse_primitive",
    "parse_view",
    "pkgbsdf",
    "pvalue",
    "pvaluer",
    "pcond",
    "pfilt",
    "ra_tiff",
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
    "spec_xyz",
    "total",
    "View",
    "vwrays",
    "WrapBSDFInput",
    "wrapbsdf",
    "write",
    "xform",
    "xyz_rgb",
]
