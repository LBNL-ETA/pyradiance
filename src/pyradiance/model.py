"""
pyradiance.model
================

This module defines model data structure.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

from .ot import oconv


@dataclass
class Primitive:
    """Radiance Primitive.

    Attributes one-to-one mapped from Radiance.

    Attributes:
        modifier: modifier, which primitive modifies this one
        ptype: primitive type
        identifier: identifier, name of this primitive
        sargs: string arguments
        fargs: real arguments
    """

    modifier: str
    ptype: str
    identifier: str
    sargs: Sequence[str]
    fargs: Sequence[float]

    @property
    def bytes(self):
        out = f"{self.modifier} {self.ptype} {self.identifier} "
        if len(self.sargs) > 0:
            out += f"{len(self.sargs)} {' '.join(self.sargs)} "
        else:
            out += "0 "
        out += "0 "
        if len(self.fargs) > 0:
            out += f"{len(self.fargs)} {str(self.fargs)[1:-1].replace(',', '')} "
        else:
            out += "0 "
        return out.encode("utf-8")

    def __str__(self) -> str:
        return (
            f"{self.modifier} {self.ptype} {self.identifier}\n"
            f"{len(self.sargs)} {' '.join(self.sargs)}\n"
            "0\n"
            f"{len(self.fargs)} "
            f"{str(self.fargs)[1:-1].replace(',', '')}\n"
        )


class ViewType:
    VT_PER = "v"
    VT_PAR = "l"
    VT_ANG = "a"
    VT_HEM = "h"
    VT_PLS = "s"
    VT_CYL = "c"


@dataclass(eq=True)
class View:
    """Radiance View.

    Attributes:
        vtype: view type
        position: view position
        direction: view direction
        vup: view up
        horiz: horizontal field of view
        vert: vertical field of view
        vfore: view fore
        vaft: view aft
        hoff: horizontal offset
        voff: vertical offset
    """

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
    vdist: float = 0
    hvec: Tuple[float, float, float] = (0, 0, 0)
    vvec: Tuple[float, float, float] = (0, 0, 0)
    hn2: float = 0
    vn2: float = 0

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
class Resolu:
    """Radiance resolution.

    Attributes:
        orient: orientation
        xr: x resolution
        yr: y resolution
    """

    orient: str
    xr: int
    yr: int


@dataclass(eq=True, frozen=True)
class Sensor:
    position: Tuple[float, float, float]
    direction: Tuple[float, float, float]


class Scene:
    """Radiance Scene."""

    __slots__ = (
        "_sid",
        "_surfaces",
        "_materials",
        "_sources",
        "_views",
        "_sensors",
        "_changed",
        "_octree",
    )

    def __init__(self, sid: str, **kwargs):
        """
        Args:
            sid: scene id
        """
        if len(sid) < 0:
            raise ValueError("Scene id must be at least one character long")
        self._sid = sid
        self._octree = f"{sid}.oct"
        self._materials: Dict[str, str] = {}
        self._surfaces: Dict[str, str] = {}
        self._views: List[View] = []
        self._sensors: List[Sequence[float]] = []
        self._sources: Dict[str, str] = {}
        for key, vals in kwargs.items():
            for val in vals:
                self._add(val, key)
        self._changed = True

    @property
    def sid(self) -> str:
        """Scene id."""
        return self._sid

    @property
    def octree(self) -> str:
        """Scene id."""
        if self._changed:
            self._build()
        return self._octree

    @property
    def materials(self):
        """Scene materials."""
        return self._materials

    @property
    def surfaces(self):
        """Scene surfaces."""
        return self._surfaces

    @property
    def sources(self):
        """Scene sources."""
        return self._sources

    @property
    def views(self):
        return self._views

    @property
    def sensors(self):
        return self._sensors

    @property
    def changed(self):
        return self._changed

    def _add(self, obj, target):
        if isinstance(obj, Primitive):
            getattr(self, target)[obj.identifier] = obj
        elif isinstance(obj, (str, Path)):
            if not os.path.exists(obj):
                raise FileNotFoundError("File not found: ", obj)
            getattr(self, target)[obj] = str(obj)
        else:
            raise TypeError("Unsupported type: ", type(obj))
        self._changed = True

    def _remove(self, obj, target):
        if isinstance(obj, Primitive):
            del getattr(self, target)[obj.identifier]
        elif isinstance(obj, (str, Path)):
            del getattr(self, target)[obj]
        else:
            raise TypeError("Unsupported type: ", type(obj))
        self._changed = True

    def add_material(self, material: Union[str, Path, Primitive]):
        """Add material to the scene.
        Args:
            material: material to be added
        """
        self._add(material, "materials")

    def remove_material(self, material: Union[str, Path, Primitive]):
        """Remove material from the scene.
        Args:
            material: material to be removed
        """
        self._remove(material, "materials")

    def add_surface(self, surface: Union[str, Path, Primitive]):
        """Add surface to the scene.
        Args:
            surface: surface to be added
        """
        self._add(surface, "surfaces")

    def remove_surface(self, surface: Union[str, Path, Primitive]):
        """Remove surface from the scene.
        Args:
            surface: surface to be removed
        """
        self._remove(surface, "surfaces")

    def add_source(self, source: Union[str, Path, Primitive]):
        """Add source to the scene.
        Args:
            source: source to be added
        """
        self._add(source, "sources")

    def remove_source(self, source: Union[str, Path, Primitive]):
        """Remove source from the scene.
        Args:
            source: source to be removed
        """
        self._remove(source, "sources")

    def add_view(self, view: View):
        """Add view to the scene.
        Args:
            view: view to be added
        """
        self._views.append(view)

    def add_sensor(self, sensor: Sequence[float]):
        """Add sensor to the scene.
        Args:
            sensor: sensor to be added
        """
        if len(sensor) != 6:
            raise ValueError("Sensor must be a sequence of 6 numbers")
        self._sensors.append(sensor)

    def _build(self):
        stdin = None
        mstdin = [
            str(mat) for mat in self.materials.values() if isinstance(mat, Primitive)
        ]
        inp = [mat for mat in self.materials.values() if isinstance(mat, str)]
        if mstdin:
            stdin = "".join(mstdin).encode()
        moctname = f"{self.sid}mat.oct"
        with open(moctname, "wb") as wtr:
            wtr.write(oconv(*inp, warning=False, stdin=stdin))
        sstdin = [
            str(srf) for srf in self.surfaces.values() if isinstance(srf, Primitive)
        ]
        sstdin.extend(
            [str(src) for src in self.sources.values() if isinstance(src, Primitive)]
        )
        inp = [path for path in self.surfaces.values() if isinstance(path, str)]
        inp.extend([path for path in self.sources.values() if isinstance(path, str)])
        if sstdin:
            stdin = "".join(sstdin).encode()
        with open(f"{self.sid}.oct", "wb") as wtr:
            wtr.write(oconv(*inp, stdin=stdin, warning=False, octree=moctname))

    def build(self):
        """Build an octree, as {sid}.oct in the current directory.
        Will not build if scene has not changed since last build.
        """
        if self._changed:
            self._build()
            self._changed = False
