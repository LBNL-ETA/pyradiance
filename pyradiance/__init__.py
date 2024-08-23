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
from .gen import (
    genblinds,
    genbsdf,
    gendaylit,
    gendaymtx,
    gensdaymtx,
    gensky,
    genssky,
    mkillum,
)
from .lib import ABASELIST, BSDF, get_view_resolu, read_rad, spec_xyz, xyz_rgb
from .model import Primitive, Scene, Sensor, View
from .ot import oconv
from .param import SamplingParameters
from .px import falsecolor, pcompos, pcond, pfilt, pvalue, pvaluer, ra_ppm, ra_tiff
from .rt import RcModifier, mkpmap, rcontrib, rpict, rtrace
from .util import (
    RcombInput,
    WrapBSDFInput,
    dctimestep,
    evalglare,
    get_header,
    get_image_dimensions,
    getinfo,
    load_material_smd,
    load_views,
    parse_primitive,
    parse_view,
    rcode_depth,
    rcode_ident,
    rcode_norm,
    rcomb,
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
    "gensdaymtx",
    "gensky",
    "genssky",
    "get_header",
    "get_image_dimensions",
    "get_view_resolu",
    "getinfo",
    "ies2rad",
    "load_views",
    "load_material_smd",
    "mgf2rad",
    "mkillum",
    "mkpmap",
    "obj2rad",
    "obj2mesh",
    "oconv",
    "pabopto2bsdf",
    "parse_primitive",
    "parse_view",
    "pcompos",
    "pkgbsdf",
    "pvalue",
    "pvaluer",
    "pcond",
    "pfilt",
    "ra_tiff",
    "ra_ppm",
    "rcalc",
    "rcode_depth",
    "rcode_ident",
    "rcode_norm",
    "rcontrib",
    "rcomb",
    "RcombInput",
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
