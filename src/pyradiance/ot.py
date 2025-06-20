"""
Radiance scene compiler
"""

from pathlib import Path
import subprocess as sp

from .anci import BINPATH, handle_called_process_error


@handle_called_process_error
def getbbox(
    *inputs: str | bytes,
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
    stdins: list[bytes] = []
    paths: list[str] = []
    for inp in inputs:
        if isinstance(inp, bytes):
            stdins.append(inp)
        elif isinstance(inp, (str, Path)):
            paths.append(inp)
    stdin: None | bytes = None
    if not header:
        cmd.append("-h")
    if not warning:
        cmd.append("-w")
    if len(stdins) > 0:
        stdin = b"\b".join(stdins)
        cmd.append("-")
    if len(paths) > 0:
        cmd.extend(paths)
    proc = sp.run(cmd, input=stdin, check=True, stdout=sp.PIPE)
    return [float(x) for x in proc.stdout.split()]


@handle_called_process_error
def oconv(
    *paths: str,
    warning: bool = True,
    stdin: None | bytes = None,
    frozen: bool = False,
    octree: None | str | Path = None,
) -> bytes:
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
    if octree is not None:
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
