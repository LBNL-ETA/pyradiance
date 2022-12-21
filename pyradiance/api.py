"""
pyradiance.api 
=============
This module contains the main API for pyradiance.

"""

import datetime
from pathlib import Path
import os
import shlex
import subprocess as sp
import sys
from typing import List, Optional, Union, Tuple, Sequence

from .parameter import Levels, SamplingParameters
from .model import Modifier, Primitive, Scene, View
from .parsers import parse_rtrace_args


BINPATH = Path(__file__).parent / "bin"


def append_to_header(inp: bytes, appendage: str) -> bytes:
    """Use getinfo to append a line to the header of a Radiance file.
    Args:
        inp: input file
        appendage: line to append
    Returns:
        bytes: output of getinfo
    """
    return getinfo(inp, append=appendage)


def build_scene(scene: Scene):
    """Build and write the scene octree file.
    to the current working directory.
    """
    if not scene.changed:
        print("Scene has not changed since last build.")
        return
    scene.changed = False
    stdin = None
    mstdin = [
        str(mat) for mat in scene.materials.values() if isinstance(mat, Primitive)
    ]
    inp = [mat for mat in scene.materials.values() if isinstance(mat, str)]
    if mstdin:
        stdin = "".join(mstdin).encode()
    moctname = f"{scene.sid}mat.oct"
    with open(moctname, "wb") as wtr:
        wtr.write(oconv(*inp, warning=False, stdin=stdin))
    sstdin = [str(srf) for srf in scene.surfaces.values() if isinstance(srf, Primitive)]
    sstdin.extend(
        [str(src) for src in scene.sources.values() if isinstance(src, Primitive)]
    )
    inp = [path for path in scene.surfaces.values() if isinstance(path, str)]
    inp.extend([path for path in scene.sources.values() if isinstance(path, str)])
    if sstdin:
        stdin = "".join(sstdin).encode()
    with open(f"{scene.sid}.oct", "wb") as wtr:
        wtr.write(oconv(*inp, stdin=stdin, warning=False, octree=moctname))


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


def gen_bsdf():
    pass


def rtpict():
    pass


def gendaylit(
    dt,
    latitude: float,
    longitude: float,
    timezone: int,
    year: Optional[int] = None,
    dirnorm: Optional[float] = None,
    diffhor: Optional[float] = None,
    dirhor: Optional[float] = None,
    dirnorm_illum: Optional[float] = None,
    diffhor_illum: Optional[float] = None,
    solar: bool = False,
    sky_only: bool = False,
    silent: bool = False,
    grefl: Optional[float] = None,
    interval: Optional[int] = None,
) -> bytes:
    """Generate sky from Perez all-weather model.

    Args:
        dt: datetime object
        latitude: latitude
        longitude: longitude
        timezone: timezone
        year: year
        dirnorm: direct normal irradiance
        diffhor: diffuse horizontal irradiance
        dirhor: direct horizontal irradiance, either this or dirnorm
        dirnormp: direct normal illuminance
        diffhorp: diffuse horizontal illuminance
        solar: if True, include solar position
    Returns:
        str: output of gendaylit
    """
    cmd = [
        str(BINPATH / "gendaylit"),
        str(dt.month),
        str(dt.day),
        str(dt.hour + dt.minute / 60 + dt.second / 3600),
        "-a",
        str(latitude),
        "-o",
        str(longitude),
        "-m",
        str(timezone),
    ]
    if year is not None:
        cmd.extend(["-y", str(year)])
    if None not in (dirnorm, diffhor):
        cmd.extend(["-W", str(dirnorm), str(diffhor)])
    elif None not in (dirhor, diffhor):
        cmd.extend(["-G", str(dirhor), str(diffhor)])
    elif None not in (dirnorm_illum, diffhor_illum):
        cmd.extend(["-L", str(dirnorm_illum), str(diffhor_illum)])
    if solar:
        cmd.extend(["-O", "1"])
    if sky_only:
        cmd.append("-s")
    if silent:
        cmd.append("-w")
    if grefl is not None:
        cmd.extend(["-g", str(grefl)])
    if interval is not None:
        cmd.extend(["-i", str(interval)])
    return sp.run(cmd, stdout=sp.PIPE, check=True).stdout


def gendaymtx(
    weather_data,
    verbose: bool = False,
    header: bool = False,
    average: bool = False,
    sun_only: bool = False,
    sky_only: bool = False,
    sun_file: Optional[str] = None,
    sun_mods: Optional[str] = None,
    daylight_hours_only: bool = False,
    dryrun: bool = False,
    sky_color: Optional[List[float]] = None,
    ground_color: Optional[List[float]] = None,
    rotate: Optional[float] = None,
    outform: Optional[str] = None,
    onesun: bool = False,
    solar_radiance: bool = False,
    mfactor: int = 1,
):
    """
    Use gendaymtx to generate a daylight matrix.
    gendaymtx [ -v ][ -h ][ -A ][ -d|-s|-n ][ -u ][ -D sunfile [ -M sunmods ]][ -r deg ][ -m N ][ -g r g b ][ -c r g b ][ -o{f|d} ][ -O{0|1} ] [ tape.wea ]

    Args:
        weather_data: weather data
        mf: multiplication factor
    Returns:
        bytes: output of gendaymtx
    """
    stdin = None
    cmd = [str(BINPATH / "gendaymtx")]
    cmd.extend(["-m", str(mfactor)])
    if verbose:
        cmd.append("-v")
    if not header:
        cmd.append("-h")
    if average:
        cmd.append("-A")
    if sun_only:
        cmd.append("-d")
    elif sky_only:
        cmd.append("-s")
    if onesun:
        cmd.extend(["-5", ".533"])
    if sky_color:
        cmd.extend(["-c", *[str(i) for i in sky_color]])
    if ground_color:
        cmd.extend(["-g", *[str(i) for i in ground_color]])
    if dryrun:
        cmd.append("-n")
    if daylight_hours_only:
        cmd.append("-u")
    if solar_radiance:
        cmd.append("-O1")
    if sun_file is not None:
        cmd.extend(["-D", sun_file])
    if sun_mods is not None:
        cmd.extend(["-M", sun_mods])
    if rotate is not None:
        cmd.extend(["-r", str(rotate)])
    if outform is not None:
        cmd.append(f"-o{outform}")
    if isinstance(weather_data, bytes):
        cmd.append("-")
        stdin = weather_data
    elif isinstance(weather_data, (str, Path)):
        cmd.append(str(weather_data))
    else:
        raise TypeError("weather_data must be a string, Path, or bytes")
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout


def gen_perez_sky(
    dt,
    latitude: float,
    longitude: float,
    timezone: int,
    year: Optional[int] = None,
    dirnorm: Optional[float] = None,
    diffhor: Optional[float] = None,
    dirhor: Optional[float] = None,
    dirnorm_illum: Optional[float] = None,
    diffhor_illum: Optional[float] = None,
    solar: bool = False,
    grefl: Optional[float] = None,
    rotate: Optional[float] = None,
) -> bytes:
    sun = gendaylit(
        dt,
        latitude,
        longitude,
        timezone,
        year,
        dirnorm=dirnorm,
        diffhor=diffhor,
        dirhor=dirhor,
        dirnorm_illum=dirnorm_illum,
        diffhor_illum=diffhor_illum,
        solar=solar,
        grefl=grefl,
    )
    if rotate:
        sun = xform(sun, rotatez=rotate)
    out = [b"skyfunc glow sglow 0 0 4 1 1 1 0"]
    out.append(b"sglow source sky 0 0 4 0 0 1 180")
    out.append(b"sglow source ground 0 0 4 0 0 -1 180")
    return sun + b"\n".join(out)


def gensky(
    dt,
    latitude: float,
    longitude: float,
    timezone: int,
    year: Optional[int] = None,
    dirnorm: Optional[float] = None,
    diffhor: Optional[float] = None,
    dirhor: Optional[float] = None,
    dirnormp: Optional[float] = None,
    diffhorp: Optional[float] = None,
    solar: bool = False,
) -> str:
    """Generate sky from Perez all-weather model."""
    cmd = [
        str(BINPATH / "gensky"),
        str(dt.month),
        str(dt.day),
        str(dt.hour + dt.minute / 60),
    ]
    cmd += ["-a", latitude, "-o", longitude, "-m", timezone]
    if year is not None:
        cmd += ["-y", year]
    if None not in (dirnorm, diffhor):
        cmd += ["-W", str(dirnorm), str(diffhor)]
    if None not in (dirhor, diffhor):
        cmd += ["-G", str(dirhor), str(diffhor)]
    if None not in (dirnormp, diffhorp):
        cmd += ["-L", str(dirnormp), str(diffhorp)]
    if solar:
        cmd += ["-O", "1"]
    return sp.run(cmd, stdout=sp.PIPE, check=True).stdout.decode().strip()


def genwea(
    datetimes: Sequence[datetime.datetime],
    dirnorm: Sequence[float],
    diffhor: Sequence[float],
    latitude: float,
    longitude: float,
    timezone: int,
    elevation: Optional[float] = None,
    location: Optional[str] = None,
) -> bytes:
    """Generate wea file from datetime, location, and sky."""
    if len(datetimes) != len(dirnorm) != len(diffhor):
        raise ValueError("datetimes, dirnorm, and diffhor must be the same length")
    rows = []
    if location is None:
        location = "_".join(
            [str(i) for i in [latitude, longitude, timezone, elevation]]
        )
    if elevation is None:
        elevation = 0
    rows.append(f"place {location}".encode())
    rows.append(f"latitude {latitude}".encode())
    rows.append(f"longitude {longitude}".format())
    rows.append(f"timezone {timezone}".encode())
    rows.append(f"elevation {elevation}".encode())
    rows.append(b"weather_data_file_units 1")
    for dt, dni, dhi in zip(datetimes, dirnorm, diffhor):
        _hrs = dt.hour + dt.minute / 60 + 0.5  # middle of hour
        _row = f"{dt.month} {dt.day} {_hrs} {dni} {dhi}"
        rows.append(_row.encode())
    return b"\n".join(rows)


def getinfo(
    *inputs: Union[str, Path, bytes],
    dimension_only: bool = False,
    dimension: bool = False,
    replace: str = "",
    append: str = "",
    command: str = "",
) -> bytes:
    """Get header information from a Radiance file."""
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
    else:
        if any(isinstance(i, bytes) for i in inputs):
            raise TypeError("All inputs must be str or Path if one is")
        cmd.extend([str(i) for i in inputs])
    return sp.run(cmd, input=stdin, stdout=sp.PIPE, check=True).stdout


def get_image_dimensions(image: Union[str, Path, bytes]) -> Tuple[int, int]:
    """Get the dimensions of an image."""
    output = getinfo(image, dimension_only=True).decode().split()
    return int(output[3]), int(output[1])


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


def getbbox(
    *path,
    header: bool = False,
) -> List[float]:
    """Get axis-aligned bounding box of a Radiance scene.
    Args:
        path: path to Radiance scene
        header: include header
    Returns:
        list: bounding box
    """
    cmd = [str(BINPATH / "getbbox")]
    if not header:
        cmd.append("-h")
    cmd.extend(path)
    proc = sp.run(cmd, check=True, stdout=sp.PIPE)
    return [float(x) for x in proc.stdout.split()]


def obj2rad(
    inp,
    quallist: bool = False,
    flatten: bool = False,
    mapfile: Optional[str] = None,
    objname: Optional[str] = None,
) -> bytes:
    """Convert a Wavefront .obj file to Radiance format."""
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
    if stdin:
        if isinstance(stdin, bytes):
            cmd.append("-")
        else:
            raise TypeError("stdin should be bytes.")
    cmd.extend(paths)
    return sp.run(cmd, input=stdin, stdout=sp.PIPE, check=True).stdout


def pcond(
    hdr: Path,
    human: bool = False,
    acuity: bool = False,
    veiling: bool = False,
    sense: bool = False,
    closs: bool = False,
    center_weighted: bool = False,
    linear: bool = False,
    fixfrac: float = 0.0,
    fixpoints: Optional[List[tuple]] = None,
    histo: str = "",
    expval: str = "",
    ldmax: float = 100.0,
    lddyn: float = 100.0,
    primaries: Optional[List[float]] = None,
    macbeth: str = "",
    mapfile: str = "",
) -> bytes:
    """
    Condition a Radiance picture.

    Args:
        hdr: input hdr
        human: Mimic human visual response. This is the same as turning on all acuity,
            veiling, sensitivity, and color loss.
        acuity: Defocus darker region.
        veiling: Add veiling glare.
        sense: Use human contrast sensitivity, simulating eye internal scattering.
        center_weighted: Use center-weighted average for acuity and veiling.
        linear: Use a linear reponse function instead of the standard dynamic range
            compression. This preseves the extremas.
        fixfrac: Fixation fraction for acuity and veiling.
        histo: Histogram file for acuity and veiling.
        expval: Exposure value for acuity and veiling.
        ldmax: Maximum luminance for acuity and veiling.
        lddyn: Luminance dynamic range for acuity and veiling.
        primaries: Color primaries for color loss.
        macbeth: Macbeth chart file for color loss.
        mapfile: Color map file for color loss.
    Returns:
        bytes: output of pcond
    """
    stdin = None
    cmd = [str(BINPATH / "pcond")]
    if human:
        cmd.append("-h")
    else:
        if acuity:
            cmd.append("-a")
        if veiling:
            cmd.append("-v")
        if sense:
            cmd.append("-s")
        if closs:
            cmd.append("-c")
    if linear:
        cmd.append("-l")
    if center_weighted:
        cmd.append("-w")
    if fixfrac > 0:
        if fixpoints is None:
            raise ValueError("fixfrac is set but fixpoints is not provided.")
        stdin = str(fixpoints).encode()
        cmd.extend(["-i", str(fixfrac)])
    elif histo:
        stdin = histo.encode()
        cmd.append("-I")
    if expval != "":
        cmd.extend(["-e", expval])
    if ldmax != 100:
        cmd.extend(["-u", str(ldmax)])
    if lddyn != 100:
        cmd.extend(["-d", str(lddyn)])
    if primaries is not None:
        cmd.extend(["-p", *(str(p) for p in primaries)])
    elif macbeth:
        cmd.extend(["-f", macbeth])
    if mapfile != "":
        cmd.extend(["-x", mapfile])
    if not isinstance(hdr, (str, Path)):
        raise TypeError("hdr should be a string or a Path.")
    cmd.append(str(hdr))
    return sp.run(cmd, input=stdin, stdout=sp.PIPE, check=True).stdout


def pfilt(
    image: Union[str, Path, bytes],
    xres: Optional[str] = None,
    yres: Optional[str] = None,
    pixel_aspect: Optional[float] = 0,
    exposure: Optional[float] = 0,
    lamp: Optional[str] = None,
    lampdat: Optional[str] = None,
    one_pass: bool = False,
    gaussian_filter_radius: Optional[float] = None,
    limitfrac: Optional[float] = None,
    hot_threshold: Optional[float] = None,
    star_points: Optional[int] = None,
    star_spread: Optional[float] = None,
    average_hot: bool = False,
) -> bytes:
    """filter a Radiance picture."""
    stdin = None
    cmd = [str(BINPATH / "pfilt")]
    if xres:
        cmd.extend(["-x", xres])
    if yres:
        cmd.extend(["-y", yres])
    if pixel_aspect:
        cmd.extend(["-p", str(pixel_aspect)])
    if exposure:
        cmd.extend(["-e", str(exposure)])
    if lamp:
        cmd.extend(["-t", lamp])
    if lampdat:
        cmd.extend(["-f", lampdat])
    if one_pass:
        cmd.append("-1")
    if gaussian_filter_radius:
        cmd.extend(["-r", str(gaussian_filter_radius)])
    if limitfrac:
        cmd.extend(["-m", str(limitfrac)])
    if hot_threshold:
        cmd.extend(["-h", str(hot_threshold)])
    if star_points:
        cmd.extend(["-n", str(star_points)])
    if star_spread:
        cmd.extend(["-s", str(star_spread)])
    if average_hot:
        cmd.append("-a")
    if isinstance(image, bytes):
        stdin = image
    elif isinstance(image, (str, Path)):
        cmd.append(str(image))
    else:
        raise TypeError("image should be a string, Path, or bytes.")
    return sp.run(cmd, input=stdin, stdout=sp.PIPE, check=True).stdout


def pvalue(
    pic: Union[Path, str, bytes],
    unique: bool = False,
    original: bool = False,
    header: bool = True,
    resstr: bool = True,
    skip: int = 0,
    exposure: int = 0,
    gamma: float = 1.0,
    dataonly: bool = False,
    outform: str = "",
    reverse_rgb: bool = False,
    interleaving: bool = True,
    brightness: bool = False,
    outprimary: Optional[str] = None,
) -> bytes:
    """Run Radiance pvalue tool.

    Args:
        pic: hdr file path. Either path or stdin is used, path takes precedence.
        unique: if True, only unique values will be returned
        original: if True, print original values, before exposure compensation
        header: if True, header will be returned
        resstr: if True, resolution string will be returned
        skip: number of bytes to skip
        exposure: exposure value
        gamma: gamma value
        dataonly: if True, only data will be returned
        outform: output data format
        reverse_rgb: if True, RGB values will be reversed
        interleaving: if True, interleaving will be used
        brightness: if True, only brightness will be returned
        outprimary: output color primaries
    Returns:
        bytes: output of pvalue
    """
    cmd = [str(BINPATH / "pvalue")]
    if unique:
        cmd.append("-u")
    if original:
        cmd.append("-o")
    if not header:
        cmd.append("-h")
    if not resstr:
        cmd.append("-H")
    if skip:
        cmd.extend(["-s", str(skip)])
    if exposure:
        cmd.extend(["-e", str(exposure)])
    if gamma:
        cmd.extend(["-g", str(gamma)])
    if dataonly:
        cmd.append("-d")
    if outform != "":
        cmd.append(f"-d{outform}")
    if reverse_rgb:
        cmd.append("-R")
    if not interleaving:
        cmd.append("-n")
    if brightness:
        cmd.append("-b")
    if outprimary:
        cmd.append("-p{outprimary}")
    if isinstance(pic, (Path, str)):
        cmd.append(str(pic))
        proc = sp.run(cmd, check=True, input=None, stdout=sp.PIPE)
    elif isinstance(pic, bytes):
        proc = sp.run(cmd, check=True, input=pic, stdout=sp.PIPE)
    else:
        raise ValueError("pic should be either a file path or bytes.")
    return proc.stdout


def pvaluer(
    pic: Union[Path, str, bytes],
    xres: Optional[int] = None,
    yres: Optional[int] = None,
    inpformat: str = "a",
    resstr: bool = True,
    dataonly: bool = False,
    header: bool = False,
    primaries: Optional[List[float]] = None,
    pxyz: bool = False,
) -> bytes:
    """
    Run Radiance pvalue tools reverse mode:
    constructing a image from pixel values.

    Args:
        pic: Path to Radiance picture file or bytes of the picture file.
        xres: Number of columns in the picture file.
        yres: Number of rows in the picture file.
        inpformat: Radiance picture file format. Default is "a" for ascii.
        header: Set to True if the picture file has a header. Default is False.
        primaries: List of primaries for XYZ calculation. Default is None.
        pxyz: Set to True to calculate XYZ values. Default is False.
    Returns:
        Bytes of the pvalue output (Radiance .
    """
    stdin = None
    cmd = [str(BINPATH / "pvalue"), "-r"]
    if not header:
        cmd.append("-h")
    if not resstr:
        cmd.append("-H")
    if dataonly:
        cmd.append("-d")
    if inpformat != "a":
        cmd.append(f"-d{inpformat}")
    if yres:
        sign = "-" if yres > 0 else "+"
        cmd.extend([f"{sign}y", str(abs(yres))])
    if xres:
        sign = "+" if xres > 0 else "-"
        cmd.extend([f"{sign}x", str(abs(xres))])
    if primaries:
        cmd.extend(["-p", *map(str, primaries)])
    if pxyz:
        cmd.append("-pXYZ")
    if isinstance(pic, (Path, str)):
        cmd.append(str(pic))
    elif isinstance(pic, bytes):
        stdin = pic
    return sp.run(cmd, check=True, stdout=sp.PIPE, input=stdin).stdout


def rad(
    inp,
    dryrun: bool = False,
    update: bool = False,
    silent: bool = False,
    varstr: Optional[List[str]] = None,
    cwd: Optional[Union[str, Path]] = None,
) -> bytes:
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
    return sp.run(cmd, cwd=cwd, stdout=sp.PIPE, check=True).stdout


def rcontrib(
    inp: bytes,
    octree: Union[Path, str],
    modifiers: List[Modifier],
    nproc=1,
    yres=None,
    inform=None,
    outform=None,
    params: Optional[SamplingParameters] = None,
) -> bytes:
    """
    Needs a wrapper for options.
    grouped by modifiers
    -n -V -c [ -fo | -r ]
    -e  -f
    -x -y -o -p -b -bn { -m | -M }
    [rtrace option]
    octree
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
        cmd.extend(params.args())
    cmd.append(str(octree))
    return sp.run(cmd, check=True, input=inp, stdout=sp.PIPE).stdout


def render(
    scene,
    view: Optional[View] = None,
    quality=Levels.MEDIUM,
    variability=Levels.MEDIUM,
    detail=Levels.MEDIUM,
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
    if radcmds[0].startswith("oconv"):
        print("rebuilding octree...")
        with open(octpath, "wb") as wtr:
            sp.run(shlex.split(radcmds[0].split(">", 1)[0]), check=True, stdout=wtr)
        argdict = parse_rtrace_args(radcmds[1])
    elif radcmds[0].startswith("rpict"):
        argdict = parse_rtrace_args(radcmds[0])
    elif radcmds[0].startswith("rm"):
        sp.run(shlex.split(radcmds[0]), check=True)
        argdict = parse_rtrace_args(radcmds[1])
    else:
        raise ValueError("rpict command not found.")

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

    if nproc == 1:
        # Use rpict instead
        options.ps = 1
        report = {"H": 10, "M": 5, "L": 1}[quality]
        return rpict(
            aview, octpath, xres=xres, yres=yres, report=report, options=options
        )
    else:
        # Use rtrace
        ambcache = True
        if options.aa is not None:
            if options.aa == 0:
                ambcache = False
        ambfile = options.af
        _, xres, _, yres = (
            vwrays(view=aview, xres=xres, yres=yres, pixeljitter=0.67, dimensions=True)
            .decode()
            .split()
        )
        xres, yres = int(xres), int(yres)
        if options.ab and ambcache and (ambfile is not None):
            # if quality != Levels.HIGH:
            #     ords = cnt(xres, yres, shuffled=True)
            #     pix = rtrace(
            #         vwrays(
            #             pixpos=ords,
            #             xres=xres,
            #             yres=yres,
            #             view=aview,
            #             outform="f",
            #             pixeljitter=0.67,
            #         ),
            #         str(octpath),
            #         nproc=nproc,
            #         xres=xres,
            #         yres=yres,
            #         inform="f",
            #         outform="a",
            #         outspec="v",
            #         options=options,
            #     )
            #     with tempfile.TemporaryDirectory() as tmpdir:
            #         ordpath = Path(tmpdir) / "ords.txt"
            #         with open(ordpath, "wb") as wtr:
            #             wtr.write(ords)
            #         shuffled_pixels = rlam(ordpath, strip_header(pix))
            #     # Using Linux sort to sort pixels, assuming no windows users reach this point
            #     sorted_pix = sp.run(
            #         ["sort", "-k2rn", "-k1n"],
            #         input=shuffled_pixels,
            #         stdout=sp.PIPE,
            #         check=True,
            #     ).stdout
            #     with open('temp.dat', 'wb') as wtr:
            #         wtr.write(append_to_header(get_header(pix), f"VIEW= {' '.join(aview.args())}"))
            #         wtr.write(sorted_pix)
            #     return pvaluer(
            #         append_to_header(get_header(pix), f"VIEW= {' '.join(aview.args())}")
            #         + sorted_pix,
            #         xres=xres,
            #         yres=yres,
            #     )
            # overture run
            oxres, oyres = xres // 6, yres // 6
            opix = rtrace(
                vwrays(
                    pixpos=cnt(oxres, oyres, shuffled=True),
                    xres=oxres,
                    yres=oyres,
                    view=aview,
                    outform="f",
                    pixeljitter=0,
                ),
                str(octpath),
                nproc=nproc,
                xres=oxres,
                yres=oyres,
                inform="f",
                outform="f",
                outspec="v",
                options=options,
            )
            del opix

        img = rtrace(
            vwrays(
                view=aview,
                xres=xres,
                yres=yres,
                outform="f",
                pixeljitter=0.67,
            ),
            str(octpath),
            nproc=nproc,
            inform="f",
            xres=xres,
            yres=yres,
            outform="c",
            options=options,
        )
        return append_to_header(img, f"VIEW= {' '.join(aview.args())}")


def rfluxmtx(
    receiver: Union[str, Path],
    view: Optional[View] = None,
    surface: Optional[Union[str, Path]] = None,
    rays: Optional[List[List[float]]] = None,
    option: Optional[List[str]] = None,
    octree: Optional[Path] = None,
    scene: Optional[Scene] = None,
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
    stdin = None
    cmd = [str(BINPATH / "rfluxmtx")]
    if option:
        cmd.extend(option)
    if surface is not None:
        cmd.append(str(surface))
    else:
        cmd.append("-")
        if view is not None:
            stdin = vwrays(view=view)
        elif rays is not None:
            stdin = (
                "\n".join([" ".join([str(i) for i in row]) for row in rays])
            ).encode()
        else:
            raise ValueError("Either view, surface or rays must be provided.")
    cmd.append(str(receiver))
    if octree is not None:
        cmd.extend(["-i", str(octree)])
    if scene is not None:
        for path in scene.materials:
            cmd.append(str(path))
        for path in scene.surfaces:
            cmd.append(str(path))
    return sp.run(cmd, check=True, stdout=sp.PIPE, input=stdin).stdout


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


def rpict(
    view,
    octree,
    xres: Optional[int] = None,
    yres: Optional[int] = None,
    report: float = 0,
    report_file: Optional[Path] = None,
    options=None,
) -> bytes:
    """Get rpict command.
    Args:
        view: A view object.
        octree: A path to octree file.
        options: A SamplingParameters object.
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
    if options:
        cmd.extend(options.args())
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
    options: Optional[SamplingParameters] = None,
    report: bool = False,
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
    if not isinstance(rays, bytes):
        raise TypeError("Rays must be bytes")
    cmd = [str(BINPATH / "rtrace")]
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
    if options is not None:
        cmd.extend(options.args())
    cmd.append(str(octree))
    return sp.run(cmd, check=True, stdout=sp.PIPE, input=rays).stdout


def strip_header(inp) -> bytes:
    """Use getinfo to strip the header from a Radiance file."""
    cmd = [str(BINPATH / "getinfo"), "-"]
    if isinstance(inp, bytes):
        stdin = inp
    else:
        raise TypeError("Input must be bytes")
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout


def vwrays(
    pixpos: Optional[bytes] = None,
    unbuf: bool = False,
    outform: str = "a",
    raycnt: int = 1,
    pixeljitter: float = 0,
    pixeldiameter: float = 0,
    pixelaspect: float = 1,
    xres: int = 512,
    yres: int = 512,
    dimensions: bool = False,
    view: Optional[View] = None,
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
    if raycnt != 1:
        cmd.extend(["-c", str(raycnt)])
    if pixeljitter != 0:
        cmd.extend(["-pj", str(pixeljitter)])
    if pixeldiameter != 0:
        cmd.extend(["-pd", str(pixeldiameter)])
    if pixelaspect != 1:
        cmd.extend(["-pa", str(pixelaspect)])
    if dimensions:
        cmd.append("-d")
    if xres != 512:
        cmd.extend(["-x", str(xres)])
    if yres != 512:
        cmd.extend(["-y", str(yres)])
    if view is not None:
        cmd.extend(view.args())
    elif pic is not None:
        cmd.append(str(pic))
        if zbuf is not None:
            cmd.append(str(zbuf))
    else:
        raise ValueError("Either view or pic should be provided.")
    return sp.run(cmd, input=stdin, stdout=sp.PIPE, check=True).stdout


def vwright(
    view,
    distance: float = 0,
) -> bytes:
    """Run vwright."""
    cmd = [str(BINPATH / "vwright")]
    cmd.extend(view.args())
    cmd.append(str(distance))
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


def xform(
    inp,
    translate: Optional[Tuple[float, float, float]] = None,
    expand_cmd: bool = True,
    iprefix: Optional[str] = None,
    mprefix: Optional[str] = None,
    invert: bool = False,
    rotatex: Optional[float] = None,
    rotatey: Optional[float] = None,
    rotatez: Optional[float] = None,
    scale: Optional[float] = None,
    mirrorx: bool = False,
    mirrory: bool = False,
    mirrorz: bool = False,
    iterate: Optional[int] = None,
) -> bytes:
    stdin = None
    cmd = [str(BINPATH / "xform")]
    if not expand_cmd:
        cmd.append("-c")
    if iprefix:
        cmd.extend(["-n", iprefix])
    if mprefix:
        cmd.extend(["-m", mprefix])
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
    if iterate:
        cmd.extend(["-i", str(iterate)])
    if translate is not None:
        cmd.extend(["-t", *(str(v) for v in translate)])
    if isinstance(inp, bytes):
        stdin = inp
    else:
        cmd.append(inp)
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout


def wrap_bsdf(
    inp=None,
    enforce_window=False,
    comment=None,
    correct_solid_angle=False,
    basis=None,
    tf=None,
    tb=None,
    rf=None,
    rb=None,
    spectr=None,
    unlink=False,
    unit=None,
    geometry=None,
    **kwargs,
):
    """Wrap BSDF."""
    cmd = [str(BINPATH / "wrapBSDF")]
    if enforce_window:
        cmd.append("-W")
    if correct_solid_angle:
        cmd.append("-c")
    if basis:
        cmd.extend(["-a", basis])
    if tf:
        cmd.extend(["-tf", tf])
    if tb:
        cmd.extend(["-tb", tb])
    if rf:
        cmd.extend(["-rf", rf])
    if rb:
        cmd.extend(["-rb", rb])
    if spectr:
        cmd.extend(["-s", spectr])
    if unlink:
        cmd.append("-U")
    if unit:
        cmd.extend(["-u", unit])
    if comment:
        cmd.extend(["-C", comment])
    if geometry:
        cmd.extend(["-g", geometry])
    fields_keys = ("n", "m", "d", "c", "ef", "eb", "eo", "t", "h", "w")
    fields = []
    for key in fields_keys:
        if key in kwargs:
            fields.append(f"{key}={kwargs[key]}")
    cmd.extend(["-f", ";".join(fields)])
    if inp is not None:
        cmd.append(inp)
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout
