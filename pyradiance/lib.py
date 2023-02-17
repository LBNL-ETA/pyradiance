"""
Routines for calling Radiance C functions
"""

from ctypes import (
    CDLL,
    c_int,
    c_char_p,
    c_double,
    c_float,
    c_short,
    c_long,
    c_char,
    c_void_p,
    Structure,
    POINTER,
    byref,
)
from math import radians, sin, cos
import os
# from random import randint
from typing import Optional, Tuple

from .model import Primitive, View, Resolu


FVECT = c_double * 3
C_CNSS = 41                     # number of spectral samples
SDmaxCh = 3                     # max number of channels
SDnameLn = 128                  # max BSDF name length

SFLAGS = {
    "s": 15,
    "t": 14,
    "r": 13,
    "ts": 6,
    "rs": 5,
    "td": 10,
    "rd": 9,
}

QFLAGS = {
    "min_max": 3,
    "min": 1,
    "max": 2,
    "val": 0,
}

OTYPES = [
    "polygon",
    "cone",
    "sphere",
    "texfunc",
    "ring",
    "cylinder",
    "inst",
    "cup",
    "bubble",
    "tube",
    "mesh",
    "alias",
    "plastic",
    "metal",
    "glass",
    "trans",
    "dielectric",
    "plastic2",
    "metal2",
    "trans2",
    "interface",
    "plasfunc",
    "metfunc",
    "brightfunc",
    "brightdata",
    "brighttext",
    "colorpict",
    "glow",
    "source",
    "light",
    "illum",
    "spotlight",
    "mist",
    "mirror",
    "transfunc",
    "BRTDfunc",
    "BSDF",
    "aBSDF",
    "plasdata",
    "metdata",
    "transdata",
    "colorfunc",
    "antimatter",
    "colordata",
    "colortext",
    "texdata",
    "mixfunc",
    "mixdata",
    "mixtext",
    "mixpict",
    "unidirecting material",
    "bidirecting material",
    "ashik2",
]

ORIENT_FLAG = [
    "+X+Y",
    "-X+Y",
    "+X-Y",
    "-X-Y",
    "+Y+X",
    "+Y-X",
    "-Y+X",
    "-Y-X",
]


class C_COLOR(Structure):
    _fields_ = [
        ("clock", c_double), 
        ("client_data", c_void_p), 
        ("flags", c_short),
        ("ssamp", c_short * C_CNSS),
        ("ssum", c_long),
        ("cx", c_float),
        ("cy", c_float),
        ("eff", c_float),
    ]


class RESOLU(Structure):
    _fields_ = [
        ("rp", c_int),
        ("xr", c_int),
        ("yr", c_int),
    ]


class FUNARGS(Structure):
    _fields_ = [
        ("sarg", POINTER(c_char_p)),
        ("farg", POINTER(c_double)),
        ("nsargs", c_short),
        ("nfargs", c_short),
    ]


class OBJREC(Structure):
    _fields_ = [
        ("omod", c_int),
        ("otype", c_short),
        ("oname", c_char_p),
        ("oargs", FUNARGS),
        ("os", c_char_p),
    ]


class VIEW(Structure):
    _fields_ = [
        ("type", c_char),
        ("vp", FVECT),
        ("vdir", FVECT),
        ("vup", FVECT),
        ("vdist", c_double),
        ("horiz", c_double),
        ("vert", c_double),
        ("hoff", c_double),
        ("voff", c_double),
        ("vfore", c_double),
        ("vaft", c_double),
        ("hvec", FVECT),
        ("vvec", FVECT),
        ("hn2", c_double),
        ("vn2", c_double),
    ]


class SDValue(Structure):
    _fields_ = [
        ("cieY", c_double),
        ("spec", C_COLOR),
    ]


class SDCDst(Structure):
    _fields_ = [
        ("SD_CDIST_BASE", c_void_p),
    ]


class SDFunc(Structure):
    _fields_ = [
        ("getBSDFs", POINTER(c_int)),
        ("queryProjSA", POINTER(c_int)),
        ("getCDist", POINTER(SDCDst)),
        ("sampCDist", POINTER(c_int)),
        ("freeSC", c_void_p),
    ]


class SDComponent(Structure):
    _fields_ = [
        ("cspec", C_COLOR * SDmaxCh),
        ("func", POINTER(SDFunc)),
        ("dist", c_void_p),
        ("cdList", POINTER(SDCDst)),
    ]


class SDSpectralDF(Structure):
    _fields_ = [
        ("minProjSA", c_double),
        ("maxHemi", c_double),
        ("ncomp", c_int),
        ("comp", SDComponent * 1),
    ]


class SDData(Structure):
    _fields_ = [
        ("name", c_char * SDnameLn),
        ("matn", c_char * SDnameLn),
        ("makr", c_char * SDnameLn),
        ("mgf", c_char_p),
        ("dim", c_double * 3),
        ("rLambFront", SDValue),
        ("rLambBack", SDValue),
        ("tLambFront", SDValue),
        ("tLambBack", SDValue),
        ("rf", POINTER(SDSpectralDF)),
        ("rb", POINTER(SDSpectralDF)),
        ("tf", POINTER(SDSpectralDF)),
        ("tb", POINTER(SDSpectralDF)),
    ]


LIBRC = CDLL(os.path.join(os.path.dirname(__file__), "libraycalls.so"))
LIBRC.SDcacheFile.argtypes = [c_char_p]
LIBRC.SDcacheFile.restype = POINTER(SDData)
LIBRC.SDfreeCache.argtypes = [POINTER(SDData)]
LIBRC.SDfreeCache.restype = None
LIBRC.SDsizeBSDF.argtypes = [POINTER(c_double), FVECT, POINTER(c_double), c_int, POINTER(SDData)]
LIBRC.SDsizeBSDF.restype = c_int
LIBRC.SDevalBSDF.argtypes = [POINTER(SDValue), FVECT, FVECT, POINTER(SDData)]
LIBRC.SDevalBSDF.restype = c_int
LIBRC.SDdirectHemi.argtypes = [FVECT, c_int, POINTER(SDData)]
LIBRC.SDdirectHemi.restype = c_double
LIBRC.SDsampBSDF.argtypes = [POINTER(SDValue), FVECT, c_double, c_int, POINTER(SDData)]
LIBRC.SDsampBSDF.restype = c_int
LIBRC.readobj.argtypes = [c_char_p]
LIBRC.readobj.restype = POINTER(OBJREC)
LIBRC.freeobjects.argtypes = [c_int, c_int]
LIBRC.freeobjects.restype = None
LIBRC.viewfile.argtypes = [c_char_p, POINTER(VIEW), POINTER(RESOLU)]
LIBRC.viewfile.restype = None


def vec_from_deg(theta: float, phi: float) -> Tuple[float, float, float]:
    theta = radians(theta)
    phi = radians(phi)
    v0 = v1 = sin(theta)
    v0 *= cos(phi)
    v1 *= sin(phi)
    v2 = cos(theta)
    return v0, v1, v2


class BSDF:
    """A BSDF object""" 
    def __init__(self, path):
        """Initialize the BSDF object from a file"""
        self.sd = LIBRC.SDcacheFile(path.encode())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        LIBRC.SDfreeCache(self.sd)

    def size(self, theta: float, phi: float, qflags: str="min_max", t2: Optional[float]=None, p2: Optional[float]=None):
        """Get resolution (in proj. steradians) for given direction(s)
        Args:
            theta: zenith angle (degrees)
            phi: azimuth angle (degrees)
            qflags: query flags (min_max, min, max, avg)
            t2: second zenith angle (degrees)
            p2: second azimuth angle (degrees)
        Returns:
            resolution(s) (in proj. steradians)
        """
        proj_sa = (c_double * 2)(0, 0) 
        v1 = (c_double * 3)(*vec_from_deg(theta, phi))
        v2 = None
        if (t2 is not None) and (p2 is not None):
            v2 = (c_double * 3)(*vec_from_deg(t2, p2))
            v1, v2 = v2, v1
        LIBRC.SDsizeBSDF(proj_sa, v1, v2, QFLAGS[qflags], self.sd)
        return proj_sa

    def eval(self, itheta: float, iphi: float, otheta: float, ophi: float):
        """Query BSDF for given path.
        Args:
            itheta: incident zenith angle (degrees)
            iphi: incident azimuth angle (degrees)
            otheta: outgoing zenith angle (degrees)
            ophi: outgoing azimuth angle (degrees)
        Returns:
            A BSDF SDValue object
        """
        value = SDValue()
        in_vec = (c_double * 3)(*vec_from_deg(itheta, iphi))
        out_vec = (c_double * 3)(*vec_from_deg(otheta, ophi))
        LIBRC.SDevalBSDF(byref(value), in_vec, out_vec, self.sd)
        return value

    def direct_hemi(self, theta, phi, sflag: str):
        """Get hemispherical integral of BSDF.
        Args:
            theta: zenith angle (degrees)
            phi: azimuth angle (degrees)
            sflag: sampling flag (t, ts, td, r, rs, rd, s)
        Returns:
            hemispherical value
        """
        in_vec = (c_double * 3)(*vec_from_deg(theta, phi))
        return LIBRC.SDdirectHemi(in_vec, SFLAGS[sflag.lower()], self.sd)

    def sample(self, theta, phi, randx, sflag:str):
        """Sample BSDF for given direction.
        """
        # rand_max = 0x7fffffff
        # randx = (i + randint(0, rand_max) * (1 / (rand_max + .5))) / nsamp
        value = SDValue()
        vout = (c_double * 3)(*vec_from_deg(theta, phi))
        LIBRC.SDsampBSDF(byref(value), vout, randx, SFLAGS[sflag.lower()], self.sd)
        return value


def read_rad(*paths: str):
    """
    Read Radiance files and return a list of Primitives.
    Args:
        paths: A list of paths to Radiance files.
    Returns:
        A list of Primitives.
    """
    for path in paths:
        LIBRC.readobj(path.encode("ascii"))
    objblocks = (POINTER(OBJREC) * 131071).in_dll(LIBRC, "objblock")
    nobjects = c_int.in_dll(LIBRC, "nobjects").value
    primitives = []
    for i in range(nobjects):
        _obj = objblocks[i // 2048][i & 2047]
        if _obj.omod == -1:
            omod = "void"
        else:
            omod = objblocks[_obj.omod // 2048][_obj.omod & 2047].oname.decode()
        sargs = []
        fargs = []
        if _obj.oargs.nsargs > 0:
            sargs = [
                _obj.oargs.sarg[i].decode("ascii") for i in range(_obj.oargs.nsargs)
            ]
        if _obj.oargs.nfargs > 0:
            fargs = [_obj.oargs.farg[i] for i in range(_obj.oargs.nfargs)]
        primitives.append(
            Primitive(omod, OTYPES[_obj.otype], _obj.oname.decode(), sargs, fargs)
        )
    LIBRC.freeobjects(0, nobjects)
    return primitives


def get_view_resolu(path) -> Tuple[View, Resolu]:
    """Get view and resolu from a view or hdr file
    Args:
        path: Path to view or hdr file
    Returns:
        A tuple of View and Resolu
    """
    _view = VIEW()
    _res = RESOLU()
    LIBRC.viewfile(path.encode(), byref(_view), byref(_res))
    view = View(
        position=(_view.vp[0], _view.vp[1], _view.vp[2]),
        direction=(_view.vdir[0], _view.vdir[1], _view.vdir[2]),
        vtype=_view.type.decode(),
        vup=(_view.vup[0], _view.vup[1], _view.vup[2]),
        horiz=_view.horiz,
        vert=_view.vert,
        hoff=_view.hoff,
        voff=_view.voff,
        vfore=_view.vfore,
        vaft=_view.vaft,
        vdist=_view.vdist,
    )
    resolu = Resolu(ORIENT_FLAG[_res.rp], _res.xr, _res.yr)
    return view, resolu
