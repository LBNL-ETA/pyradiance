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
        self.materials = {}
        self.surfaces = {}
        self.views = set()
        self.sensors = set()
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
        self.views.add(view)

    def add_sensor(self, sensor: List[float]):
        self.sensors.add(sensor)


def parse_view_file(fpath) -> List[View]:
    with open(fpath) as rdr:
        vu_lines = rdr.readlines()
    return [parse_vu(line) for line in vu_lines]


def parse_primitive(pstr) -> List[Primitive]:
    """Parse Radiance primitives inside a file path into a list of dictionary.
    Args:
        pstr: A string of Radiance primitives.

    Returns:
        list of primitives
    """
    res = []
    tokens = re.sub(r"#.+?\n", "", pstr).strip().split()
    tokens = iter(tokens)
    for t in tokens:
        modifier, ptype, identifier = t, next(tokens), next(tokens)
        nsarg = next(tokens)
        sarg = [next(tokens) for _ in range(int(nsarg))]
        next(tokens)
        nrarg = next(tokens)
        rarg = [float(next(tokens)) for _ in range(int(nrarg))]
        res.append(Primitive(modifier, ptype, identifier, sarg, rarg))
    return res


def parse_rad(fpath: str) -> List[Primitive]:
    """Parse a Radiance file.

    Args:
        fpath: Path to the .rad file

    Returns:
        A list of primitives
    """
    with open(fpath) as rdr:
        lines = rdr.readlines()
    if any((l.startswith("!") for l in lines)):
        lines = (
            sp.run([str(BIN_PATH / "xform"), fpath], stdout=sp.PIPE)
            .stdout.decode()
            .splitlines()
        )
    return parse_primitive("\n".join(lines))


def parse_vu(vu_str: str) -> View:
    """Parse view string into a View object.

    Args:
        vu_str: view parameters as a string

    Returns:
        A view object
    """

    args_list = vu_str.strip().split()
    vparser = argparse.ArgumentParser()
    vparser.add_argument("-v", action="store", dest="vt")
    vparser.add_argument("-vp", nargs=3, type=float)
    vparser.add_argument("-vd", nargs=3, type=float)
    vparser.add_argument("-vu", nargs=3, type=float)
    vparser.add_argument("-vv", type=float)
    vparser.add_argument("-vh", type=float)
    vparser.add_argument("-vo", type=float)
    vparser.add_argument("-va", type=float)
    vparser.add_argument("-vs", type=float)
    vparser.add_argument("-vl", type=float)
    # vparser.add_argument("-x", type=int)
    # vparser.add_argument("-y", type=int)
    vparser.add_argument("-vf", type=argparse.FileType("r"))
    args, _ = vparser.parse_known_args(args_list)
    if args.vf is not None:
        args, _ = vparser.parse_known_args(
            args.vf.readline().strip().split(), namespace=args
        )
        args.vf.close()
    if None in (args.vp, args.vd):
        raise ValueError("Invalid view")
    view = View(args.vp, args.vd)
    if args.vt is not None:
        view.vtype = args.vt[-1]
    # if args.x is not None:
    #     view.xres = args.x
    # if args.y is not None:
    #     view.yres = args.y
    if args.vv is not None:
        view.vert = args.vv
    if args.vh is not None:
        view.horiz = args.vh
    if args.vo is not None:
        view.vfore = args.vo
    if args.va is not None:
        view.vaft = args.va
    if args.vs is not None:
        view.hoff = args.vs
    if args.vl is not None:
        view.voff = args.vl
    return view
