"""
Radiance scene compiler
"""

import subprocess as sp
from typing import List

from .anci import BINPATH, handle_called_process_error


@handle_called_process_error
def getbbox(
    *path,
    header: bool = False,
) -> List[float]:
    """Get axis-aligned bounding box of a Radiance scene.
    Args:
        path: path to Radiance scene
        header: include header
    Returns:
        list: bounding box
    """
    cmd = [str(BINPATH / "getbbox")]
    if not header:
        cmd.append("-h")
    cmd.extend(path)
    proc = sp.run(cmd, check=True, stdout=sp.PIPE)
    return [float(x) for x in proc.stdout.split()]


@handle_called_process_error
def oconv(*paths, warning=True, stdin=None, frozen: bool = False, octree=None) -> bytes:
    """Run Radiance oconv tool to build an octree.
    Args:
        paths: list of Radiance files
        warning: if False, warnings will be suppressed
        stdin: if not None, stdin will be used
        frozen: if True, the octree will be frozen
        octree: if provided, the resulting octree incorporate existing one
    Returns:
        bytes: output of oconv
    """
    cmd = [str(BINPATH / "oconv")]
    if octree:
        cmd.extend(["-i", str(octree)])
    if warning:
        cmd.append("-w")
    if frozen:
        cmd.append("-f")
    if stdin:
        if isinstance(stdin, bytes):
            cmd.append("-")
        else:
            raise TypeError("stdin should be bytes.")
    cmd.extend(paths)
    return sp.run(cmd, input=stdin, stdout=sp.PIPE, check=True).stdout
