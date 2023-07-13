"""
Radiance utilities
"""

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import subprocess as sp
import sys
from typing import List, Optional, Sequence, Tuple, Union

from .anci import BINPATH, handle_called_process_error
from .model import View
from .param import SamplingParameters, parse_rtrace_args
from .ot import getbbox


@handle_called_process_error
def evalglare(
    inp,
    view: Optional[List[str]] = None,
    detailed: bool = False,
    ev_only: bool = False,
    ev: Optional[float] = None,
    smooth: bool = False,
    threshold: Optional[float] = None,
    task_area: Optional[tuple] = None,
    masking_file: Optional[Union[str, Path]] = None,
    band_lum_angle: Optional[float] = None,
    check_file: Optional[Union[str, Path]] = None,
    correction_mode: Optional[str] = None,
    peak_extraction: bool = True,
    peak_extraction_value: float = 50000,
    bg_lum_mode: int = 0,
    search_radius: float = 0.2,
    version: bool = False,
    source_color: Optional[Tuple[float, float, float]] = None,
):
    """Run evalglare on a Radiance image.
    Args:
        inp: input image
        view: view parameters
        detailed: detailed output
        ev_only: return vertical illuminance value
        ev: vertical illuminance value to use instead of the one computer from the image.
        smooth: enable smoothing function.
        threshold: Threshold factor.
        task_area: task area
        masking_file: masking file
        band_lum_angle: band luminance angle
        check_file: check file path.
        correction_mode: correction mode
        peak_extraction: enable luminance peak extraction
        peak_extraction_value: luminance peak extraction value
        bg_lum_mode: background luminance calculation mode
        search_radius: search radius
        version: print version
        source_color: source color
    Returns:
        Evalglare output
    """
    stdin = None
    cmd = [str(BINPATH / "evalglare")]
    if version:
        cmd.append("-v")
        return sp.run(cmd, check=True, capture_output=True).stdout
    if ev_only:
        cmd.append("-V")
    else:
        if detailed:
            cmd.append("-d")
        if ev is not None:
            if isinstance(ev, (float, int)):
                cmd.extend(["-i", str(ev)])
            else:
                cmd.extend(["-I", *map(str, ev)])
        if view is not None:
            cmd.extend(view)
        if check_file is not None:
            cmd.append("-c")
            cmd.append(str(check_file))
            if source_color is not None:
                cmd.append("-u")
                cmd.extend(*map(str, source_color))
        if smooth:
            cmd.append("-s")
        if threshold is not None:
            cmd.append("-b")
            cmd.append(str(threshold))
        if task_area:
            if check_file is not None:
                cmd.append("-T")
            else:
                cmd.append("-t")
            cmd.extend(*map(str, task_area))
        if bg_lum_mode:
            cmd.append("-q")
            cmd.append(str(bg_lum_mode))
        if masking_file:
            cmd.append("-A")
            cmd.append(str(masking_file))
        if band_lum_angle:
            cmd.append("-B")
            cmd.append(str(band_lum_angle))
        if correction_mode:
            cmd.append("-C")
            cmd.append(str(correction_mode))
        if not peak_extraction:
            cmd.append("-x")
        if peak_extraction_value:
            cmd.append("-Y")
            cmd.append(str(peak_extraction_value))
        if search_radius != 0.2:
            cmd.append("-r")
            cmd.append(str(search_radius))
    if isinstance(inp, bytes):
        stdin = inp
    elif isinstance(inp, (Path, str)):
        cmd.append(str(inp))
    else:
        raise ValueError("input must be a path, string, or bytes")
    return sp.run(cmd, input=stdin, check=True, capture_output=True).stdout


@handle_called_process_error
def dctimestep(
    *mtx,
    nstep: Optional[int] = None,
    header: bool = True,
    xres: Optional[int] = None,
    yres: Optional[int] = None,
    inform: Optional[str] = None,
    outform: Optional[str] = None,
    ospec: Optional[str] = None,
) -> Optional[bytes]:
    """Call dctimestep to perform matrix multiplication.
    Args:
        mtx: input matrices
        nstep: number of steps
        header: include header
        xres: x resolution
        yres: y resolution
        inform: input format
        outform: output format
        ospec: output specification
    Returns:
        bytes: output of dctimestep
    """
    _stdout = True
    stdin = None
    cmd = [str(BINPATH / "dctimestep")]
    if isinstance(mtx[-1], bytes):
        stdin = mtx[-1]
        mtx = mtx[:-1]
    if nstep:
        cmd.extend(["-n", str(nstep)])
    if not header:
        cmd.append("-h")
    if xres:
        cmd.extend(["-x", str(xres)])
    if yres:
        cmd.extend(["-y", str(yres)])
    if inform:
        cmd.append(f"-i{inform}")
    if outform:
        cmd.extend(f"-o{outform}")
    if ospec:
        cmd.extend(["-o", ospec])
        _stdout = False
    cmd.extend(mtx)
    result = sp.run(cmd, check=True, input=stdin, capture_output=True)
    if _stdout:
        return result.stdout
    return None


@handle_called_process_error
def getinfo(
    *inputs: Union[str, Path, bytes],
    dimension_only: bool = False,
    dimension: bool = False,
    strip_header: bool = False,
    replace: str = "",
    append: str = "",
    command: str = "",
) -> bytes:
    """Get header information from a Radiance file.
    Args:
        inputs: input file or bytes
        dimension_only: return only the dimension
        dimension: return the dimension
        strip_header: strip header from the output
        replace: replace the header with this string
        append: append this string to the header
        command: command to use to get the header
    Returns:
        getinfo output
    """
    stdin = None
    cmd = [str(BINPATH / "getinfo")]
    if dimension_only:
        cmd.append("-d")
    elif dimension:
        cmd.append("+d")
    elif replace:
        cmd.extend(["-r", replace])
    elif append:
        cmd.extend(["-a", append])
    if command:
        cmd.extend(["-c", command])
    if len(inputs) == 1 and isinstance(inputs[0], bytes):
        stdin = inputs[0]
        if strip_header:
            cmd.append("-")
    else:
        if any(isinstance(i, bytes) for i in inputs):
            raise TypeError("All inputs must be str or Path if one is")
        cmd.extend([str(i) for i in inputs])
    return sp.run(cmd, input=stdin, capture_output=True, check=True).stdout


def get_image_dimensions(image: Union[str, Path, bytes]) -> Tuple[int, int]:
    """Get the dimensions of an image.
    Args:
        image: image file or bytes
    Returns:
        Tuple[int, int]: width and height
    """
    output = getinfo(image, dimension_only=True).decode().split()
    return int(output[3]), int(output[1])


@handle_called_process_error
def get_header(inp, dimension: bool = False) -> bytes:
    """Get header information from a Radiance file.

    Args:
        inp: input file or bytes
    Returns:
        bytes: header
    """
    stdin = None
    cmd = [str(BINPATH / "getinfo")]
    if dimension:
        cmd.append("-d")
    if isinstance(inp, bytes):
        stdin = inp
    elif isinstance(inp, (str, Path)):
        cmd.append(str(inp))
    else:
        raise TypeError("inp must be a string, Path, or bytes")
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout


@handle_called_process_error
def rad(
    inp,
    dryrun: bool = False,
    update: bool = False,
    silent: bool = False,
    varstr: Optional[List[str]] = None,
) -> bytes:
    """Render a RADIANCE scene

    Args:
        inp: input file or bytes
        dryrun: print the command instead of running it
        update: update the scene
        silent: suppress output
        varstr: list of variables to set
        cwd: working directory
    Returns:
        bytes: output of rad
    """
    cmd = [str(BINPATH / "rad")]
    if dryrun:
        cmd.append("-n")
    if update:
        cmd.append("-t")
    if silent:
        cmd.append("-s")
    cmd.append(str(inp))
    if varstr is not None:
        cmd.extend(varstr)
    return sp.run(cmd, stdout=sp.PIPE, check=True).stdout


# # Replaced with read_rad from lib.py
# def read_rad(fpath: str) -> List[Primitive]:
#     """Parse a Radiance file.
#
#     Args:
#         fpath: Path to the .rad file
#
#     Returns:
#         A list of primitives
#     """
#     with open(fpath) as rdr:
#         lines = rdr.readlines()
#     if any((l.startswith("!") for l in lines)):
#         lines = xform(fpath).decode().splitlines()
#     return parse_primitive("\n".join(lines))


@handle_called_process_error
def rcode_depth(
    inp: Union[str, Path, bytes],
    ref_depth: str = "1.0",
    inheader: bool = True,
    outheader: bool = True,
    inresolution: bool = True,
    outresolution: bool = True,
    xres: Optional[int] = None,
    yres: Optional[int] = None,
    inform: str = "a",
    outform: str = "a",
    decode: bool = False,
    compute_intersection: bool = False,
    per_point: bool = False,
    depth_file: Optional[str] = None,
    flush: bool = False,
) -> bytes:
    """Encode/decode 16-bit depth map.

    Args:
        inp: input file or bytes
        ref_depth: reference distance, can be follow by /unit.
        inheader: Set to False to not expect header on input
        outheader: Set to False to not include header on output
        inresolution: Set to False to not expect resolution on input
        outresolution: Set to False to not include resolution on output
        xres: x resolution
        yres: y resolution
        inform: input format
        outform: output format when decoding
        decode: Set to True to decode instead
        compute_intersection: Set to True to compute intersection instead
        per_point: Set to True to compute per point instead of per pixel
        depth_file: depth file
        flush: Set to True to flush output
    Returns:
        bytes: output of rcode_depth
    """
    cmd = [str(BINPATH / "rcode_depth")]
    if decode or compute_intersection:
        if decode:
            cmd.append("-r")
        elif compute_intersection:
            cmd.append("-p")
        if per_point:
            cmd.append("-i")
        else:
            if not inheader:
                cmd.append("-hi")
            if not outheader:
                cmd.append("-ho")
            if not inresolution:
                cmd.append("-Hi")
            if not outresolution:
                cmd.append("-Ho")
        if flush:
            cmd.append("-u")
        if outform != "a":
            if outform not in ("d", "f"):
                raise ValueError("outform must be 'd' or 'f'")
            cmd.append(f"-f{outform}")
        if per_point and (depth_file is None):
            raise ValueError("depth_file must be set when per_point is True")
        if per_point and (not isinstance(inp, bytes)):
            raise TypeError(
                "inp(pixel coordinates) must be bytes when per_point is True"
            )
        if depth_file is not None:
            cmd.append(depth_file)
    else:
        if ref_depth:
            cmd.extend(["-d", ref_depth])
        if not inheader:
            cmd.append("-hi")
        if not outheader:
            cmd.append("-ho")
        if not inresolution:
            cmd.append("-Hi")
        if not outresolution:
            cmd.append("-Ho")
        if xres:
            cmd.extend(["-x", str(xres)])
        if yres:
            cmd.extend(["-y", str(yres)])
        if inform != "a":
            if inform not in ("d", "f"):
                raise ValueError("inform must be 'd' or 'f'")
            cmd.append(f"-f{inform}")
    stdin = None
    if isinstance(inp, bytes):
        stdin = inp
    elif isinstance(inp, (str, Path)):
        cmd.append(str(inp))
    else:
        raise TypeError("inp must be a string, Path, or bytes")
    return sp.run(cmd, stdout=sp.PIPE, input=stdin, check=True).stdout


@handle_called_process_error
def rcode_ident(
    inp: Union[str, Path, bytes],
    index_size: int = 16,
    sep: str = "\n",
    decode: bool = False,
    header: bool = True,
    xres: Optional[int] = None,
    yres: Optional[int] = None,
    resstr: bool = True,
    identifiers: bool = False,
    indexes: bool = False,
    per_point: bool = False,
    flush: bool = False,
) -> bytes:
    """Store identifiers in an indexed map and retrieve from same
    Args:
        inp: input file or bytes
        index_size: index size
        sep: separator
        decode: Set to True to decode instead
        header: Set to False to not to expect header on input;
            or not to include header on output when decoding
        xres: x resolution
        yres: y resolution
        resstr: Set to False to not include resolution string on output
        identifiers: Set to True to include identifiers on output
        indexes: Set to True to instead list identifiers indexes on output
        per_point: Set to True to compute per point instead of per pixel
        flush: Set to True to flush output after each identifier
    Returns:
        bytes: output of rcode_ident
    """
    cmd = [str(BINPATH / "rcode_ident")]
    if decode:
        cmd.append("-r")
        if not resstr:
            cmd.append("-H")
        if identifiers:
            cmd.append("-l")
        elif indexes:
            cmd.append("-n")
        if per_point:
            cmd.append("-i")
        if flush:
            cmd.append("-u")
    else:
        if index_size not in (8, 16, 24):
            raise ValueError("index_size must be 8, 16, or 24")
        cmd.append(f"-{index_size}")
        if xres:
            cmd.extend(["-x", str(xres)])
        if yres:
            cmd.extend(["-y", str(yres)])
    if not header:
        cmd.append("-h")
    if sep != "\n":
        cmd.append(f"-t{sep}")
    stdin = None
    if isinstance(inp, bytes):
        stdin = inp
    elif isinstance(inp, (str, Path)):
        cmd.append(str(inp))
    else:
        raise TypeError("inp must be a string, Path, or bytes")
    return sp.run(cmd, stdout=sp.PIPE, input=stdin, check=True).stdout


@handle_called_process_error
def rcode_norm(
    inp,
    inheader: bool = True,
    outheader: bool = True,
    inresolution: bool = True,
    outresolution: bool = True,
    xres: Optional[int] = None,
    yres: Optional[int] = None,
    inform: str = "a",
    outform: str = "a",
    decode: bool = False,
    per_point: bool = False,
    norm_file: Optional[str] = None,
    flush: bool = False,
) -> bytes:
    """Encode/decode 32-bit surface normal map.

    Args:
        inp: input file or bytes
        inheader: Set to False to not expect header on input
        outheader: Set to False to not include header on output
        inresolution: Set to False to not expect resolution on input
        outresolution: Set to False to not include resolution on output
        xres: x resolution
        yres: y resolution
        inform: input format
        outform: output format when decoding
        decode: Set to True to decode instead
        per_point: Set to True to compute per point instead of per pixel
        flush: Set to True to flush output
    Returns:
        bytes: output of rcode_norm
    """
    cmd = [str(BINPATH / "rcode_norm")]
    if decode:
        cmd.append("-r")
        if not inheader:
            cmd.append("-hi")
        if not outheader:
            cmd.append("-ho")
        if per_point:
            cmd.append("-i")
        else:
            if not inresolution:
                cmd.append("-Hi")
            if not outresolution:
                cmd.append("-Ho")
        if flush:
            cmd.append("-u")
        if outform != "a":
            if outform not in ("d", "f"):
                raise ValueError("outform must be 'd' or 'f'")
            cmd.append(f"-f{outform}")
        if per_point and (norm_file is None):
            raise ValueError("norm_file must be set when per_point is True")
        if per_point and (not isinstance(inp, bytes)):
            raise TypeError(
                "inp(pixel coordinates) must be bytes when per_point is True"
            )
        if norm_file is not None:
            cmd.append(norm_file)

    else:
        if not inheader:
            cmd.append("-hi")
        if not outheader:
            cmd.append("-ho")
        if not inresolution:
            cmd.append("-Hi")
        if not outresolution:
            cmd.append("-Ho")
        if xres:
            cmd.extend(["-x", str(xres)])
        if yres:
            cmd.extend(["-y", str(yres)])
        if inform != "a":
            if inform not in ("d", "f"):
                raise ValueError("inform must be 'd' or 'f'")
            cmd.append(f"-f{inform}")
    stdin = None
    if isinstance(inp, bytes):
        stdin = inp
    elif isinstance(inp, (str, Path)):
        cmd.append(str(inp))
    else:
        raise TypeError("inp must be a string, Path, or bytes")
    return sp.run(cmd, stdout=sp.PIPE, input=stdin, check=True).stdout


def render(
    scene,
    view: Optional[View] = None,
    quality: str = "Medium",
    variability: str = "Medium",
    detail: str = "Medium",
    nproc: int = 1,
    resolution: Optional[Tuple[int, int]] = None,
    ambbounce: Optional[int] = None,
    ambcache: bool = True,
    params: Optional[SamplingParameters] = None,
) -> bytes:
    """Render a scene.

    Args:
        scene: Scene object.
        quality: Quality level.
        variability: Variability level.
        detail: Detail level.
        nproc: Number of processes to use.
        ambbounce: Number of ambient bounces.
        ambcache: Use ambient cache.
        params: Sampling parameters.
    Returns:
        tuple[bytes, int, int]: output of render, width, height
    """
    nproc = 1 if sys.platform == "win32" else nproc
    octpath = Path(f"{scene.sid}.oct")
    scenestring = " ".join(
        [str(srf) for _, srf in {**scene.surfaces, **scene.sources}.items()]
    )
    materialstring = " ".join((str(mat) for _, mat in scene.materials.items()))
    rad_render_options = []
    if ambbounce is not None:
        rad_render_options.extend(["-ab", str(ambbounce)])
    if not ambcache:
        rad_render_options.extend(["-aa", "0"])
    aview = scene.views[0] if view is None else view
    xmin, xmax, ymin, ymax, zmin, zmax = getbbox(*scene.surfaces.values())
    distance = (
        ((xmax - xmin) / 2) ** 2 + ((ymax - ymin) / 2) ** 2 + ((zmax - zmin) / 2) ** 2
    )
    view_center = (
        (aview.position[0] - (xmax + xmin) / 2) ** 2
        + (aview.position[1] - (ymax + ymin) / 2) ** 2
        + (aview.position[2] - (zmax + zmin) / 2) ** 2
    )
    if view_center > distance:
        zone = f"E {xmin} {xmax} {ymin} {ymax} {zmin} {zmax}"
    else:
        zone = f"I {xmin} {xmax} {ymin} {ymax} {zmin} {zmax}"

    radvars = [
        f"ZONE={zone}",
        f"OCTREE={octpath}",
        f"scene={scenestring}",
        f"materials={materialstring}",
        f"QUALITY={quality}",
        f"VARIABILITY={variability}",
        f"DETAIL={detail}",
        f"render= {' '.join(rad_render_options)}",
    ]
    if ambbounce and ambcache:
        ambfile = f"{scene.sid}.amb"
        radvars.append(f"AMBFILE={ambfile}")
        if os.path.exists(ambfile):
            os.remove(ambfile)
    if resolution:
        xres, yres = resolution
        radvars.append(f"RESOLUTION={xres} {yres}")
    else:
        xres = yres = 512
    radcmds = [
        l.strip()
        for l in rad(os.devnull, dryrun=True, varstr=radvars).decode().splitlines()
    ]
    _sidx = 0
    if radcmds[0].startswith("oconv"):
        print("rebuilding octree...")
        with open(octpath, "wb") as wtr:
            sp.run(shlex.split(radcmds[0].split(">", 1)[0]), check=True, stdout=wtr)
        _sidx = 1
    elif radcmds[0].startswith(("rm", "del")):
        sp.run(shlex.split(radcmds[0]), check=True)
        _sidx = 1
    radcmds = [c for c in radcmds[_sidx:] if not c.startswith(("pfilt", "rm"))]
    argdict = parse_rtrace_args(" ".join(radcmds))

    options = SamplingParameters()
    options.dt = 0.05
    options.ds = 0.25
    options.dr = 1
    options.ad = 512
    options.as_ = 128
    options.aa = 0.2
    options.ar = 64
    options.lr = 7
    options.lw = 1e-03
    options.update_from_dict(argdict)
    if params is not None:
        options.update(params)
    return rtpict(
        aview, octpath, nproc=nproc, xres=xres, yres=yres, params=options.args()
    )


@handle_called_process_error
def rfluxmtx(
    receiver: Union[str, Path],
    surface: Optional[Union[str, Path]] = None,
    rays: Optional[bytes] = None,
    params: Optional[Sequence[str]] = None,
    octree: Optional[Path] = None,
    scene: Optional[Sequence[Union[Path, str]]] = None,
) -> bytes:
    """Run rfluxmtx command.
    Args:
        scene: A Scene object.
        sender: A Sender.
        receiver: A Radiance SensorGrid.
        option: Radiance parameters for rfluxmtx command as a list of strings.
    Sender: stdin, polygon
    Receiver: surface with -o
    """
    cmd = [str(BINPATH / "rfluxmtx")]
    if params:
        cmd.extend(params)
    if surface is not None:
        cmd.append(str(surface))
    else:
        cmd.append("-")
    cmd.append(str(receiver))
    if octree is not None:
        cmd.extend(["-i", str(octree)])
    if scene is not None:
        cmd.extend([str(s) for s in scene])
    return sp.run(cmd, check=True, stdout=sp.PIPE, input=rays).stdout


@handle_called_process_error
def rmtxop(
    inp, outform="a", transpose=False, scale=None, transform=None, reflectance=None
):
    """Run rmtxop command."""
    cmd = [str(BINPATH / "rmtxop")]
    stdin = None
    if transpose:
        cmd.append("-t")
    if outform != "a":
        cmd.append(f"-f{outform}")
    if scale is not None:
        cmd.extend(["-s", str(scale)])
    if transform is not None:
        cmd.extend(["-c", *[str(c) for c in transform]])
    if reflectance is not None:
        cmd.append(f"r{reflectance[0]}")
    if isinstance(inp, bytes):
        stdin = inp
        cmd.append("-")
    elif isinstance(inp, (str, Path)):
        cmd.append(str(inp))
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout


@handle_called_process_error
def rsensor(
    sensor: Sequence[Union[str, Path]],
    sensor_view: Optional[Sequence[Union[str, Path]]] = None,
    direct_ray: Optional[Sequence[int]] = None,
    ray_count: Optional[Sequence[int]] = None,
    octree: Optional[Union[str, Path]] = None,
    nproc: int = 1,
    params: Optional[Sequence[str]] = None,
) -> bytes:
    """Compute sensor signal from a RADIANCE scene

    Args:
        sensor: Sensor file
        sensor_view: Sensor view file
        direct_ray: The number of rays sent to each light source per sensor
        ray_count: The number of ray samples sent at random
        octree: Octree file
        nproc: Number of processors to use
        params: Additional parameters for rsensor command
    Returns:
        Output of rsensor command
    """
    cmd = [str(BINPATH / "rsensor")]

    for i, sf in enumerate(sensor):
        if ray_count is not None:
            cmd.extend(["-rd", str(ray_count[i])])
        if None not in (direct_ray, octree):
            cmd.extend(["-dn", str(direct_ray[i])])
        if sensor_view is not None:
            cmd.append(str(sensor_view[i]))
        cmd.append(str(sf))
    if octree:
        if nproc > 1:
            cmd.extend(["-n", str(nproc)])
        if params:
            cmd.extend(params)
        cmd.append(str(octree))
    else:
        cmd.append(".")
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


@handle_called_process_error
def rtpict(
    view: View,
    octree: Union[str, Path],
    nproc: int = 1,
    outform: Optional[str] = None,
    outdir: Optional[str] = None,
    ref_depth: Optional[str] = None,
    xres: Optional[int] = None,
    yres: Optional[int] = None,
    params: Optional[Sequence[str]] = None,
) -> Optional[bytes]:
    """Run rtpict command.
    Args:
        view: A View object.
        octree: Path to octree file.
        nproc: Number of processors to use.
        outform: Output format. Default is "i".
        outdir: Output directory. Default is current directory.
        ref_depth: Maximum number of reflections. Default is 5.
        xres: Horizontal resolution. Default is 512.
        yres: Vertical resolution. Default is 512.
        params: Radiance parameters for rtpict command as a list of strings.
    Returns:
        Rendered image as output or None if output to directory
    """
    cmd = [str(BINPATH / "rtpict")]
    cmd.extend(view.args())
    cmd.extend(["-n", str(nproc)])
    if outform is not None:
        if outdir is not None:
            cmd.extend([f"-o{outform}", str(outdir)])
    if ref_depth is not None:
        cmd.extend(["-d", str(ref_depth)])
    if xres:
        cmd.extend(["-x", str(xres)])
    if yres:
        cmd.extend(["-y", str(yres)])
    if params:
        cmd.extend(params)
    cmd.append(str(octree))
    proc = sp.run(cmd, check=True, stdout=sp.PIPE)
    if not outdir:
        return proc.stdout


@handle_called_process_error
def strip_header(inp) -> bytes:
    """Use getinfo to strip the header from a Radiance file."""
    cmd = ["getinfo", "-"]
    if isinstance(inp, bytes):
        stdin = inp
    else:
        raise TypeError("Input must be bytes")
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout


@handle_called_process_error
def vwrays(
    pixpos: Optional[bytes] = None,
    unbuf: bool = False,
    outform: str = "a",
    ray_count: int = 1,
    pixel_jitter: float = 0,
    pixel_diameter: float = 0,
    pixel_aspect: float = 1,
    xres: int = 512,
    yres: int = 512,
    dimensions: bool = False,
    view: Optional[Sequence[str]] = None,
    pic: Optional[Path] = None,
    zbuf: Optional[Path] = None,
) -> bytes:
    """vwrays."""
    stdin = None
    cmd = [str(BINPATH / "vwrays")]
    if pixpos is not None:
        stdin = pixpos
        cmd.append("-i")
    if unbuf:
        cmd.append("-u")
    if outform != "a":
        cmd.append(f"-f{outform}")
    cmd.extend(["-c", str(ray_count)])
    cmd.extend(["-pj", str(pixel_jitter)])
    cmd.extend(["-pd", str(pixel_diameter)])
    cmd.extend(["-pa", str(pixel_aspect)])
    cmd.extend(["-x", str(xres)])
    cmd.extend(["-y", str(yres)])
    if dimensions:
        cmd.append("-d")
    if view is not None:
        cmd.extend(view)
    elif pic is not None:
        cmd.append(str(pic))
        if zbuf is not None:
            cmd.append(str(zbuf))
    else:
        raise ValueError("Either view or pic should be provided.")
    return sp.run(cmd, input=stdin, stdout=sp.PIPE, check=True).stdout


@handle_called_process_error
def vwright(
    view,
    distance: float = 0,
) -> bytes:
    """Run vwright."""
    cmd = [str(BINPATH / "vwright")]
    cmd.extend(view.args())
    cmd.append(str(distance))
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


@dataclass
class WrapBSDFInput:
    """Input data for wrapbsdf command."""

    spectrum: Optional[str] = "Visible"
    tf: Optional[Union[str, Path]] = None
    tb: Optional[Union[str, Path]] = None
    rf: Optional[Union[str, Path]] = None
    rb: Optional[Union[str, Path]] = None

    def args(self) -> List[str]:
        """Return command as a list of strings."""
        arglist = ["-s", self.spectrum]
        if self.tf:
            arglist.extend(["-tf", str(self.tf)])
        if self.tb:
            arglist.extend(["-tb", str(self.tb)])
        if self.rf:
            arglist.extend(["-rf", str(self.rf)])
        if self.rb:
            arglist.extend(["-rb", str(self.rb)])
        if len(arglist) == 2:
            raise ValueError("At least one of tf, tb, rf, rb should be provided.")
        return arglist


@handle_called_process_error
def wrapbsdf(
    inxml=None,
    enforce_window=False,
    comment: Optional[str] = None,
    correct_solid_angle=False,
    basis: Optional[str] = None,
    inp: Optional[Sequence[WrapBSDFInput]] = None,
    unlink: bool = False,
    unit=None,
    geometry=None,
    **kwargs,
) -> bytes:
    """Wrap BSDF.
    Args:
        inp: Input file. Default is stdin.
        enforce_window: Enforce window convention. Default is False.
        comment: Comment. Default is None.
        correct_solid_angle: Correct solid angle. Default is False.
        basis: Basis. Default is None.
        tf: Front transmittance. Default is None.
        tb: Back transmittance. Default is None.
        rf: Front reflectance. Default is None.
        rb: Back reflectance. Default is None.
        spectr: Spectral data. Default is None.
        unlink: Unlink. Default is False.
        unit: Unit. Default is None.
        geometry: Geometry. Default is None.
        **kwargs: Additional arguments for Window tags such as n, m, t...
    Returns:
        Wrapped BSDF.
    """
    cmd = [str(BINPATH / "wrapBSDF")]
    if enforce_window:
        cmd.append("-W")
    if correct_solid_angle:
        cmd.append("-c")
    if basis:
        cmd.extend(["-a", basis])
    if inp is not None:
        for s in inp:
            cmd.extend(s.args())
    if unlink:
        cmd.append("-U")
    if unit:
        cmd.extend(["-u", unit])
    if comment:
        cmd.extend(["-C", comment])
    if geometry:
        cmd.extend(["-g", geometry])
    fields_keys = ["n", "m", "d", "c", "ef", "eb", "eo", "t", "h", "w"]
    fields = []
    for key in fields_keys:
        if key in kwargs:
            fields.append(f"{key}={kwargs[key]}")
    if fields:
        cmd.extend(["-f", ";".join(fields)])
    if inxml is not None:
        cmd.append(str(inxml))
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


@handle_called_process_error
def xform(
    inp,
    translate: Optional[Tuple[float, float, float]] = None,
    expand_cmd: bool = True,
    iprefix: Optional[str] = None,
    modifier: Optional[str] = None,
    invert: bool = False,
    rotatex: Optional[float] = None,
    rotatey: Optional[float] = None,
    rotatez: Optional[float] = None,
    scale: Optional[float] = None,
    mirrorx: bool = False,
    mirrory: bool = False,
    mirrorz: bool = False,
) -> bytes:
    """Transform a RADIANCE scene description

    Notes:
        Iterate and arrays are not supported.

    Args:
        inp: Input file or string
        translate: Translation vector
        expand_cmd: Set to True to expand command
        iprefix: Prefix identifier
        mprefix: Set surface modifier to this name
        invert: Invert surface normal
        rotatex: Rotate the scene degrees about the x axis.
            A positive rotation corresponds to
        rotatey: Rotate the scene degrees about the y axis.
        rotatez: Rotate the scene degrees about the z axis.
        scale: Scale the scene by this factor
        mirrorx: Mirror the scene about the yz plane.
        mirrory: Mirror the scene about the xz plane.
        mirrorz: Mirror the scene about the xy plane.
    Returns:
        The transformed scene description in bytes

    """
    stdin = None
    cmd = [str(BINPATH / "xform")]
    if not expand_cmd:
        cmd.append("-c")
    if iprefix:
        cmd.extend(["-n", iprefix])
    if modifier:
        cmd.extend(["-m", modifier])
    if invert:
        cmd.append("-I")
    if rotatex:
        cmd.extend(["-rx", str(rotatex)])
    if rotatey:
        cmd.extend(["-ry", str(rotatey)])
    if rotatez:
        cmd.extend(["-rz", str(rotatez)])
    if scale:
        cmd.extend(["-s", str(scale)])
    if mirrorx:
        cmd.append("-mx")
    if mirrory:
        cmd.append("-my")
    if mirrorz:
        cmd.append("-mz")
    if translate is not None:
        cmd.extend(["-t", *(str(v) for v in translate)])
    if isinstance(inp, bytes):
        stdin = inp
    else:
        cmd.append(inp)
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout
