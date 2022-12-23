"""
Radiance conversion routines.
"""

from pathlib import Path
import subprocess as sp
from typing import Optional


BINPATH = Path(__file__).parent / "bin"


def obj2rad(
    inp,
    quallist: bool = False,
    flatten: bool = False,
    mapfile: Optional[str] = None,
    objname: Optional[str] = None,
) -> bytes:
    """Convert a Wavefront .obj file to Radiance format."""
    stdin = None
    cmd = [str(BINPATH / "obj2rad")]
    if quallist:
        cmd.append("-n")
    elif flatten:
        cmd.append("-f")
    if objname is not None:
        cmd.extend(["-o", objname])
    if mapfile is not None:
        cmd.extend(["-m", mapfile])
    if isinstance(inp, bytes):
        stdin = inp
    else:
        cmd.append(str(inp))
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout
