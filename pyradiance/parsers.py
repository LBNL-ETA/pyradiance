"""
This module contains all data parsing routines.
"""
import argparse
import re
from pathlib import Path
import subprocess as sp
from typing import List

from .model import View, Primitive


BIN_PATH = Path(__file__).parent / "bin"


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


def parse_rtrace_args(options: str) -> dict:
    """Add rtrace options and flags to a parser."""
    parser = argparse.ArgumentParser(add_help=False)
    parser = add_ambient_args(parser)
    parser = add_direct_args(parser)
    parser = add_mist_args(parser)
    parser = add_limit_args(parser)
    parser = add_specular_args(parser)
    parser = add_toggle_args(parser)
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


def parse_rad_header(header_str: str) -> tuple:
    """Parse a Radiance matrix file header.

    Args:
        header_str(str): header as string
    Returns:
        A tuple contain nrow, ncol, ncomp, datatype
    Raises:
        ValueError if any of NROWs NCOLS NCOMP FORMAT is not found.
        (This is problematic as it can happen)
    """
    compiled = re.compile(
        r" NROWS=(.*) | NCOLS=(.*) | NCOMP=(.*) | FORMAT=(.*) ", flags=re.X
    )
    matches = compiled.findall(header_str)
    if len(matches) != 4:
        raise ValueError("Can't find one of the header entries.")
    nrow = int([mat[0] for mat in matches if mat[0] != ""][0])
    ncol = int([mat[1] for mat in matches if mat[1] != ""][0])
    ncomp = int([mat[2] for mat in matches if mat[2] != ""][0])
    dtype = [mat[3] for mat in matches if mat[3] != ""][0].strip()
    return nrow, ncol, ncomp, dtype


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
