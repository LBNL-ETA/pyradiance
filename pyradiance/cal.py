"""
Radiance calculation utilites
"""

from pathlib import Path
import subprocess as sp
from typing import Optional

from .anci import BINPATH, handle_called_process_error


@handle_called_process_error
def cnt(
    *dims: int,
    shuffled: bool = False,
) -> bytes:
    """Index counter.

    Args:
        dims: list of dimensions
        shuffled: if True, the output will be shuffled
    Returns:
        bytes: output of cnt

    Examples:
        >>> cnt(2, 3)
        b'0 0\\n0 1\\n0 2\\n1 0\\n1 1\\n1 2\\n'
        >>> cnt(2, 3, shuffled=True)
        b'1 2\\n0 1\\n1 0\\n0 2\\n1 1\\n0 0\\n'
    """
    cmd = [str(BINPATH / "cnt")]
    if shuffled:
        cmd.append("-s")
    cmd.extend([str(d) for d in dims])
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


@handle_called_process_error
def rcalc(
    inp, 
    sep=None, 
    inform=None, 
    incount=1, 
    outform=None, 
    passive=False, 
    pass_negative=False, 
    inlimit=None,
    outlimit=None,
    source=None,
    expr=None,
    assign=None,
    exact_only=False,
    ignore_newlines=False,
    silent=False,
):
    stdin = None
    cmd = [str(BINPATH / "rcalc")]
    if sep is not None:
        cmd.append(f'-t{sep}')
    if inform is not None:
        cmd.append(f'-i{inform}{incount}')
    if outform is not None:
        cmd.append(f'-o{outform}')
    if inform and outform:
        if passive:
            cmd.append('-p')
        elif pass_negative:
            cmd.append('-P')
    if inlimit is not None:
        cmd.extend(['-in', str(inlimit)])
    if outlimit is not None:
        cmd.extend(['-on', str(outlimit)])
    if source is not None:
        cmd.extend(['-f', source])
    if expr is not None:
        cmd.extend(['-e', expr])
    if assign is not None:
        cmd.extend(['-s', assign])
    if exact_only:
        cmd.append('-b')
    if ignore_newlines:
        cmd.append('-l')
    if silent:
        cmd.append('-w')
    if isinstance(inp, (Path, str)):
        cmd.append(str(inp))
    elif isinstance(inp, bytes):
        stdin = inp
    else:
        raise TypeError(f"inp must be Path, str or bytes, not {type(inp)}")
    return sp.run(cmd, check=True, capture_output=True, input=stdin).stdout


@handle_called_process_error
def total(
    inp,
    mean=False,
    sumpower=0,
    multiply=False,
    find_max=False,
    find_min=False,
    inform: Optional[str] = None,
    incount=1,
    outform: Optional[str] = None,
    substep: Optional[int] = None,
    substep_reset=True,
    inlimit: Optional[int] = None,
    outlimit: Optional[int] = None,
    sep: Optional[str] = None,
) -> bytes:
    """Sum up columns.

    Args:
        inp: input file or bytes
        mean: if True, the mean value will be calculated
        sumpower: the power of the sum, mutally exclusive with multiply, find_max, and find_min
        multiply: if True, the values will be multiplied, mutally exclusive with sumpower, find_max, and find_min
        find_max: if True, the maximum value will be found, mutally exclusive with sumpower, multiply, and find_min
        find_min: if True, the minimum value will be found, mutally exclusive with sumpower, multiply, and find_max
        inform: input format
        incount: number of input values
        outform: output format
        substep: substep
        substep_reset: if True, the substep will be reset
        inlimit: input limit
        outlimit: output limit
        sep: separator

    Returns:
        bytes: output of total
    """
    cmd = [str(BINPATH / "total")]
    if mean:
        cmd.append("-m")
    if sumpower:
        cmd.append(f"-s{sumpower}")
    elif multiply:
        cmd.append("-p")
    elif find_max:
        cmd.append("-u")
    elif find_min:
        cmd.append("-l")
    if inform:
        if inform not in ("d", "f"):
            raise ValueError("inform must be 'd' or 'f'")
        cmd.append(f"-i{inform}{incount}")
    if outform:
        if outform not in ("d", "f"):
            raise ValueError("outform must be 'd' or 'f'")
        cmd.append(f"-o{outform}")
    if substep:
        cmd.extend(f"-{substep}")
        if not substep_reset:
            cmd.append("-r")
    if inlimit:
        cmd.extend(["-in", str(inlimit)])
    if outlimit:
        cmd.extend(["-on", str(outlimit)])
    if sep:
        cmd.append(f"-t{sep}")
    stdin = None
    if isinstance(inp, bytes):
        stdin = inp
    elif isinstance(inp, (str, Path)):
        cmd.append(str(inp))
    else:
        raise ValueError("Invalid input type.")
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout


@handle_called_process_error
def rlam(
    *inputs,
) -> bytes:
    """Laminate records from multiple files.

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
