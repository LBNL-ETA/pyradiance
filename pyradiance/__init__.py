"""
# Python interface for Radiance

pyradiance is a Python interface for Radiance. It is a collection of Python
modules that provide a high level interface to Radiance. It is designed to
make Radiance easier to use and accessible to Python user.

"""


import logging
import os

from .api import (
    build_scene,
    gen_perez_sky,
    get_header,
    get_image_dimensions,
    gendaymtx,
    gensky,
    genwea,
    obj2rad,
    oconv,
    rmtxop,
    pvalue,
    pvaluer,
    pcond,
    pfilt,
    render,
    rpict,
    rtrace,
)

from .data import model_cubical_office

from .model import Sensor, Scene, View, Primitive

from .parameter import SamplingParameters

from .parsers import parse_view_file, parse_primitive

logging.getLogger(__name__).addHandler(logging.NullHandler())

os.environ["RAYPATH"] = os.path.join(os.path.dirname(__file__), "lib")

__all__ = [
    "model_cubical_office",
    "build_scene",
    "gen_perez_sky",
    "gendaymtx",
    "gensky",
    "genwea",
    "get_header",
    "get_image_dimensions",
    "obj2rad",
    "oconv",
    "pvalue",
    "pvaluer",
    "pcond",
    "pfilt",
    "render",
    "rmtxop",
    "rpict",
    "rtrace",
    "Scene",
    "Sensor",
    "View",
    "Primitive",
    "SamplingParameters",
    "parse_view_file",
    "parse_primitive",
]
