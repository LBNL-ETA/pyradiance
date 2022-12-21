"""
pyradiance.model
================

This module defines model data structure.
"""

import os
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Primitive:
    """Radiance Primitive.

    Attributes one-to-one mapped from Radiance.

    Attributes:
        modifier: modifier, which primitive modifies this one
        ptype: primitive type
        identifier: identifier, name of this primitive
        str_arg: string argument
        real_arg: real argument
        int_arg: integer argument, not used in Radiance (default="0")
    """

    modifier: str
    ptype: str
    identifier: str
    strarg: List[str]
    realarg: List[float]

    def __repr__(self) -> str:
        output = (
            f"{self.modifier}, {self.ptype}, "
            f"{self.identifier}, {len(self.strarg)} {self.strarg}, "
            f"0, {len(self.realarg)} {self.realarg})"
        )
        return output

    def __str__(self) -> str:
        output = (
            f"{self.modifier} {self.ptype} {self.identifier}\n"
            f"{len(self.strarg)} {' '.join(self.strarg)}\n"
            "0\n"
            f"{len(self.realarg)} "
            f"{str(self.realarg)[1:-1].replace(',', '')}\n"
        )
        return output


class ViewType:
    VT_PER = "v"
    VT_PAR = "l"
    VT_ANG = "a"
    VT_HEM = "h"
    VT_PLS = "s"
    VT_CYL = "c"


@dataclass
class View:
    position: Tuple[float, float, float]
    direction: Tuple[float, float, float]
    vtype: str = ViewType.VT_PER
    vup: Tuple[float, float, float] = (0, 0, 1)
    horiz: float = 45
    vert: float = 45
    hoff: float = 0
    voff: float = 0
    vfore: float = 0
    vaft: float = 0

    def args(self):
        return [
            f"-vt{self.vtype}",
            "-vp",
            *[str(i) for i in self.position],
            "-vd",
            *[str(i) for i in self.direction],
            "-vu",
            *[str(i) for i in self.vup],
            "-vh",
            str(self.horiz),
            "-vv",
            str(self.vert),
            "-vo",
            str(self.vfore),
            "-va",
            str(self.vaft),
            "-vs",
            str(self.hoff),
            "-vl",
            str(self.voff),
        ]


@dataclass
class Sensor:
    position: Tuple[float, float, float]
    direction: Tuple[float, float, float]


class Scene:

    __slots__ = (
        "sid",
        "surfaces",
        "materials",
        "sources",
        "views",
        "sensors",
        "changed",
        "windows",
    )

    def __init__(self, sid: str):
        self.sid = sid
        self.materials = {}
        self.surfaces = {}
        self.views = []
        self.sensors = []
        self.sources = {}
        self.changed = True
        self.windows = {}

    def _add(self, obj, target):
        if isinstance(obj, Primitive):
            getattr(self, target)[obj.identifier] = obj
        elif isinstance(obj, (str, Path)):
            if not os.path.exists(obj):
                raise FileNotFoundError("File not found: ", obj)
            getattr(self, target)[obj] = str(obj)
        else:
            raise TypeError("Unsupported type: ", type(obj))
        self.changed = True

    def _remove(self, obj, target):
        if isinstance(obj, Primitive):
            del getattr(self, target)[obj.identifier]
        elif isinstance(obj, (str, Path)):
            del getattr(self, target)[obj]
        else:
            raise TypeError("Unsupported type: ", type(obj))
        self.changed = True

    def add_material(self, material):
        self._add(material, "materials")

    def remove_material(self, material):
        self._remove(material, "materials")

    def add_surface(self, surface):
        self._add(surface, "surfaces")

    def remove_surface(self, surface):
        self._remove(surface, "surfaces")

    def add_source(self, source):
        self._add(source, "sources")

    def remove_source(self, source):
        self._remove(source, "sources")

    def add_window(self, window):
        self._add(window, "windows")

    def remove_window(self, window):
        self._remove(window, "windows")

    def add_view(self, view):
        self.views.append(view)

    def add_sensor(self, sensor: List[float]):
        self.sensors.append(sensor)


@dataclass
class Modifier:
    """Modifier for rcontrib command.

    Args:
        modifier: Modifier name.
        value: Modifier value.
    """

    modifier = None
    modifier_path = None
    calfile = None
    expression = None
    nbins = None
    binv = None
    param = None
    xres = None
    yres = None
    output = None

    def args(self):
        """Return modifier as a list of arguments."""
        arglist = []
        if self.calfile is not None:
            arglist.extend(["-f", str(self.calfile)])
        if self.expression is not None:
            arglist.extend(["-e", str(self.expression)])
        if self.nbins is not None:
            arglist.extend(["-bn", str(self.nbins)])
        if self.binv is not None:
            arglist.extend(["-b", str(self.binv)])
        if self.param is not None:
            arglist.extend(["-p", str(self.param)])
        if self.xres is not None:
            arglist.extend(["-x", str(self.xres)])
        if self.yres is not None:
            arglist.extend(["-y", str(self.yres)])
        if self.output is not None:
            arglist.extend(["-o", str(self.output)])
        if self.modifier is not None:
            arglist.extend(["-m", self.modifier])
        elif self.modifier_path is not None:
            arglist.extend(["-M", self.modifier_path])
        else:
            raise ValueError("Modifier or modifier path must be provided.")
        return arglist
