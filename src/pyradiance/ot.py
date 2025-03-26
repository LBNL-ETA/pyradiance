"""
Radiance scene compiler
"""

import subprocess as sp

from .anci import BINPATH, handle_called_process_error


@handle_called_process_error
def getbbox(
    *path: str | bytes,
    header: bool = False,
    warning: bool = True,
) -> list[float]:
    """Get axis-aligned bounding box of a Radiance scene.

    Args:
        path: path to Radiance scene
        header: include header

    Returns:
        list: bounding box
    """
    cmd = [str(BINPATH / "getbbox")]
    stdin: None | bytes = None
    if not header:
        cmd.append("-h")
    if isinstance(path[0], bytes):
        stdin = path[0]
        cmd.append("-")
    else:
        cmd.extend(path)
    proc = sp.run(cmd, input=stdin, check=True, stdout=sp.PIPE)
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
    cmd.extend(paths)
    if stdin:
        if isinstance(stdin, bytes):
            cmd.append("-")
        else:
            raise TypeError("stdin should be bytes.")
    return sp.run(cmd, input=stdin, stdout=sp.PIPE, check=True).stdout
