"""
pyradiance.model
================

This module defines model data structure.
"""

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Dict, List, Sequence, Tuple, Union


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
    strarg: Sequence[str]
    realarg: Sequence[float]

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


@dataclass(eq=True, frozen=True)
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


@dataclass(eq=True, frozen=True)
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
        self.materials: Dict[str, str] = {}
        self.surfaces: Dict[str, str] = {}
        self.views: List[View] = []
        self.sensors: List[Sequence[float]] = []
        self.sources: Dict[str, str] = {}
        self.changed = True
        self.windows: Dict[str, str] = {}

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

    def add_sensor(self, sensor: Sequence[float]):
        self.sensors.append(sensor)


def parse_primitive(pstr) -> List[Primitive]:
    """Parse Radiance primitives inside a file path into a list of dictionary.
    Args:
        pstr: A string of Radiance primitives.

    Returns:
        list of primitives
    """
    res = []
    tokens = re.sub(r"#.+?\n", "", pstr).strip().split()
    itokens = iter(tokens)
    for t in itokens:
        modifier, ptype, identifier = t, next(itokens), next(itokens)
        nsarg = next(itokens)
        sarg = [next(itokens) for _ in range(int(nsarg))]
        next(itokens)
        nrarg = next(itokens)
        rarg = [float(next(itokens)) for _ in range(int(nrarg))]
        res.append(Primitive(modifier, ptype, identifier, sarg, rarg))
    return res


def parse_view(vstr: str) -> View:
    """Parse view string into a View object.

    Args:
        vstr: view parameters as a string

    Returns:
        A View object
    """
    args_list = vstr.strip().split()
    vparser = argparse.ArgumentParser()
    vparser.add_argument("-v", action="store", dest="vt")
    vparser.add_argument("-vp", nargs=3, type=float, default=(0, 0, 0))
    vparser.add_argument("-vd", nargs=3, type=float, default=(0, 1, 0))
    vparser.add_argument("-vu", nargs=3, type=float, default=(0, 0, 1))
    vparser.add_argument("-vv", type=float, default=45)
    vparser.add_argument("-vh", type=float, default=45)
    vparser.add_argument("-vo", type=float, default=0)
    vparser.add_argument("-va", type=float, default=0)
    vparser.add_argument("-vs", type=float, default=0)
    vparser.add_argument("-vl", type=float, default=0)
    vparser.add_argument("-vf", type=argparse.FileType("r"))
    args, _ = vparser.parse_known_args(args_list)
    if args.vf is not None:
        args, _ = vparser.parse_known_args(
            args.vf.readline().strip().split(), namespace=args
        )
        args.vf.close()
    return View(
        position=args.vp,
        direction=args.vd,
        vtype=args.vt[-1],
        horiz=args.vh,
        vert=args.vv,
        vfore=args.vo,
        vaft=args.va,
        hoff=args.vs,
        voff=args.vl,
    )


def load_views(file: Union[str, Path]) -> List[View]:
    """Load views from a file.
    One view per line.

    Args:
        file: A file path to a view file.

    Returns:
        A view object.
    """
    with open(file) as f:
        lines = f.readlines()
    return [parse_view(line) for line in lines]
