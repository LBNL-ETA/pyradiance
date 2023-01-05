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


def rcalc():
    pass


def total():
    pass


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
    stdins = []
    for inp in inputs:
        if isinstance(inp, (str, Path)):
            cmd.append(str(inp))
        elif isinstance(inp, bytes):
            cmd.append("-")
            stdins.append(inp)
    if len(stdins) > 1:
        raise ValueError("Only one stdin is allowed with rlam.")
    stdin = stdins[0] if stdins else None
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout
