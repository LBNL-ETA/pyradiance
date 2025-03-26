"""
pyradiance is a Python interface for Radiance. It is a collection of Python
modules that provide a high level interface to Radiance. It is designed to
make Radiance easier to use and accessible to Python user.
"""

import os
from importlib.metadata import version
from .anci import BINPATH, write
from .cal import cnt, rcalc, rlam, total
from .bsdf import spec_xyz, xyz_rgb
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
    genbox,
    gendaylit,
    gendaymtx,
    genrev,
    gensdaymtx,
    gensky,
    genssky,
    mkillum,
)
from .genbsdf import (
    ShadingMaterial,
    BlindsGeometry,
    generate_blinds,
    generate_bsdf,
    generate_xml,
)

from .model import Primitive, Scene
from .ot import oconv

from .px import (
    Pcomb,
    falsecolor,
    pcompos,
    pcond,
    pfilt,
    pvalue,
    pvaluer,
    ra_ppm,
    ra_tiff,
)

if os.name == "posix":
    from .radiance_ext import (
        RCCONTEXT,
        RcontribSimulManager,
        RcOutputOp,
        RTdoFIFO,
        RTimmIrrad,
        RTlimDist,
        RTmask,
        RtraceSimulManager,
        RTtraceSources,
        calcontext,
        eval,
        get_ray_params,
        initfunc,
        loadfunc,
        ray_done,
        set_eparams,
        set_option,
        set_ray_params,
        setspectrsamp,
    )

from .rad_params import (
    View,
    Resolu,
    RayParams,
    create_default_view,
    viewfile,
    parse_view,
    get_view_args,
    get_default_ray_params,
    get_ray_params_args,
)

from .rt import mkpmap, Rcontrib, rpict, rtrace
from .util import (
    Xform,
    dctimestep,
    evalglare,
    get_header,
    get_image_dimensions,
    getinfo,
    load_material_smd,
    parse_primitive,
    rcode_depth,
    rcode_ident,
    rcode_norm,
    Rcomb,
    render,
    rfluxmtx,
    rmtxop,
    rsensor,
    vwrays,
    WrapBSDF,
)

__version__ = version("pyradiance")

os.environ["RAYPATH"] = (
    "." + os.pathsep + os.path.join(os.path.dirname(__file__), "lib")
)
os.environ["PATH"] = str(BINPATH) + os.pathsep + os.environ["PATH"]

__all__ = [
    "set_ray_params",
    "get_default_ray_params",
    "RayParams",
    "get_ray_params",
    "parse_view",
    "setspectrsamp",
    "set_option",
    "RCCONTEXT",
    "initfunc",
    "RcontribSimulManager",
    "RtraceSimulManager",
    "RcOutputOp",
    "calcontext",
    "loadfunc",
    "RTdoFIFO",
    "RTimmIrrad",
    "RTlimDist",
    "RTmask",
    "RTtraceSources",
    "ray_done",
    "bsdf2klems",
    "bsdf2ttree",
    "cnt",
    "dctimestep",
    "evalglare",
    "eval",
    "falsecolor",
    "genblinds",
    "genbox",
    "gendaylit",
    "gendaymtx",
    "genrev",
    "gensdaymtx",
    "gensky",
    "genssky",
    "get_header",
    "get_image_dimensions",
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
    "Pcomb",
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
    "Rcontrib",
    "Rcomb",
    "read_rad",
    "render",
    "rfluxmtx",
    "rlam",
    "rmtxop",
    "robjutil",
    "rpict",
    "rsensor",
    "rtrace",
    "RcModifier",
    "Primitive",
    "Scene",
    "SamplingParameters",
    "spec_xyz",
    "set_eparams",
    "total",
    "View",
    "vwrays",
    "WrapBSDF",
    "write",
    "Xform",
    "xyz_rgb",
    "ShadingMaterial",
    "BlindsGeometry",
    "generate_blinds",
    "generate_bsdf",
    "generate_xml",
    "Resolu",
    "create_default_view",
    "viewfile",
    "get_view_args",
    "get_ray_params_args",
]
