"""
Radiance conversion routines.
"""

from pathlib import Path
import subprocess as sp
from typing import Optional, Sequence, Union


BINPATH = Path(__file__).parent / "bin"


def obj2rad(
    inp,
    quallist: bool = False,
    flatten: bool = False,
    mapfile: Optional[str] = None,
    objname: Optional[str] = None,
) -> bytes:
    """Convert Wavefront .OBJ file to RADIANCE description.

    Args:
        inp: Path to OBJ file
        quallist: Print a list of all the available quality settings.
        flatten: Flatten the hierarchy of the input file.
        mapfile: Path to a file containing a list of texture maps to be used.
        objname: Name of the object to be created.
    Returns:
        The output of the command
    """
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


def pkgbsdf(*xml: Union[str, Path], frozen: bool = False, stdout: bool = False) -> Optional[bytes]:
    """Pacakge BSDFs provided as XML for Radiance.

    Args:
        xml: Path to XML files
        frozen: produce frozen octree instance for any detail geometry.
        stdout: print the output to stdout, only works for a single XML input.
    Returns:
        The output of the command
    """
    cmd = [str(BINPATH / "pkgBSDF")]
    if frozen:
        cmd.append("-i")
    if stdout:
        if len(xml) > 1:
            raise ValueError("stdout only works for a single XML input.")
        cmd.append("-s")
    cmd.extend([str(i) for i in xml])
    result = sp.run(cmd, check=True, stdout=sp.PIPE).stdout
    if stdout:
        return result


def mgf2rad(*inp, matfile=None, mult=None, dist=None):
    """Convert Materials and Geometry Format file to RADIANCE description.
    Args:
        inp: Path to MGF file
        matfile: Path to material file where the translated materials will be written.
        mult: multiplier for all the emission values
        dist: glow distance (in meters) for all emitting surfaces.
    Returns:
        The output of the command
    """
    cmd = [str(BINPATH / "mgf2rad")]
    if matfile is not None:
        cmd.extend(["-m", matfile])
    if mult is not None:
        cmd.extend(["-e", mult])
    if dist is not None:
        cmd.extend(["-g", dist])
    cmd.extend(inp)
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


def ies2rad(
    *inp,
    libdir: Optional[str] = None,
    prefdir: Optional[str] = None,
    outname: Optional[str] = None,
    stdout: bool = False,
    units: Optional[str] = None,
    radius: Optional[float] = None,
    instancing_geometry: bool = False,
    lampdat: Optional[str] = None,
    lamp_type: Optional[str] = None,
    lamp_color: Optional[str] = None,
    set_default_lamp_color: Optional[str] = None,
    multiply_factor: Optional[float] = None,
):
    """Convert IES luminaire data to RADIANCE description.

    Args:
        inp: Path to IES file
        libdir: Path to directory where the library files are located.
        prefdir Set the library subdirectory.
        outname: Output file name root.
        stdout: Print the output to stdout.
        units: Set the units of the output file.
        rad: ignore the crude geometry given by the IES input file and use instead an illum sphere with radius rad.
        instancing_geometry: compile MGF detail geometry into a separate octree and create a single
            instance referencing it.
        lampdat: map lamp name to xy chromaticity and lumen depreciation data.
        lamp_type: lamp type.
        lamp_color: set lamp color to red green blue if lamp type is unknown.
        set_default_lamp_color: set default lamp color according to the entry for lamp in the lookup table.
        multiply_factor: multiply all output quantities by this factor. This is the best way to scale
            fixture brightness for different lamps.
    Returns:
        The output of the command
    """
    cmd = [str(BINPATH / "ies2rad")]
    if libdir is not None:
        cmd.extend(["-l", libdir])
    if prefdir is not None:
        cmd.extend(["-p", prefdir])
    if outname is not None:
        cmd.extend(["-o", outname])
    if stdout:
        cmd.append("-s")
    if units is not None:
        cmd.extend(["-d", units])
    if radius is not None:
        cmd.extend(["-i", str(radius)])
    if instancing_geometry:
        cmd.append("-g")
    if lampdat is not None:
        cmd.extend(["-f", lampdat])
    if lamp_type is not None:
        cmd.extend(["-t", lamp_type])
    if lamp_color is not None:
        if len(lamp_color) != 3:
            raise ValueError("lamp_color should be a list of 3 values.")
        cmd.extend(["-c", lamp_color])
    if set_default_lamp_color is not None:
        cmd.extend(["-u", set_default_lamp_color])
    if multiply_factor is not None:
        cmd.extend(["-m", str(multiply_factor)])
    cmd.extend(inp)


def bsdf2klems(
    *inp,
    spp: Optional[int] = None,
    half: bool = False,
    quater: bool = False,
    progress_bar: bool = False,
    progress_bar_length: Optional[int] = None,
    maxlobes: Optional[int] = None,
    forward: bool = False,
    backward: bool = True,
    expr: Optional[str] = None,
    file: Optional[str] = None,
):
    """Generate XML Klems matrix description of a BSDF.

    Args:
        inp: Path to XML file
        spp: number of samples for each input-output patch pair, default=1024.
        half: Generate instead a half Klems basis XML.
        quater: Generate instead a quater Klems basis XML.
        progress_bar: toggle to show progress bar.
        progress_bar_length: length of the progress bar, default=79 characters.
        maxlobes: maximum number of lobes in any interpolated radial basis
            function (default=15000). Setting the value to 0 turns off this limit.
        forward: generate forward matrix (default=off).
        backward: generate backward matrixi (default=on).
        expr: expression to evaluate.
        file: file to write the output to
    Returns:
        The output of the command
    """
    cmd = [str(BINPATH / "bsdf2klems")]
    if spp is not None:
        cmd.extend(["-n", str(spp)])
    if half:
        cmd.append("-h")
    elif quater:
        cmd.append("-q")
    if not progress_bar:
        cmd.append("-p")
    elif progress_bar_length is not None:
        cmd.append(f"p{progress_bar_length}")
    if len(inp) == 1 and not inp[0]:
        inp = inp[0]
        # xml input
        if inp.endswith(".xml"):
            cmd.append(inp)
        # func input
        else:
            if forward:
                cmd.append("+forward")
            if not backward:
                cmd.append("-backward")
            if expr is not None:
                cmd.extend(["-e", expr])
            if file is not None:
                cmd.extend(["-f", file])
            cmd.append(inp)
    # sir input
    else:
        if maxlobes is not None:
            cmd.extend(["-m", str(maxlobes)])
        cmd.extend(inp)
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


def bsdf2ttree(
    *inp,
    isotropic: bool = False,
    reciprocity_averaging: bool = True,
    resolution: int = 6,
    percent_cull: Sequence[float] = [90],
    super_samples: int = 256,
    difference_threshold: float = 0.35,
    progress_bar: bool = False,
    progress_bar_length: Optional[int] = None,
    maxlobes: int = 15000,
    forward: bool = False,
    backward: bool = True,
    expr: Optional[str] = None,
    file: Optional[str] = None,
):
    """Generate XML tensor tree description of a BSDF.

    Args:
        inp: Path to XML file
        isotropic: Generate an isotropic ttree.
        reciprocity_averaging: Use reciprocity averaging.
        resolution: resolution of the ttree.
        percent_cull: percent of the ttree to cull.
        super_samples: number of samples for each input-output patch pair, default=1024.
        difference_threshold: difference threshold for culling.
        progress_bar: toggle to show progress bar.
        progress_bar_length: length of the progress bar, default=79 characters.
        maxlobes: maximum number of lobes in any interpolated radial basis
            function (default=15000). Setting the value to 0 turns off this limit.
        forward: generate forward matrix (default=off).
        backward: generate backward matrixi (default=on).
        expr: expression to evaluate.
        file: file to write the output to
    Returns:
        The output of the command
    """
    cmd = [str(BINPATH / "bsdf2ttree")]
    if not progress_bar:
        cmd.append("-p")
    elif progress_bar_length is not None:
        cmd.append(f"p{progress_bar_length}")
    if not reciprocity_averaging:
        cmd.append("-a")
    cmd.extend(["-g", str(resolution)])
    cmd.extend(["-n", str(super_samples)])
    cmd.extend(["-s", str(difference_threshold)])
    if all([f.endswith(".sir") for f in inp]):
        cmd.extend(["-l", str(maxlobes)])
        if percent_cull is not None:
            if len(percent_cull) not in (1, len(inp)):
                raise ValueError(
                    "number of percent_cull should be 1 or equal to number of inputs."
                )
            if len(percent_cull) == 1:
                cmd.extend(["-t", str(percent_cull[0])])
            else:
                for i, p in zip(inp, percent_cull):
                    cmd.extend(["-t", str(i), str(p)])
        else:
            cmd.extend(inp)
    else:
        if len(inp) > 1:
            raise ValueError("only one input is allowed for bsdf_func invocation.")
        if isotropic:
            cmd.append("-t3")
        if forward:
            cmd.append("+forward")
        if not backward:
            cmd.append("-backward")
        if isinstance(percent_cull, (float, int)):
            cmd.extend(["-t", str(percent_cull)])
        else:
            cmd.extend(["-t", str(percent_cull[0])])
        if expr is not None:
            cmd.extend(["-e", expr])
        if file is not None:
            cmd.extend(["-f", file])
        cmd.append(inp[0])
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


def pabopto2bsdf(
    *inp,
    nproc: int = 1,
    symmetry: Optional[str] = None,
    angle: Optional[Union[float, str]] = None,
    reverse=False,
) -> bytes:
    """Convert BSDF measurements to a scattering interpolant representation.

    Args:
        inp: pab-opto Mountain files, need two or more.
        nproc: number of processors to use.
        symmetry: BSDF symmetry, which is one of "isotropic", "quadrilateral", "bilateral",
           "up", or "anisotropic".  Any of these may be abbreviated with as little as a
           single letter, and case is ignored.
        angle: cull scattered measurements that are nearer to grazing than the given angle
           in degrees.  If the word "auto" (which can be abbreviated as 'a' or 'A') is
           given instead of an angle, then the near-grazing angle will be determined by the
           lowest incident angle measurement present in the input data.  This is sometimes
           necessary to eliminate noise and edge effects that some measurements exhibit near grazing.
        reverse: reverses the assumed sample orientation front-to-back, and is discussed below under
            the "#intheta" header entry.
    Returns:
        The output of the command
    """
    cmd = [str(BINPATH / "pabopto2bsdf")]
    if nproc > 1:
        cmd.extend(["-n", str(nproc)])
    if symmetry is not None:
        if symmetry[0].lower() not in ("u", "b", "q", "i", "a"):
            raise ValueError("symmetry should be one of u, b, q, i, a.")
        cmd.extend(["-s", symmetry])
    if angle is not None:
        cmd.extend(["-g", str(angle)])
    if reverse:
        cmd.append("-t")
    if not isinstance(inp, (str, Path)):
        raise ValueError("input should be a string or a Path.")
    cmd.extend([str(i) for i in inp])
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout
