"""
pyradiance.parameter
====================
This module contains functions for generating simulation
parameters for running radiance
"""

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
