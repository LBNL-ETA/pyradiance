"""
Radiannce rendering programs
=============
This module contains the main API for pyradiance.
"""

import subprocess as sp
import sys
from pathlib import Path
from typing import Sequence

from .anci import BINPATH, handle_called_process_error


@handle_called_process_error
def mkpmap(
    octree: Path | str,
    global_map: None | tuple[Path | str, int] = None,
    caustic_map: None | tuple[Path | str, int] = None,
    volume_map: None | tuple[Path | str, int] = None,
    direct_map: None | tuple[Path | str, int] = None,
    contrib_map: None | tuple[Path | str, int] = None,
    pre_global_map: None | tuple[Path | str, int, float] = None,
    predistrib: None | float = None,
    rect_region: None | tuple[float, float, float, float, float, float] = None,
    sphere_region: None | tuple[float, float, float, float] = None,
    maxbounce: None | int = None,
    maxprepass: None | int = None,
    port_mod: None | Sequence[str] = None,
    port_modfile: None | str = None,
    precomp: None | float = None,
    seed: None | int = None,
    virtual_mod: None | Sequence[str] = None,
    virtual_modfile: None | str = None,
    amb_excl_mod: None | str = None,
    amb_excl_modfile: None | str = None,
    amb_incl_mod: None | str = None,
    amb_incl_modfile: None | str = None,
    backface_vis: bool = False,
    sample_res: None | int = None,
    partition_size: None | float = None,
    progress_file: None | str = None,
    overwrite: bool = False,
    maxdist: None | float = None,
    scattering_albedo: None | tuple[float, float, float] = None,
    extinction_coefficient: None | tuple[float, float, float] = None,
    scattering_eccentricity: None | float = None,
    nproc: int = 1,
    progress_interval: None | int = None,
) -> None:
    """
    Mkpmap takes a RADIANCE scene description as an octree and performs
    Monte Carlo forward path tracing from the light sources, depositing
    indirect ray hitpoints along with their energy (flux) as "photons".
    The resulting localised energy distribution represents a global
    illumination solution which is written to a file for subsequent evaluation
    by rpict(1), rtrace(1) and rvu(1) in a backward raytracing pass.
    The photon map(s) can be reused for multiple viewpoints and sensor
    locations as long as the geometry remains unchanged.
    Args:
        octree: Octree file path.
        global_map: Global map file path and number of photons.
        caustic_map: Caustic map file path and number of photons.
        volume_map: Volume map file path and number of photons.
        direct_map: Direct map file path and number of photons.
        contrib_map: Contribution map file path and number of photons.
        pre_global_map: Precomputed global map file path, number of photons and bandwidth.
        predistrib: Photon predistribution factor.
        rect_region: Rectangular region
        sphere_region: Spherical region
        maxbounce: Maximum number of bounces.
        maxprepass: Maximum number of iteratiosn of distributoin prepass before terminating.
        port_mod: Specifies a modifier to act as a photon port.
        port_modfile: File with modifiers to act as photon ports.
        precomp: Fraction of global photons to precompute.
        seed: Random seed.
        virtual_mod: Specifies a modifier to act as a virtual source.
        virtual_modfile: File with modifiers to act as virtual sources.
        amb_excl_mod: Specifies a modifier to exclude from ambient calculation.
        amb_excl_modfile: File with modifiers to exclude from ambient calculation.
        amb_incl_mod: Specifies a modifier to include in ambient calculation.
        amb_incl_modfile: File with modifiers to include in ambient calculation.
        backface_vis: Backface visibility.
        sample_res: Sample resolution.



    """
    cmd = [str(BINPATH / "mkpmap")]
    if global_map is not None:
        cmd.extend(["-apg", str(global_map[0]), str(global_map[1])])
    if caustic_map is not None:
        cmd.extend(["-apc", str(caustic_map[0]), str(caustic_map[1])])
    if volume_map is not None:
        cmd.extend(["-apv", str(volume_map[0]), str(volume_map[1])])
    if direct_map is not None:
        cmd.extend(["-apd", str(direct_map[0]), str(direct_map[1])])
    if contrib_map is not None:
        cmd.extend(["-apC", str(contrib_map[0]), str(contrib_map[1])])
    if pre_global_map is not None:
        cmd.extend(
            [
                "-app",
                str(pre_global_map[0]),
                str(pre_global_map[1]),
                str(pre_global_map[2]),
            ]
        )
        if precomp is not None:
            cmd.extend(["-apP", str(precomp)])
    if predistrib is not None:
        cmd.extend(["-apD", str(predistrib)])
    if rect_region is not None:
        cmd.extend(["-api", *map(str, rect_region)])
    elif sphere_region is not None:
        cmd.extend(["-apI", *map(str, sphere_region)])
    if maxbounce is not None:
        cmd.extend(["-lr", str(maxbounce)])
    if maxprepass is not None:
        cmd.extend(["-apM", str(maxprepass)])
    if port_mod is not None:
        for mod in port_mod:
            cmd.extend(["-apo", mod])
    elif port_modfile is not None:
        cmd.extend(["-apO", port_modfile])
    if seed is not None:
        cmd.extend(["-apr", str(seed)])
    if virtual_mod is not None:
        for mod in virtual_mod:
            cmd.extend(["-aps", mod])
    elif virtual_modfile is not None:
        cmd.extend(["-apS", virtual_modfile])
    if amb_excl_mod is not None:
        for mod in amb_excl_mod:
            cmd.extend(["-ae", mod])
    elif amb_excl_modfile is not None:
        cmd.extend(["-aE", amb_excl_modfile])
    elif amb_incl_mod is not None:
        for mod in amb_incl_mod:
            cmd.extend(["-ai", mod])
    elif amb_incl_modfile is not None:
        cmd.extend(["-aI", amb_incl_modfile])
    if backface_vis:
        cmd.append("-bv+")
    if sample_res is not None:
        cmd.extend(["-dp", str(sample_res)])
    if partition_size is not None:
        cmd.extend(["-ds", str(partition_size)])
    if progress_file is not None:
        cmd.extend(["-e", progress_file])
    if overwrite:
        cmd.append("-fo+")
    if maxdist is not None:
        cmd.extend(["-ld", str(maxdist)])
    if scattering_albedo is not None:
        cmd.extend(["-ma", *map(str, scattering_albedo)])
    if extinction_coefficient is not None:
        cmd.extend(["-me", *map(str, extinction_coefficient)])
    if scattering_eccentricity is not None:
        cmd.extend(["-mg", str(scattering_eccentricity)])
    cmd.extend(["-n", str(nproc)])
    if progress_interval is not None:
        cmd.extend(["-t", str(progress_interval)])
    cmd.append(str(octree))
    sp.run(cmd, check=True, capture_output=True)


class Rcontrib:
    def __init__(
        self,
        inp: bytes,
        octree: Path | str,
        nproc: int = 1,
        yres: None | int = None,
        inform: None | str = None,
        outform: None | str = None,
        report: int = 0,
        params: None | Sequence[str] = None,
    ):
        self.cmd = [str(BINPATH / "rcontrib")]
        self.octree = octree
        self.inp = inp
        self.cmd.extend(["-n", str(nproc)])
        if params is not None:
            self.cmd.extend(params)
        if None not in (inform, outform):
            self.cmd.append(f"-f{inform}{outform}")
        if yres is not None:
            self.cmd.extend(["-y", str(yres)])
        if report:
            self.cmd.extend(["-t", str(report)])

    def add_modifier(
        self,
        modifier: None | str = None,
        modifier_path: None | str = None,
        calfile: None | str = None,
        expression: None | str = None,
        nbins: None | str = None,
        binv: None | str = None,
        param: None | str = None,
        xres: None | int = None,
        yres: None | int = None,
        output: None | str = None,
    ):
        arglist = []
        if calfile is not None:
            arglist.extend(["-f", str(calfile)])
        if expression is not None:
            arglist.extend(["-e", str(expression)])
        if nbins is not None:
            arglist.extend(["-bn", str(nbins)])
        if binv is not None:
            arglist.extend(["-b", str(binv)])
        if param is not None:
            arglist.extend(["-p", str(param)])
        if xres is not None:
            arglist.extend(["-x", str(xres)])
        if yres is not None:
            arglist.extend(["-y", str(yres)])
        if output is not None:
            arglist.extend(["-o", str(output)])
        if modifier is not None:
            arglist.extend(["-m", modifier])
        elif modifier_path is not None:
            arglist.extend(["-M", modifier_path])
        else:
            raise ValueError("Modifier or modifier path must be provided.")
        self.cmd.extend(arglist)
        return self

    @handle_called_process_error
    def __call__(self):
        self.cmd.append(str(self.octree))
        return sp.run(
            self.cmd, check=True, input=self.inp, stderr=sp.PIPE, stdout=sp.PIPE
        ).stdout


@handle_called_process_error
def rpict(
    view: Sequence[str],
    octree: Path | str,
    xres: None | int = None,
    yres: None | int = None,
    report: float = 0,
    report_file: None | Path = None,
    params: None | Sequence[str] = None,
) -> bytes:
    """Get rpict command.

    Args:
        view: A list of view parameters in strings.
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
    cmd.extend(view)
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
    return sp.run(cmd, check=True, capture_output=True).stdout


@handle_called_process_error
def rtrace(
    rays: bytes,
    octree: Path | str,
    header: bool = True,
    inform: str = "a",
    outform: str = "a",
    irradiance: bool = False,
    irradiance_lambertian: bool = False,
    outspec: None | str = None,
    trace_exclude: str = "",
    trace_include: str = "",
    trace_exclude_file: None | str | Path = None,
    trace_include_file: None | str | Path = None,
    uncorrelated: bool = False,
    xres: None | int = None,
    yres: None | int = None,
    nproc: None | int = None,
    params: None | Sequence[str] = None,
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
    return sp.run(cmd, check=True, capture_output=True, input=rays).stdout
