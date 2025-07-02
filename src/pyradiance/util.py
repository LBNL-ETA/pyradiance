"""
Radiance utilities
"""

import csv
import os
import re
import subprocess as sp
import tempfile
from pathlib import Path
from typing import Sequence, Literal

from .anci import BINPATH, handle_called_process_error

from .bsdf import spec_xyz, xyz_rgb
from .model import Primitive, Scene
from .rad_params import View, RayParams, get_ray_params_args, get_view_args
from .ot import getbbox
from .px import pvaluer
from .cal import cnt
from .rt import rpict, rtrace


Ops = Literal["*", "+", ".", "/"]
FileType = Literal["a", "f", "d", "c"]
SpectrumTag = Literal["Visible", "Solar"]


@handle_called_process_error
def evalglare(
    inp: str | bytes | Path,
    view: None | list[str] = None,
    detailed: bool = False,
    ev_only: bool = False,
    ev: None | float | Sequence[float] = None,
    smooth: bool = False,
    threshold: None | float = None,
    task_area: None | tuple = None,
    masking_file: None | str | Path = None,
    band_lum_angle: None | float = None,
    check_file: None | str | Path = None,
    correction_mode: None | str = None,
    peak_extraction: bool = True,
    peak_extraction_value: float = 50000,
    bg_lum_mode: int = 0,
    search_radius: float = 0.2,
    version: bool = False,
    source_color: None | tuple[float, float, float] = None,
    fast: None | int = None,
) -> bytes:
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
    stdin: None | bytes = None
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
        if fast is not None:
            cmd.append(f"-{fast}")
        if view is not None:
            cmd.extend(view)
        if check_file is not None:
            cmd.append("-c")
            cmd.append(str(check_file))
            if source_color is not None:
                cmd.append("-u")
                cmd.extend(map(str, source_color))
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
            cmd.extend(map(str, task_area))
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
    return sp.run(cmd, input=stdin, check=True, capture_output=True).stdout


@handle_called_process_error
def dctimestep(
    *mtx: str | bytes,
    nstep: None | int = None,
    header: bool = True,
    xres: None | int = None,
    yres: None | int = None,
    inform: None | str = None,
    outform: None | str = None,
    ospec: None | str = None,
) -> None | bytes:
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
    if len(mtx) not in (2, 4):
        raise ValueError("mtx must be a list of 2 or 4 items")
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
    if isinstance(mtx[-1], bytes):
        stdin = mtx[-1]
        mtx = mtx[:-1]
    cmd.extend(mtx)
    result = sp.run(cmd, check=True, input=stdin, capture_output=True)
    if _stdout:
        return result.stdout
    return None


@handle_called_process_error
def getinfo(
    *inputs: tuple[str | Path | bytes, ...],
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
        cmd.extend(map(str, inputs))
    return sp.run(cmd, input=stdin, capture_output=True, check=True).stdout


def get_image_dimensions(image: str | Path | bytes) -> tuple[int, int]:
    """Get the dimensions of an image.

    Args:
        image: image file path or image bytes

    Returns:
        Tuple[int, int]: width and height
    """
    output = getinfo(image, dimension_only=True).decode().split()
    return int(output[3]), int(output[1])


@handle_called_process_error
def get_header(inp: str | Path | bytes, dimension: bool = False) -> bytes:
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
    inp: str | Path,
    view: None | str = None,
    dryrun: bool = False,
    update: bool = False,
    silent: bool = False,
    varstr: None | list[str] = None,
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
    if view:
        cmd.extend(["-v", view])
    cmd.append(str(inp))
    if varstr is not None:
        cmd.extend(varstr)
    return sp.run(cmd, stdout=sp.PIPE, check=True).stdout


def read_rad(fpath: str) -> list[Primitive]:
    """Parse a Radiance file.

    Args:
        fpath: Path to the .rad file

    Returns:
        A list of primitives
    """
    with open(fpath) as rdr:
        lines = rdr.readlines()
    if any(line.startswith("!") for line in lines):
        lines = Xform(fpath)().decode().splitlines()
    return parse_primitive("\n".join(lines))


@handle_called_process_error
def rcode_depth(
    inp: str | Path | bytes,
    ref_depth: str = "1.0",
    inheader: bool = True,
    outheader: bool = True,
    inresolution: bool = True,
    outresolution: bool = True,
    xres: None | int = None,
    yres: None | int = None,
    inform: FileType = "a",
    outform: FileType = "a",
    decode: bool = False,
    compute_intersection: bool = False,
    per_point: bool = False,
    depth_file: None | str = None,
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
    inp: str | Path | bytes,
    index_size: int = 16,
    sep: str = "\n",
    decode: bool = False,
    header: bool = True,
    xres: None | int = None,
    yres: None | int = None,
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
    inp: str | Path | bytes,
    inheader: bool = True,
    outheader: bool = True,
    inresolution: bool = True,
    outresolution: bool = True,
    xres: None | int = None,
    yres: None | int = None,
    inform: FileType = "a",
    outform: FileType = "a",
    decode: bool = False,
    per_point: bool = False,
    norm_file: None | str = None,
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


class Rcomb:
    def __init__(
        self,
        transform: None | str = None,
        transform_all: None | str = None,
        source: None | str = None,
        expression: None | str = None,
        concat: None | Sequence[str] = None,
        outform: None | FileType = None,
        header: bool = True,
        silent: bool = False,
    ):
        """Combine multiple rasters.

        Args:
            transform: transform
            transform_all: transform all
            source: source
            expression: expression
            concat: concat
            outform: output format
            header: include header
            silent: suppress output
        """
        cmd = [str(BINPATH / "rcomb")]
        stdin: None | bytes = None
        if not header:
            cmd.append("-h")
        if silent:
            cmd.append("-w")
        if expression is not None:
            cmd.extend(["-e", expression])
        if concat is not None:
            for c in concat:
                cmd.extend(["-m", c])
        if transform_all is not None:
            cmd.extend(["-C", transform_all])
        if source is not None:
            cmd.extend(["-f", source])
        if outform:
            cmd.append(f"-f{outform}")
        if transform is not None:
            cmd.extend(["-c", transform])
        self.cmd = cmd
        self.stdin = stdin

    def add_input(
        self,
        input: str | Path | bytes,
        transform: None | str = None,
        scale: None | Sequence[float] = None,
    ) -> "Rcomb":
        """Insert commands for inputs

        Args:
            input: input can be file path or bytes
            transform: transform string
            scale: sequence of scaling factors

        Returns:
            self
        """
        if transform is not None:
            self.cmd.extend(["-c", transform])
        if scale is not None:
            self.cmd.append("-s")
            self.cmd.extend(map(str, scale))
        if isinstance(input, bytes):
            if self.stdin is not None:
                raise ValueError("Only one bytes input allowed")
            self.stdin = input
            self.cmd.append("-")
        elif isinstance(input, (str, Path)):
            self.cmd.append(str(input))
        else:
            raise TypeError("inp must be a string, Path, or bytes")
        return self

    @handle_called_process_error
    def __call__(self) -> bytes:
        return sp.run(self.cmd, input=self.stdin, check=True, stdout=sp.PIPE).stdout


def render(
    scene: Scene,
    view: None | View = None,
    quality: str = "Medium",
    variability: str = "Medium",
    detail: str = "Medium",
    nproc: int = 1,
    ncssamp: int = 3,
    resolution: None | tuple[int, int] = None,
    ambbounce: int = 0,
    ambcache: bool = True,
    params: None | RayParams = None,
) -> bytes:
    """Render a scene.

    Args:
        scene: Scene object.
        quality: Quality level.
        variability: Variability level.
        detail: Detail level.
        nproc: Number of processes to use.
        ncssamp: Number of channels to sample
        ambbounce: Number of ambient bounces.
        ambcache: Use ambient cache.
        params: Sampling parameters.

    Returns:
        tuple[bytes, int, int]: output of render, width, height
    """
    nproc = 1 if os.name == "nt" else nproc
    scenestring = ""
    for _, srf in scene.surfaces.items():
        if not isinstance(srf, Primitive):
            scenestring += f' "{srf}"'
    materialstring = ""
    for _, mat in scene.materials.items():
        if not isinstance(mat, Primitive):
            materialstring += f' "{mat}"'
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
        (aview.vp[0] - (xmax + xmin) / 2) ** 2
        + (aview.vp[1] - (ymax + ymin) / 2) ** 2
        + (aview.vp[2] - (zmax + zmin) / 2) ** 2
    )
    if view_center > distance:
        zone = f"E {xmin} {xmax} {ymin} {ymax} {zmin} {zmax}"
    else:
        zone = f"I {xmin} {xmax} {ymin} {ymax} {zmin} {zmax}"

    fd, optpath = tempfile.mkstemp()
    os.close(fd)
    radvars = [
        f"ZONE={zone}",
        f"OCTREE={scene.octree}",
        f"scene={scenestring}",
        f"materials={materialstring}",
        f"QUALITY={quality}",
        f"VARIABILITY={variability}",
        f"DETAIL={detail}",
        f"render= {' '.join(rad_render_options)}",
        f"OPT= {optpath}",
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
    rad(os.devnull, dryrun=True, varstr=radvars).decode().splitlines()
    with open(optpath) as f:
        param_strs = f.read().strip().replace("\n", " ").split()
    os.remove(optpath)
    scene.build()
    specout = ncssamp > 3
    if specout:
        param_strs.append("-co+")
    if params is not None:
        param_strs.extend(get_ray_params_args(params))
    vargs = get_view_args(aview)
    res = vwrays(view=vargs, dimensions=True, xres=xres, yres=yres).decode().split()
    xres, yres = int(res[1]), int(res[3])
    if not specout and nproc == 1:
        return rpict(
            vargs, scene.octree, params=["-ps", "1"] + param_strs, xres=xres, yres=yres
        )
    if nproc > 1 and ambbounce > 0 and ambcache:
        # straight picture output, so just shuffle sample order
        if not specout:
            ord = cnt(xres, yres, shuffled=True)
            pix = rtrace(
                octree=scene.octree,
                rays=vwrays(view=vargs, outform="f", pixpos=ord, xres=xres, yres=yres),
                inform="f",
                outform="a",
                outspec="v",
                nproc=nproc,
                params=param_strs,
            )
            header = getinfo(
                getinfo(get_header(pix), replace="NCOMP"),
                append=f"VIEW={' '.join(vargs)}",
            )
            rlam = b"\n".join(
                o + b"\t" + p
                for o, p in zip(ord.splitlines(), strip_header(pix).splitlines())
            )
            content = sp.run(
                ["sort", "-k2rn", "-k1n"], input=rlam, check=True, stdout=sp.PIPE
            ).stdout
            return pvaluer(header + content, yres=yres, xres=xres)
        # else randomize overture calculation to prime ambient cache
        oxres, oyres = int(xres / 6), int(yres / 6)
        rtrace(
            octree=scene.octree,
            inform="f",
            params=param_strs,
            nproc=nproc,
            rays=vwrays(
                view=vargs,
                outform="f",
                pixpos=cnt(oxres, oyres, shuffled=True),
                xres=oxres,
                yres=oyres,
            ),
        )

    return getinfo(
        rtrace(
            octree=scene.octree,
            params=param_strs,
            rays=vwrays(
                view=vargs,
                outform="f",
                xres=xres,
                yres=yres,
            ),
            inform="f",
            outform="c",
            nproc=nproc,
            xres=xres,
            yres=yres,
        ),
        append=f"VIEW={' '.join(vargs)}",
    )


@handle_called_process_error
def rfluxmtx(
    receiver: str | Path,
    surface: None | str | Path = None,
    rays: None | bytes = None,
    params: None | Sequence[str] = None,
    octree: None | Path | str = None,
    scene: None | Sequence[Path | str] = None,
) -> bytes:
    """Run rfluxmtx command.

    Args:
        receiver: receiver file path
        surface: input surface file path, mutually exclusive with rays
        rays: input rays bytes, mutually exclusive with surface
        params: ray tracing parameters
        octree: octree file path
        scene: list of scene files

    Returns:
        The results of rfluxmtx in bytes
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
        if os.name == "nt":
            cmd.extend(f'"{str(s)}"' for s in scene)
        else:
            cmd.extend(str(s) for s in scene)
    return sp.run(cmd, check=True, stdout=sp.PIPE, input=rays).stdout


# TODO: update to latest rmtxop interface
@handle_called_process_error
def rmtxop(
    inp: str | Path | bytes,
    outform: FileType = "a",
    transpose: bool = False,
    scale: None | float = None,
    transform: None | str | Sequence[float] = None,
    reflectance: None | str = None,
) -> bytes:
    """Run rmtxop command.

    Args:
        inp: input
        outform: output format: 'a', 'f', 'd', 'c'
        transpose: whether to transpose matrix
        scale: scaling factor
        transform: transform factors for each channel

    Returns:
        The results of rmtxop in bytes
    """
    cmd = [str(BINPATH / "rmtxop")]
    stdin = None
    if transpose:
        cmd.append("-t")
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


class Rmtxop:
    def __init__(self, outform: FileType = "a", color: None | str = None):
        self.cmd = [str(BINPATH / "rmtxop")]
        self.stdin = None
        self.cmd.append(f"-f{outform}")
        if color is not None:
            self.cmd.extend(["-C", color])
        self.nparts = 0

    def add_input(
        self,
        input_data: str | Path | bytes,
        op: Ops = ".",
        scale: None | float | Sequence[float] = None,
        transform: None | str | Sequence[float] = None,
        transpose: bool = False,
        refl_side: None | str = None,
        color: None | str = None,
    ):
        if self.nparts > 1:
            self.cmd.append(op)
        if scale is not None:
            self.cmd.append("-s")
            if isinstance(scale, (int, float)):
                self.cmd.append(str(scale))
            else:
                self.cmd.extend(map(str, scale))
        if refl_side is not None:
            self.cmd.append(f"r{refl_side[0]}")
        if transpose is not None:
            self.cmd.append("-t")
        if transform is not None:
            self.cmd.append("-c")
            if isinstance(transform, str):
                self.cmd.append(transform)
            else:
                self.cmd.extend(map(str, transform))
        elif color is not None:
            self.cmd.extend(["-C", color])
        if isinstance(input_data, bytes):
            if self.stdin is None:
                self.stdin = input_data
                self.cmd.append("-")
            else:
                raise ValueError("stdin is already taken")
        else:
            self.cmd.append(str(input_data))
        self.nparts += 1
        return self

    @handle_called_process_error
    def __call__(self) -> bytes:
        return sp.run(self.cmd, check=True, input=self.stdin, stdout=sp.PIPE).stdout


@handle_called_process_error
def rsensor(
    sensor: Sequence[str | Path],
    sensor_view: None | Sequence[str | Path] = None,
    direct_ray: None | Sequence[int] = None,
    ray_count: None | Sequence[int] = None,
    octree: None | str | Path = None,
    nproc: int = 1,
    params: None | Sequence[str] = None,
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
        if (direct_ray is not None) and octree is not None:
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
def strip_header(inp: bytes) -> bytes:
    """Use getinfo to strip the header from a Radiance file."""
    cmd = [str(BINPATH / "getinfo"), "-"]
    if isinstance(inp, bytes):
        stdin = inp
    else:
        raise TypeError("Input must be bytes")
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout


@handle_called_process_error
def vwrays(
    pixpos: None | bytes = None,
    unbuf: bool = False,
    outform: FileType = "a",
    ray_count: int = 1,
    pixel_jitter: float = 0,
    pixel_diameter: float = 0,
    pixel_aspect: float = 1,
    xres: int = 512,
    yres: int = 512,
    dimensions: bool = False,
    view: None | Sequence[str] = None,
    pic: None | Path = None,
    zbuf: None | Path = None,
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
    view: View,
    distance: float = 0,
) -> bytes:
    """Run vwright."""
    cmd = [str(BINPATH / "vwright")]
    cmd.extend(get_view_args(view))
    cmd.append(str(distance))
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


class WrapBSDF:
    def __init__(
        self,
        inxml: None | str | Path = None,
        enforce_window: bool = False,
        comment: None | str = None,
        correct_solid_angle: bool = False,
        basis: None | str = None,
        unlink: bool = False,
        unit: None | str = None,
        geometry: None | str = None,
        **kwargs: str | float,
    ):
        """Initialize wrapper operation of BSDF data into XML

        Args:
            inxml: input xml file
            enforce_window: Enforcing LBNL Window XML schema,
            comment: additional comment to add to XML,
            correct_solid_angle: Correct the input BSDF by solid angles,
            basis: BSDF basis to use, "kf", "kh", "kq",
            unlink: Whether to remove input file after creating XML file,
            unit: BSDF geometry unit,
            geometry: Whether to include geometry in XML,
            **kwargs: Additional tags to be passed into XML
        """
        self.has_visible = False
        self.has_solar = False
        self.cmd = [str(BINPATH / "wrapBSDF")]
        if enforce_window:
            self.cmd.append("-W")
        if correct_solid_angle:
            self.cmd.append("-c")
        if basis:
            self.cmd.extend(["-a", basis])
        if unlink:
            self.cmd.append("-U")
        if unit:
            self.cmd.extend(["-u", unit])
        if comment:
            self.cmd.extend(["-C", comment])
        if geometry:
            self.cmd.extend(["-g", geometry])
        fields_keys = ["n", "m", "d", "c", "ef", "eb", "eo", "tir", "t", "h", "w"]
        fields = []
        for key in fields_keys:
            if key in kwargs:
                fields.append(f"{key}={kwargs[key]}")
        if fields:
            self.cmd.extend(["-f", ";".join(fields)])
        if inxml is not None:
            self.cmd.append(str(inxml))

    def _add_spectrum(
        self,
        spectrum: SpectrumTag,
        tb: None | str = None,
        tf: None | str = None,
        rb: None | str = None,
        rf: None | str = None,
    ):
        arglist = ["-s", spectrum]
        if tf:
            arglist.extend(["-tf", str(tf)])
        if tb:
            arglist.extend(["-tb", str(tb)])
        if rf:
            arglist.extend(["-rf", str(rf)])
        if rb:
            arglist.extend(["-rb", str(rb)])
        if len(arglist) == 2:
            print("At least one of tf, tb, rf, rb should be provided for", spectrum)
            return self
        self.cmd.extend(arglist)
        return self

    def add_visible(
        self,
        tb: None | str = None,
        tf: None | str = None,
        rb: None | str = None,
        rf: None | str = None,
    ) -> "WrapBSDF":
        """Insert commands for visible data

        Args:
            tb: back transmittance file
            tf: front transmittance file
            rb: back reflectance file
            rf: front reflectance file

        Returns:
            self
        """
        self.has_visible = True
        return self._add_spectrum("Visible", tb=tb, tf=tf, rb=rb, rf=rf)

    def add_solar(
        self,
        tb: None | str = None,
        tf: None | str = None,
        rb: None | str = None,
        rf: None | str = None,
    ) -> "WrapBSDF":
        """Insert commands for solar data

        Args:
            tb: back transmittance file
            tf: front transmittance file
            rb: back reflectance file
            rf: front reflectance file

        Returns:
            self
        """
        self.has_solar = True
        return self._add_spectrum("Solar", tb=tb, tf=tf, rb=rb, rf=rf)

    @handle_called_process_error
    def _execute(self) -> bytes:
        if not self.has_visible and not self.has_solar:
            raise ValueError("Need to specify at least solar or visible data")
        return sp.run(self.cmd, check=True, stdout=sp.PIPE).stdout

    def __call__(self) -> bytes:
        return self._execute()


class Xform:
    def __init__(
        self,
        inp: str | Path | bytes,
        expand_cmd: bool = True,
        invert: bool = False,
        iprefix: None | str = None,
        modifier: None | str = None,
    ):
        """Initialize a transformation operation of a RADIANCE scene description

        Args:
            inp: Input file or bytes
            expand_cmd: Set to True to expand command
            iprefix: Prefix identifier
            modifier: Set surface modifier to this name
            invert: Invert surface normal
        """
        self.inp = inp
        self.stdin: None | bytes = None
        self.args = [str(BINPATH / "xform")]
        if not expand_cmd:
            self.args.append("-c")
        if iprefix is not None:
            self.args.extend(["-n", iprefix])
        if modifier is not None:
            self.args.extend(["-m", modifier])
        if invert:
            self.args.append("-I")

    def translate(self, x: float, y: float, z: float) -> "Xform":
        """Insert translate command.

        Args:
            x: translation in x coordinate
            y: translation in y coordinate
            z: translation in z coordinate

        Returns:
            self
        """
        self.args.extend(["-t", str(x), str(y), str(z)])
        return self

    def rotatex(self, deg: float) -> "Xform":
        """Insert rotation around x axis command.

        Args:
            deg: rotation in degree

        Returns:
            self
        """
        self.args.extend(["-rx", str(deg)])
        return self

    def rotatey(self, deg: float) -> "Xform":
        """Insert rotation around x axis command.

        Args:
            deg: rotation in degree

        Returns:
            self
        """
        self.args.extend(["-ry", str(deg)])
        return self

    def rotatez(self, deg: float) -> "Xform":
        """Insert rotation around x axis command.

        Args:
            deg: rotation in degree

        Returns:
            self
        """
        self.args.extend(["-rz", str(deg)])
        return self

    def scale(self, ratio: float) -> "Xform":
        """Insert scaling command.

        Args:
            ratio: scaling factor

        Returns:
            self
        """
        self.args.extend(["-s", str(ratio)])
        return self

    def mirrorx(self) -> "Xform":
        """Insert mirror about yz plane command.

        Returns:
            self
        """
        self.args.append("-mx")
        return self

    def mirrory(self) -> "Xform":
        """Insert mirror about xz plane command.

        Returns:
            self
        """
        self.args.append("-my")
        return self

    def mirrorz(self) -> "Xform":
        """Insert mirror about xy plane command.

        Returns:
            self
        """
        self.args.append("-mz")
        return self

    def array(self, number: int) -> "Xform":
        """Insert array command.

        Args:
            number: array number

        Returns:
            self
        """
        self.args.extend(["-a", str(number)])
        return self

    def iterate(self, number: int) -> "Xform":
        """Insert iterate command.

        Args:
            number: iterate number

        Returns:
            self
        """
        self.args.extend(["-i", str(number)])
        return self

    @handle_called_process_error
    def _execute(self):
        if isinstance(self.inp, bytes):
            self.stdin = self.inp
        else:
            self.args.append(str(self.inp))
        return sp.run(self.args, check=True, input=self.stdin, stdout=sp.PIPE).stdout

    def __call__(self):
        return self._execute()


def load_material_smd(
    file: Path, roughness: float = 0.0, spectral: bool = False, metal: bool = False
) -> list[Primitive]:
    """Generate Radiance primitives from csv file from spectral
    material database (spectraldb.com).

    Args:
        file: Path to .csv file
        roughness: Roughtness of material
        spectral: Output spectral primitives
        metal: Whether material is metal

    Returns:
        A list of primitives
    """

    primitives: list[Primitive] = []

    mmod: str = "void"
    specular: float = 0.0
    mid: str = file.stem.replace(" ", "_")
    wvls: list[float] = []
    scis: list[float] = []
    sces: list[float] = []

    with open(file, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            wvl, sci, sce = map(float, row)
            wvls.append(wvl)
            scis.append(sci / 100.0)
            sces.append(sce / 100.0)

    min_wvl = min(wvls)
    max_wvl = max(wvls)

    sce_cie = spec_xyz(sces, min_wvl, max_wvl)
    if all(scis):
        sci_cie = spec_xyz(scis, min_wvl, max_wvl)
        specular = sci_cie[1] - sce_cie[1]

    mfargs: list[float] = []
    pfargs: list[float] = []
    if spectral:
        pid = f"{mid}_spectrum"
        mmod = pid
        pfargs.extend([min_wvl, max_wvl])
        pfargs.extend(sces)
        pp = Primitive("void", "spectrum", pid, [], pfargs)
        mfargs.extend([1.0, 1.0, 1.0, specular, roughness])
        primitives.append(pp)
    else:
        rgb = xyz_rgb(*sce_cie)
        mfargs.extend(rgb)
        mfargs.extend([specular, roughness])

    primitives.append(Primitive(mmod, "metal" if metal else "plastic", mid, [], mfargs))
    return primitives


def parse_primitive(pstr: str | bytes) -> list[Primitive]:
    """Parse Radiance primitives inside a file path into a list of dictionary.

    Args:
        pstr: A string of Radiance primitives.

    Returns:
        list of primitives
    """
    if isinstance(pstr, bytes):
        pstr = pstr.decode()
    res = []
    tokens = re.sub(r"#.+?\n", "", pstr).strip().split()
    itokens = iter(tokens)
    for t in itokens:
        modifier, ptype, identifier = t, next(itokens), next(itokens)
        nsarg = next(itokens)
        sarg = [next(itokens) for _ in range(int(nsarg))]
        next(itokens)
        nrarg = next(itokens)
        rarg = [float(next(itokens)) for _ in range(int(nrarg))]
        res.append(Primitive(modifier, ptype, identifier, sarg, rarg))
    return res
