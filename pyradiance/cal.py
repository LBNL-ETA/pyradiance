"""
Radiance calculation utilites
"""

from pathlib import Path
import subprocess as sp

BINPATH = Path(__file__).parent / "bin"


def cnt(
    *dims,
    shuffled: bool = False,
) -> bytes:
    """Run Radiance cnt tool.

    Args:
        dims: list of dimensions
        shuffled: if True, the output will be shuffled
    Returns:
        bytes: output of cnt
    """
    cmd = [str(BINPATH / "cnt")]
    if shuffled:
        cmd.append("-s")
    cmd.extend([str(d) for d in dims])
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


def rlam(
    *inputs,
) -> bytes:
    """Run Radaince rlam tool.

    Args:
        inputs: list of input files or bytes. There can
        only be one bytes input.
    Returns:
        bytes: output of rlam
    """
    cmd = [str(BINPATH / "rlam")]
    stdin = []
    for inp in inputs:
        if isinstance(inp, (str, Path)):
            cmd.append(str(inp))
        elif isinstance(inp, bytes):
            cmd.append("-")
            stdin.append(inp)
    if len(stdin) > 1:
        raise ValueError("Only one stdin is allowed with rlam.")
    stdin = stdin[0] if stdin else None
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout
