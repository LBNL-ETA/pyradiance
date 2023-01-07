"""
Radiannce rendering programs
=============
This module contains the main API for pyradiance.
"""

from dataclasses import dataclass
from pathlib import Path
import subprocess as sp
import sys
from typing import Optional, Sequence, Union


BINPATH = Path(__file__).parent / "bin"


@dataclass
class RcModifier:
    """Modifier for rcontrib command.

    Attributes:
        modifier: Modifier name, mutually exclusive with modifier_path.
        modifier_path: Path to modifier file, mutually exclusive with modifier.
        calfile: Calc file path.
        expression: Expressions.
        nbins: Number of bins, can be expression.
        binv: Bin value.
        param: Parameter.
        xres: X resolution.
        yres: Y resolution.
        output: Output file.
    """

    modifier: Optional[str] = None
    modifier_path: Optional[str] = None
    calfile: Optional[str] = None
    expression: Optional[str] = None
    nbins: Optional[str] = None
    binv: Optional[str] = None
    param: Optional[str] = None
    xres: Optional[int] = None
    yres: Optional[int] = None
    output: Optional[str] = None

    def args(self):
        """Return modifier as a list of arguments."""
        arglist = []
        if self.calfile is not None:
            arglist.extend(["-f", str(self.calfile)])
        if self.expression is not None:
            arglist.extend(["-e", str(self.expression)])
        if self.nbins is not None:
            arglist.extend(["-bn", str(self.nbins)])
        if self.binv is not None:
            arglist.extend(["-b", str(self.binv)])
        if self.param is not None:
            arglist.extend(["-p", str(self.param)])
        if self.xres is not None:
            arglist.extend(["-x", str(self.xres)])
        if self.yres is not None:
            arglist.extend(["-y", str(self.yres)])
        if self.output is not None:
            arglist.extend(["-o", str(self.output)])
        if self.modifier is not None:
            arglist.extend(["-m", self.modifier])
        elif self.modifier_path is not None:
            arglist.extend(["-M", self.modifier_path])
        else:
            raise ValueError("Modifier or modifier path must be provided.")
        return arglist


def rcontrib(
    inp: bytes,
    octree: Union[Path, str],
    modifiers: Sequence[RcModifier],
    nproc=1,
    yres=None,
    inform=None,
    outform=None,
    params: Optional[Sequence[str]] = None,
) -> bytes:
    """Run rcontrib command.
    Args:
        inp: A bytes object.
        octree: A path to octree file.
        modifiers: A list of RcModifier objects.
        nproc: Number of processes.
        yres: Y resolution.
        inform: Input format.
        outform: Output format.
        params: A list of additional parameters.
    Returns:
        A bytes object.
    """
    cmd = [str(BINPATH / "rcontrib")]
    if nproc > 1 and sys.platform != "win32":
        cmd.extend(["-n", str(nproc)])
    if None not in (inform, outform):
        cmd.append(f"-f{inform}{outform}")
    for mod in modifiers:
        cmd.extend(mod.args())
    if yres is not None:
        cmd.extend(["-y", str(yres)])
    if params is not None:
        cmd.extend(params)
    cmd.append(str(octree))
    return sp.run(cmd, check=True, input=inp, stdout=sp.PIPE).stdout


def rpict(
    view,
    octree,
    xres: Optional[int] = None,
    yres: Optional[int] = None,
    report: float = 0,
    report_file: Optional[Path] = None,
    params: Optional[Sequence[str]] = None,
) -> bytes:
    """Get rpict command.
    Args:
        view: A view object.
        octree: A path to octree file.
        xres: X resolution.
        yres: Y resolution.
        report: Report.
        report_file: Report file.
        params: A list of additional parameters.
    Returns:
        A bytes object.
    """
    cmd = [str(BINPATH / "rpict")]
    cmd.extend(view.args())
    if report:
        cmd.extend(["-t", str(report)])
    if report_file:
        cmd.extend(["-e", str(report_file)])
    if xres:
        cmd.extend(["-x", str(xres)])
    if yres:
        cmd.extend(["-y", str(yres)])
    if params:
        cmd.extend(params)
    cmd.append(str(octree))
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


def rtrace(
    rays,
    octree,
    header: bool = True,
    inform: str = "a",
    outform: str = "a",
    irradiance: bool = False,
    irradiance_lambertian: bool = False,
    outspec: Optional[str] = None,
    trace_exclude: str = "",
    trace_include: str = "",
    trace_exclude_file: Optional[Union[str, Path]] = None,
    trace_include_file: Optional[Union[str, Path]] = None,
    uncorrelated: bool = False,
    xres: Optional[int] = None,
    yres: Optional[int] = None,
    nproc: Optional[int] = None,
    params: Optional[Sequence[str]] = None,
    report: bool = False,
    version: bool = False,
) -> bytes:
    """Run rtrace.
    Args:
        rays: A string of bytes representing the input rays.
        octree: Path to octree file.
        header: A boolean to indicate if the header should be included in the output.
        inform: Input format. Default is 'a'.
        outform: Output format. Default is 'a'.
        irradiance: A boolean to indicate if irradiance should be calculated.
        irradiance_lambertian: A boolean to indicate if irradiance should be calculated
            using Lambertian assumption.
        outspec: Output specification. Default is None.
        trace_exclude: A string of space separated material
            names to exclude from the trace.
        trace_include: A string of space separated material
            names to include in the trace.
        trace_exclude_file: Path to a file containing
            material names to exclude from the trace.
        trace_include_file: Path to a file containing
            material names to include in the trace.
        uncorrelated: A boolean to indicate if uncorrelated sampling should be used.
        xres: X resolution of the output image.
        yres: Y resolution of the output image.
        nproc: Number of processors to use.
        options: A SamplingParameters object.
    Returns:
        A string of bytes representing the output of rtrace.
    """
    cmd = [str(BINPATH / "rtrace")]
    if version:
        cmd.append("-version")
        return sp.run(cmd, check=True, stdout=sp.PIPE).stdout
    if not isinstance(rays, bytes):
        raise TypeError("Rays must be bytes")
    if not header:
        cmd.append("-h")
    if irradiance:
        cmd.append("-I")
    elif irradiance_lambertian:
        cmd.append("-i")
    cmd.append(f"-f{inform}{outform}")
    if outspec:
        cmd.append(f"-o{outspec}")
    if trace_exclude:
        cmd.append(f"-te{trace_exclude}")
    elif trace_include:
        cmd.append(f"-ti{trace_include}")
    elif trace_exclude_file:
        cmd.append(f"-tE{trace_exclude_file}")
    elif trace_include_file:
        cmd.append(f"-tI{trace_include_file}")
    if uncorrelated:
        cmd.append("-u+")
    if xres:
        cmd.extend(["-x", str(xres)])
    if yres:
        cmd.extend(["-y", str(yres)])
    if nproc:
        cmd.extend(["-n", str(nproc)])
    if report:
        cmd.extend(["-e", sys.stderr.name])
    if params is not None:
        cmd.extend(params)
    cmd.append(str(octree))
    return sp.run(cmd, check=True, stdout=sp.PIPE, input=rays).stdout
