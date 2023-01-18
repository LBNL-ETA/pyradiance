from ctypes import (
    CDLL,
    c_int,
    c_char_p,
    c_double,
    c_short,
    c_char,
    Structure,
    POINTER,
    byref,
)
import os
from typing import Tuple

from .model import Primitive, View, Resolu


FVECT = c_double * 3


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


class RadianceAPI(CDLL):
    def __init__(self):
        super().__init__(
            os.path.join(os.path.dirname(__file__), "libraycalls.so")
        )
        self.readobj.argtypes = [c_char_p]
        self.readobj.restype = POINTER(OBJREC)
        self.freeobjects.argtypes = [c_int, c_int]
        self.freeobjects.restype = None
        self.viewfile.argtypes = [c_char_p, POINTER(VIEW), POINTER(RESOLU)]
        self.viewfile.restype = None

    def read_rad(self, *paths: str):
        """Reads a Radiance scene file and returns a list of primitives.
        Args:
            paths: Path to .rad file.
        Returns:
            List of primitives.
        """
        for path in paths:
            self.readobj(path.encode("ascii"))
        objblocks = (POINTER(OBJREC) * 131071).in_dll(self, "objblock")
        nobjects = c_int.in_dll(self, "nobjects").value
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
        self.freeobjects(0, nobjects)
        return primitives

    def free_objects(self, firstobj, nobjects):
        self.freeobjects(firstobj, nobjects)

    def get_view_resolu(self, path) -> Tuple[View, Resolu]:
        """Get view and resolu from .hdr or .vf file
        Args:
            path: Path to .hdr or .vf file.
        Returns:
            View and Resolu.
        """
        _view = VIEW()
        _res = RESOLU()
        self.viewfile(path.encode(), byref(_view), byref(_res))
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
