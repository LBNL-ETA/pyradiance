"""
pyradiance.parameter
====================
This module contains functions for generating simulation
parameters for running radiance
"""

import argparse
from pathlib import Path
from typing import NamedTuple


class Levels:
    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"


class ColorPrimaries(NamedTuple):
    xr: float
    yr: float
    xg: float
    yg: float
    xb: float
    yb: float
    xw: float
    yw: float


class IntArg:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, type=None) -> object:
        return obj.__dict__.get(self.name)

    def __set__(self, obj, value) -> None:
        if not isinstance(value, int):
            raise ValueError("ab has to be an integer")
        self.value = value
        obj.__dict__[self.name] = value


class FloatArg:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, type=None) -> object:
        return obj.__dict__.get(self.name)

    def __set__(self, obj, value) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError("Value has to be a int or float")
        self.value = value
        obj.__dict__[self.name] = value


class Tuple3Arg:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, type=None) -> object:
        return obj.__dict__.get(self.name)

    def __set__(self, obj, value) -> None:
        if not isinstance(value, tuple):
            raise ValueError(f"{self.name} has to be a tuple")
        if not all(isinstance(i, (int, float)) for i in value):
            raise ValueError(f"{self.name} inside has to be a integer or float")
        if len(value) != 3:
            raise ValueError(f"{self.name} has to be a tuple of length 3")
        self.value = value
        obj.__dict__[self.name] = value


class PathArg:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, type=None) -> object:
        return obj.__dict__.get(self.name)

    def __set__(self, obj, value) -> None:
        if not isinstance(value, (str, Path)):
            raise ValueError(f"{self.name} has to be a string or Path")
        # if not Path(value).exists():
        # raise ValueError(f"{self.name} does not exist")
        self.value = value
        obj.__dict__[self.name] = value


class SamplingParameters:
    aa = FloatArg()
    ab = IntArg()
    ad = IntArg()
    ar = IntArg()
    as_ = IntArg()
    av = Tuple3Arg()
    aw = IntArg()
    af = PathArg()
    dc = FloatArg()
    dj = FloatArg()
    dr = IntArg()
    dp = IntArg()
    ds = FloatArg()
    dt = FloatArg()
    lr = IntArg()
    lw = FloatArg()
    ms = FloatArg()
    pa = FloatArg()
    pj = FloatArg()
    ps = IntArg()
    pt = FloatArg()
    ss = FloatArg()
    st = FloatArg()

    def args(self):
        arglist = []
        for key, value in self.__dict__.items():
            if value is None:
                continue
            elif isinstance(value, tuple):
                arglist.extend([f"-{key}", *map(str, value)])
            elif key == "as_":
                arglist.extend(["-as", str(value)])
            else:
                arglist.extend([f"-{key}", str(value)])
        return arglist

    def update_key(self, key, val):
        if key == "av":
            if isinstance(val, str):
                val = tuple(map(float, val.strip().split(" ")))
            elif isinstance(val, list):
                val = tuple(val)
        elif key == "af":
            val = Path(val.strip())
        elif key in ("ab", "ad", "ar", "as", "aw", "dr", "dp", "lr", "ps"):
            val = int(val)
        elif key == "as":
            key += "_"
        else:
            val = float(val)
        setattr(self, key, val)

    def update_from_file(self, path: str):
        with open(path, "r") as rdr:
            params = rdr.readlines()
        for param in params:
            key, val = param[1:].split(" ", 1)
            self.update_key(key, val)

    def update_from_dict(self, params: dict):
        [self.update_key(key, value) for key, value in params.items()]

    def update(self, sp):
        if not isinstance(sp, SamplingParameters):
            raise ValueError("sp has to be a SamplingParameters")
        for key, value in sp.__dict__.items():
            if value is None:
                continue
            setattr(self, key, value)


def add_ambient_args(parser):
    parser.add_argument("-aa", type=float, metavar="", default=None)
    parser.add_argument("-ab", type=int, metavar="", default=None)
    parser.add_argument("-ad", type=int, metavar="", default=None)
    parser.add_argument("-af", type=str, metavar="", default=None)
    parser.add_argument("-am", type=int, metavar="", default=None)
    parser.add_argument("-ar", type=int, metavar="", default=None)
    parser.add_argument("-as", type=int, metavar="", default=None)
    parser.add_argument("-av", type=float, nargs=3, metavar="", default=None)
    parser.add_argument("-aw", type=int, metavar="", default=None)
    return parser


def add_direct_args(parser):
    parser.add_argument("-dc", type=float, metavar="", default=None)
    parser.add_argument("-dj", type=float, metavar="", default=None)
    parser.add_argument("-dp", type=int, metavar="", default=None)
    parser.add_argument("-dr", type=int, metavar="", default=None)
    parser.add_argument("-ds", type=float, metavar="", default=None)
    parser.add_argument("-dt", type=float, metavar="", default=None)
    return parser


def add_specular_args(parser):
    parser.add_argument("-ss", type=float, metavar="", default=None)
    parser.add_argument("-st", type=float, metavar="", default=None)
    return parser


def add_pixel_args(parser):
    parser.add_argument("-pa", type=int, metavar="", default=None)
    parser.add_argument("-pj", type=float, metavar="", default=None)
    parser.add_argument("-pm", type=int, metavar="", default=None)
    parser.add_argument("-pd", type=float, metavar="", default=None)
    parser.add_argument("-ps", type=int, metavar="", default=None)
    parser.add_argument("-pt", type=float, metavar="", default=None)
    return parser


def add_toggle_args(parser):
    parser.add_argument("-I", action="store_true", dest="I", default=None)
    parser.add_argument("-I+", action="store_true", dest="I", default=None)
    parser.add_argument("-I-", action="store_false", dest="I", default=None)
    parser.add_argument("-i", action="store_true", dest="i", default=None)
    parser.add_argument("-i+", action="store_true", dest="i", default=None)
    parser.add_argument("-i-", action="store_false", dest="i", default=None)
    parser.add_argument("-V", action="store_true", dest="V", default=None)
    parser.add_argument("-V+", action="store_true", dest="V", default=None)
    parser.add_argument("-V-", action="store_false", dest="V", default=None)
    parser.add_argument("-u", action="store_true", dest="u", default=None)
    parser.add_argument("-u+", action="store_true", dest="u", default=None)
    parser.add_argument("-u-", action="store_false", dest="u", default=None)
    parser.add_argument("-ld-", action="store_false", dest="ld", default=None)
    parser.add_argument("-w", action="store_false", dest="w", default=None)
    parser.add_argument("-w-", action="store_false", dest="w", default=None)
    parser.add_argument("-w+", action="store_true", dest="w", default=None)
    parser.add_argument("-bv", action="store_true", dest="bv", default=None)
    parser.add_argument("-bv-", action="store_false", dest="bv", default=None)
    parser.add_argument("-bv+", action="store_true", dest="bv", default=None)
    parser.add_argument("-dv", action="store_true", dest="dv", default=None)
    parser.add_argument("-dv-", action="store_false", dest="dv", default=None)
    parser.add_argument("-dv+", action="store_true", dest="dv", default=None)
    return parser


def add_limit_args(parser):
    parser.add_argument("-ld", type=float, default=None)
    parser.add_argument("-lr", type=int, default=None)
    parser.add_argument("-lw", type=float, default=None)
    return parser


def add_mist_args(parser):
    parser.add_argument("-me", type=float, nargs=3, default=None)
    parser.add_argument("-ma", type=float, nargs=3, default=None)
    parser.add_argument("-mg", type=float, default=None)
    parser.add_argument("-ms", type=float, default=None)
    return parser

def add_view_args(parser):
    parser.add_argument("-v", action="store", dest="vt")
    parser.add_argument("-vp", nargs=3, type=float, default=(0, 0, 0))
    parser.add_argument("-vd", nargs=3, type=float, default=(0, 1, 0))
    parser.add_argument("-vu", nargs=3, type=float, default=(0, 0, 1))
    parser.add_argument("-vv", type=float, default=45)
    parser.add_argument("-vh", type=float, default=45)
    parser.add_argument("-vo", type=float, default=0)
    parser.add_argument("-va", type=float, default=0)
    parser.add_argument("-vs", type=float, default=0)
    parser.add_argument("-vl", type=float, default=0)
    parser.add_argument("-vf", type=argparse.FileType("r"))
    return parser


def parse_rpict_args(options: str) -> dict:
    """Parse rpict options."""
    parser = argparse.ArgumentParser(add_help=False)
    parser = add_pixel_args(parser)
    parser = add_ambient_args(parser)
    parser = add_direct_args(parser)
    parser = add_mist_args(parser)
    parser = add_limit_args(parser)
    parser = add_specular_args(parser)
    parser = add_toggle_args(parser)
    parser.add_argument("-t", type=float, help="time between reports")
    args, _ = parser.parse_known_args(options.strip().split())
    odict = {k: v for k, v in vars(args).items() if v is not None}
    return odict


def add_rtrace_args(parser):
    parser = add_ambient_args(parser)
    parser = add_direct_args(parser)
    parser = add_mist_args(parser)
    parser = add_limit_args(parser)
    parser = add_specular_args(parser)
    parser = add_toggle_args(parser)
    return parser


def add_rcontrib_args(parser):
    parser = add_rtrace_args(parser)
    parser.add_argument("-c", type=int) 
    return parser


def parse_rtrace_args(options: str) -> dict:
    """Add rtrace options and flags to a parser."""
    parser = argparse.ArgumentParser(add_help=False)
    parser = add_rtrace_args(parser)
    args, _ = parser.parse_known_args(options.strip().split())
    odict = {k: v for k, v in vars(args).items() if v is not None}
    return odict


def parse_rcontrib_args(options: str) -> dict:
    """Add rtrace options and flags to a parser."""
    parser = argparse.ArgumentParser(add_help=False)
    parser = add_rcontrib_args(parser)
    args, _ = parser.parse_known_args(options.strip().split())
    odict = {k: v for k, v in vars(args).items() if v is not None}
    return odict


def parse_sim_args(options: str) -> dict:
    parser = argparse.ArgumentParser(add_help=False)
    parser = add_ambient_args(parser)
    parser = add_direct_args(parser)
    parser = add_mist_args(parser)
    parser = add_limit_args(parser)
    parser = add_specular_args(parser)
    parser = add_toggle_args(parser)
    parser = add_pixel_args(parser)
    parser.add_argument("-t", type=float, help="time between reports")
    args, _ = parser.parse_known_args(options.strip().split())
    odict = {k: v for k, v in vars(args).items() if v is not None}
    return odict
