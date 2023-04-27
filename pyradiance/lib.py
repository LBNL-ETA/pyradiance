"""
Routines for calling Radiance C functions
"""

from ctypes import (
    CDLL,
    c_char,
    c_char_p,
    c_double,
    c_float,
    c_int,
    c_long,
    c_short,
    c_size_t,
    c_void_p,
    Structure,
    POINTER,
    byref,
)
from math import radians, sin, cos
import os
from random import randint
import tempfile
from typing import List, Optional, Tuple

from .model import Primitive, View, Resolu


# C def
_FVect = c_double * 3
_C_CNSS = 41  # number of spectral samples
_Color = c_float * 3
_Object = c_int
_Mat4 = c_double * 4 * 4
_RNumber = c_size_t
_SDmaxCh = 3  # max number of channels
_SdnameLn = 128  # max BSDF name length

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

# bsdf_m.h
MAXLATS = 46
MAXBASES = 7


class _Lat(Structure):
    _fields_ = [
        ("tmin", c_float),
        ("nphis", c_int),
    ]


class _AngleBasis(Structure):
    _fields_ = [
        ("name", c_char * 64),
        ("nangles", c_int),
        ("lat", _Lat * (MAXLATS + 1)),
    ]


class _C_Color(Structure):
    _fields_ = [
        ("clock", c_double),
        ("client_data", c_void_p),
        ("flags", c_short),
        ("ssamp", c_short * _C_CNSS),
        ("ssum", c_long),
        ("cx", c_float),
        ("cy", c_float),
        ("eff", c_float),
    ]


class _Resolu(Structure):
    _fields_ = [
        ("rp", c_int),
        ("xr", c_int),
        ("yr", c_int),
    ]


class _FunArgs(Structure):
    _fields_ = [
        ("sarg", POINTER(c_char_p)),
        ("farg", POINTER(c_double)),
        ("nsargs", c_short),
        ("nfargs", c_short),
    ]


class _ObjRec(Structure):
    _fields_ = [
        ("omod", c_int),
        ("otype", c_short),
        ("oname", c_char_p),
        ("oargs", _FunArgs),
        ("os", c_char_p),
    ]


class _Xf(Structure):
    _fields_ = [
        ("xfm", _Mat4),
        ("sca", c_double),
    ]


class _FullXf(Structure):
    _fields_ = [
        ("f", _Xf),
        ("b", _Xf),
    ]


class _Ray(Structure): pass
_Ray._fields_ = [
        ("rorg", _FVect),
        ("rdir", _FVect),
        ("rmax", c_double),
        ("rot", c_double),
        ("rop", _FVect),
        ("ron", _FVect),
        ("rod", c_double),
        ("uv", c_double * 2),
        ("pert", _FVect),
        ("rmt", c_double),
        ("rxt", c_double),
        ("parent", POINTER(_Ray)),
        ("clipset", POINTER(_Object)),
        ("newcset", POINTER(_Object)),
        ("revf", c_void_p),
        ("hitf", c_void_p),
        ("ro", POINTER(_ObjRec)),
        ("rox", POINTER(_FullXf)),
        ("slights", POINTER(c_int)),
        ("rno", _RNumber),
        ("robj", _Object),
        ("rsrc", c_int),
        ("rweight", c_float),
        ("gecc", c_float),
        ("rcoef", _Color),
        ("pcol", _Color),
        ("mcol", _Color),
        ("rcol", _Color),
        ("cext", _Color),
        ("albedo", _Color),
        ("rflips", c_short),
        ("rlvl", c_short),
        ("rtype", c_short),
        ("crtype", c_short),
    ]


class _View(Structure):
    _fields_ = [
        ("type", c_char),
        ("vp", _FVect),
        ("vdir", _FVect),
        ("vup", _FVect),
        ("vdist", c_double),
        ("horiz", c_double),
        ("vert", c_double),
        ("hoff", c_double),
        ("voff", c_double),
        ("vfore", c_double),
        ("vaft", c_double),
        ("hvec", _FVect),
        ("vvec", _FVect),
        ("hn2", c_double),
        ("vn2", c_double),
    ]


class _SDValue(Structure):
    _fields_ = [
        ("cieY", c_double),
        ("spec", _C_Color),
    ]


class _SDCDst(Structure):
    _fields_ = [
        ("SD_CDIST_BASE", c_void_p),
    ]


class _SDFunc(Structure):
    _fields_ = [
        ("getBSDFs", POINTER(c_int)),
        ("queryProjSA", POINTER(c_int)),
        ("getCDist", POINTER(_SDCDst)),
        ("sampCDist", POINTER(c_int)),
        ("freeSC", c_void_p),
    ]


class _SDComponent(Structure):
    _fields_ = [
        ("cspec", _C_Color * _SDmaxCh),
        ("func", POINTER(_SDFunc)),
        ("dist", c_void_p),
        ("cdList", POINTER(_SDCDst)),
    ]


class _SDSpectralDF(Structure):
    _fields_ = [
        ("minProjSA", c_double),
        ("maxHemi", c_double),
        ("ncomp", c_int),
        ("comp", _SDComponent * 1),
    ]


class _SDData(Structure):
    _fields_ = [
        ("name", c_char * _SdnameLn),
        ("matn", c_char * _SdnameLn),
        ("makr", c_char * _SdnameLn),
        ("mgf", c_char_p),
        ("dim", c_double * 3),
        ("rLambFront", _SDValue),
        ("rLambBack", _SDValue),
        ("tLambFront", _SDValue),
        ("tLambBack", _SDValue),
        ("rf", POINTER(_SDSpectralDF)),
        ("rb", POINTER(_SDSpectralDF)),
        ("tf", POINTER(_SDSpectralDF)),
        ("tb", POINTER(_SDSpectralDF)),
    ]


LIBRC = CDLL(os.path.join(os.path.dirname(__file__), "libraycalls.so"))
LIBRC.SDcacheFile.argtypes = [c_char_p]
LIBRC.SDcacheFile.restype = POINTER(_SDData)
LIBRC.SDfreeCache.argtypes = [POINTER(_SDData)]
LIBRC.SDfreeCache.restype = None
LIBRC.SDsizeBSDF.argtypes = [
    POINTER(c_double),
    _FVect,
    POINTER(c_double),
    c_int,
    POINTER(_SDData),
]
LIBRC.SDsizeBSDF.restype = c_int
LIBRC.SDevalBSDF.argtypes = [POINTER(_SDValue), _FVect, _FVect, POINTER(_SDData)]
LIBRC.SDevalBSDF.restype = c_int
LIBRC.SDdirectHemi.argtypes = [_FVect, c_int, POINTER(_SDData)]
LIBRC.SDdirectHemi.restype = c_double
LIBRC.SDsampBSDF.argtypes = [
    POINTER(_SDValue),
    _FVect,
    c_double,
    c_int,
    POINTER(_SDData),
]
LIBRC.SDsampBSDF.restype = c_int
LIBRC.readobj.argtypes = [c_char_p]
LIBRC.readobj.restype = POINTER(_ObjRec)
LIBRC.freeobjects.argtypes = [c_int, c_int]
LIBRC.freeobjects.restype = None
LIBRC.viewfile.argtypes = [c_char_p, POINTER(_View), POINTER(_Resolu)]
LIBRC.viewfile.restype = None
LIBRC.c_ccvt.argtypes = [POINTER(_C_Color), c_short]
LIBRC.c_ccvt.restype = None
LIBRC.c_sset.argtypes = [POINTER(_C_Color), c_double, c_double, POINTER(c_float), c_int]
LIBRC.c_sset.restype = c_double
LIBRC.cie_rgb.argtypes = [_Color, _Color]
LIBRC.cie_rgb.restype = None


ABASELIST = (_AngleBasis * MAXBASES).in_dll(LIBRC, "abase_list")


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

    @property
    def info(self):
        """Report general information about the BSDF"""
        _info = [
            f"Materials: {self.sd.contents.matn.decode()}",
            f"Manufacturer: {self.sd.contents.makr.decode()}",
            f"Width x Height x Thickness (m): {self.sd.contents.dim[0]} x {self.sd.contents.dim[1]} x {self.sd.contents.dim[2]}",
        ]
        if self.sd.contents.mgf:
            _info.append(f"Has geometry: {len(self.sd.contents.mgf)}")
        else:
            _info.append("Has geometry: no")
        return "\n".join(_info)

    @property
    def components(self):
        """Report diffuse and specular components."""
        _out = []
        if self.sd.contents.rf:
            _out.append(
                f"Peak front hemispherical reflectance: {self.sd.contents.rLambFront.cieY + self.sd.contents.rf.contents.maxHemi}"
            )
        if self.sd.contents.rb:
            _out.append(
                f"Peak back hemispherical reflectance: {self.sd.contents.rLambBack.cieY + self.sd.contents.rb.contents.maxHemi}"
            )
        if self.sd.contents.tf:
            _out.append(
                f"Peak front hemispherical transmittance: {self.sd.contents.tLambFront.cieY + self.sd.contents.tf.contents.maxHemi}"
            )
        if self.sd.contents.tb:
            _out.append(
                f"Peak back hemispherical transmittance: {self.sd.contents.tLambBack.cieY + self.sd.contents.tb.contents.maxHemi}"
            )
        _out.append(
            f"Diffuse front reflectance: {self._sdvalue_to_xyz(self.sd.contents.rLambFront)}"
        )
        _out.append(
            f"Diffuse back reflectance: {self._sdvalue_to_xyz(self.sd.contents.rLambBack)}"
        )
        _out.append(
            f"Diffuse front transmittance: {self._sdvalue_to_xyz(self.sd.contents.tLambFront)}"
        )
        _out.append(
            f"Diffuse back transmittance: {self._sdvalue_to_xyz(self.sd.contents.tLambBack)}"
        )
        return "\n".join(_out)

    def size(
        self,
        theta: float,
        phi: float,
        qflags: str = "min_max",
        t2: Optional[float] = None,
        p2: Optional[float] = None,
    ) -> Tuple[float, float]:
        """Get resolution (in proj. steradians) for given direction(s)
        Args:
            theta: zenith angle (degrees)
            phi: azimuth angle (degrees)
            qflags: query flags (min_max, min, max, avg)
            t2: second zenith angle (degrees)
            p2: second azimuth angle (degrees)
        Returns:
            resolution(s) (in proj. steradians)
        Examples:
            >>> pr.BSDF("bsdf.xml").size(0, 0)
            0.0001, 0.0001
        """
        proj_sa = (c_double * 2)(0, 0)
        v1 = (c_double * 3)(*vec_from_deg(theta, phi))
        v2 = None
        if (t2 is not None) and (p2 is not None):
            v2 = (c_double * 3)(*vec_from_deg(t2, p2))
            v1, v2 = v2, v1
        LIBRC.SDsizeBSDF(proj_sa, v1, v2, QFLAGS[qflags], self.sd)
        return proj_sa[0], proj_sa[1]

    def _sdvalue_to_xyz(self, vp) -> Tuple[float, float, float]:
        if vp.cieY <= 1e-9:
            return (0, 0, 0)
        return (
            vp.spec.cx / vp.spec.cy * vp.cieY,
            vp.cieY,
            (1 - vp.spec.cx - vp.spec.cy) / vp.spec.cy * vp.cieY,
        )

    def eval(
        self, itheta: float, iphi: float, otheta: float, ophi: float
    ) -> Tuple[float, float, float]:
        """Query BSDF for given path.
        Args:
            itheta: incident zenith angle (degrees)
            iphi: incident azimuth angle (degrees)
            otheta: outgoing zenith angle (degrees)
            ophi: outgoing azimuth angle (degrees)
        Returns:
            BSDF color in XYZ
        Examples:
            >>> import pyradiance as pr
            >>> pr.BSDF("bsdf.xml").eval(0, 0, 180, 0)
            2.3, 2.3, 2.3
        """
        value = _SDValue()
        in_vec = (c_double * 3)(*vec_from_deg(itheta, iphi))
        out_vec = (c_double * 3)(*vec_from_deg(otheta, ophi))
        LIBRC.SDevalBSDF(byref(value), in_vec, out_vec, self.sd)
        return self._sdvalue_to_xyz(value)

    def direct_hemi(self, theta: float, phi: float, sflag: str) -> float:
        """Get hemispherical integral of BSDF.
        Args:
            theta: zenith angle (degrees)
            phi: azimuth angle (degrees)
            sflag: sampling flag (t, ts, td, r, rs, rd, s)
        Returns:
            hemispherical value
        Examples:
            >>> import pyradiance as pr
            >>> pr.BSDF("bsdf.xml").direct_hemi(0, 0, "t")
            0.01
        """
        in_vec = (c_double * 3)(*vec_from_deg(theta, phi))
        return LIBRC.SDdirectHemi(in_vec, SFLAGS[sflag.lower()], self.sd)

    def sample(
        self, theta: float, phi: float, randx: float, sflag: str
    ) -> Tuple[List[float], Tuple[float, float, float]]:
        """Sample BSDF for given direction.
        Args:
            theta: zenith angle (degrees)
            phi: azimuth angle (degrees)
            randx: random variable [0-1)
            sflag: sampling flag (t, ts, td, r, rs, rd, s)
        Returns:
            Outgoing sample direction and color in XYZ.
        Examples:
            >>> pr.BSDF("bsdf.xml").sample(0, 0, 0.5, "r")
            [0.0, 0.0, 1.0], (0.1, 0.1, 0.1)
        """
        value = _SDValue()
        vout = (c_double * 3)(*vec_from_deg(theta, phi))
        LIBRC.SDsampBSDF(byref(value), vout, randx, SFLAGS[sflag.lower()], self.sd)
        return vout[:], self._sdvalue_to_xyz(value)

    def samples(
        self, theta: float, phi: float, nsamp: int, sflag: str
    ) -> Tuple[List[List[float]], List[Tuple[float, float, float]]]:
        """
        Generate samples for a given incident direction.
        Args:
            theta: incident theta angle (degrees)
            phi: incident phi angle (degrees)
            nsamp: number of samples
            sflag: sampling flag {t | ts | td | r | rs | rd | s}
        Returns:
            Outgoing sample directions and colors in XYZ.
        Examples:
            >>> pr.BSDF("bsdf.xml").samples(0, 0, 10, "r")
            [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0], ...], [(0.1, 0.1, 0.1), (0.1, 0.1, 0.1), ...]
        """
        rand_max = 0x7FFFFFFF
        vin = (c_double * 3)(*vec_from_deg(theta, phi))
        vout = (c_double * 3)(0, 0, 0)
        vecs = []
        values = []
        for i in range(nsamp, 0, -1):
            vout[0], vout[1], vout[2] = vin[0], vin[1], vin[2]
            value = _SDValue()
            randx = ((i - 1) + randint(0, rand_max) * (1 / (rand_max + 0.5))) / nsamp
            LIBRC.SDsampBSDF(byref(value), vout, randx, SFLAGS[sflag.lower()], self.sd)
            vecs.append(vout[:])
            values.append(self._sdvalue_to_xyz(value))
        return vecs, values


def read_rad(*paths: str, inbytes=None):
    """
    Read Radiance files and return a list of Primitives. Files order matters.
    Args:
        paths: A list of paths to Radiance files.
    Returns:
        A list of Primitives.
    Examples:
        >>> pr.read_rad("scene.rad")
    """

    if inbytes is None:
        for path in paths:
            LIBRC.readobj(path.encode("ascii"))
    else:
        # slow
        with tempfile.NamedTemporaryFile() as f:
            f.write(inbytes)
            f.flush()
            LIBRC.readobj(f.name.encode("ascii"))
    objblocks = (POINTER(_ObjRec) * 131071).in_dll(LIBRC, "objblock")
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
    Examples:
        >>> pr.get_view_resolu("view.vf")
    """
    _view = _View()
    _res = _Resolu()
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
        hvec=(_view.hvec[0], _view.hvec[1], _view.hvec[2]),
        vvec=(_view.vvec[0], _view.vvec[1], _view.vvec[2]),
        hn2=_view.hn2,
        vn2=_view.vn2,
    )
    resolu = Resolu(ORIENT_FLAG[_res.rp], _res.xr, _res.yr)
    return view, resolu


def spec_xyz(spec: List[float], wlmin: float, wlmax: float) -> Tuple[float, float, float]:
    """Convert a spectrum into CIE XYZ.
    Args:
        spec: A list of spectral values, must be equally spaced in wavelength.
        wlmin: The minimum wavelength in nm.
        wlmax: The maximum wavelength in nm.
    Returns:
        A tuple of X, Y, Z values.
    """
    c = _C_Color()
    nwvl = len(spec)
    ssamp = (c_float * nwvl)(*spec)
    cie_y = LIBRC.c_sset(byref(c), wlmin, wlmax, ssamp, nwvl)
    LIBRC.c_ccvt(byref(c), 4)
    d = c.cx / c.cy
    cie_x = d * cie_y
    cie_z = (1 / c.cy - 1 - d) * cie_y
    return cie_x, cie_y, cie_z


def xyz_rgb(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Convert CIE XYZ to RGB (Radiance).
    Args:
        x: X value.
        y: Y value.
        z: Z value.
    Returns:
        A tuple of R, G, B values.
    """
    rgb = (c_float * 3)()
    xyz = (c_float * 3)(x, y, z)
    LIBRC.cie_rgb(rgb, xyz)
    return rgb[0], rgb[1], rgb[2]
