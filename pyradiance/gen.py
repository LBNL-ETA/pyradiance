"""
Radiance generators and scene Manipulators
"""
from datetime import datetime
from pathlib import Path
import subprocess as sp
from typing import List, Optional, Sequence, Union

from .anci import BINPATH, handle_called_process_error


@handle_called_process_error
def genblinds(
    mat: str,
    name: str,
    depth: float,
    width: float,
    height: float,
    nslats: int,
    angle: float,
    rcurv: Optional[float] = None,
) -> bytes:
    """Generate a RADIANCE description of venetian blinds.

    Args:
        mat: Material name
        name: Name of the blinds
        depth: Depth of the blinds
        width: Width of the blinds
        height: Height of the blinds
        nslats: Number of slats
        angle: Angle of the slats
        rcurv: Radius of curvature of the slats, + for upward curvature, - for downward

    Returns:
        bytes: RADIANCE description of the blinds

    Examples:
        >>> genblinds('mat', 'blinds', 0.1, 0.5, 1.0, 4, 45, 0.1)
    """
    cmd = [BINPATH / "genblinds", mat, name, str(depth), str(width), str(height)]
    cmd.extend([str(nslats), str(angle)])
    if rcurv is not None:
        if rcurv > 0:
            cmd.extend(["+r", str(rcurv)])
        else:
            cmd.extend(["-r", str(rcurv)])
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


@handle_called_process_error
def genbsdf(
    *inp: Union[str, Path],
    nsamp: int = 1,
    nproc: int = 1,
    params: Optional[Sequence[str]] = None,
    enforce_window=False,
    ttree_rank: Optional[int] = None,
    ttree_res: Optional[int] = None,
    color: bool = False,
    reciprocity: bool = True,
    recover_dir: Optional[Union[str, Path]] = None,
    forward: bool = False,
    backward: bool = True,
    mgf: Optional[Union[str, Path]] = None,
    geom: bool = False,
    geom_unit: Optional[str] = None,
    dim: Optional[Sequence[float]] = None,
    **kwargs,
) -> bytes:
    """Generate BSDF description from Radiance or MGF input

    Examples:
        >>> genbsdf('material.mat', 'blinds.rad', nsamp=50, nproc=4)

    Args:
        inp: Input files. This can be a list of files or a single string with
        nsamp: Number of samples to generate. Default is 1.
        nproc: Number of processors to use. Default is 1.
        params: A list of parameters to pass to genBSDF.
        enforce_window: Set to True to enforce the window. Default is False.
        ttree_rank: Tensor tree rank, 3 for isotropic and 4 for anisotropic BSDF.
        ttree_res: Tensor tree BSDF resolution, e.g., 5 6 7.
        color: Set to True to generate color BSDF. Default is False.
        reciprocity: Set to False to disable reciprocity. Default is True.
        recover_dir: Set to a path to recover from a previous run.
        forward: Set to True to generate forward BSDF. Default is False.
        backward: Set to True to generate backward BSDF. Default is True.
        mgf: Set to a path to a MGF file to use.
        geom: Set to True to generate geometry BSDF. Default is False.
        geom_unit: Set to a unit to use for geometry BSDF.
        dim: Set to a list of 6 numbers to use for geometry BSDF.
        kwargs: Additional parameters to pass to genBSDF.
    Returns:
        str: Output of genBSDF.
    """
    cmd = [str(BINPATH / "genBSDF")]
    if recover_dir is not None:
        cmd += ["-recover", str(recover_dir)]
        return sp.run(cmd, check=True, stdout=sp.PIPE).stdout
    cmd += ["-n", str(nproc), "-c", str(nsamp)]
    if params is not None:
        cmd += ["-r", " ".join(params)]
    if ttree_rank is not None:
        if ttree_rank not in (3, 4):
            raise ValueError("ttree_rank must be 3 or 4")
        if ttree_res is None:
            raise ValueError("ttree_res must be specified if ttree_rank is specified")
        cmd += [f"-t{ttree_rank}", str(ttree_res)]
    reciprocity_sign = "+" if reciprocity else "-"
    cmd.append(f"{reciprocity_sign}a")
    if geom:
        if geom_unit is None:
            raise ValueError("geom_unit must be specified if geom is True")
        geom_sign = "+" if geom else "-"
        cmd += [f"{geom_sign}geom", geom_unit]
    forward_sign = "+" if forward else "-"
    cmd.append(f"{forward_sign}f")
    backward_sign = "+" if backward else "-"
    cmd.append(f"{backward_sign}b")
    mgf = "+" if mgf else "-"
    cmd.append(f"{mgf}mgf")
    color_sign = "+" if color else "-"
    cmd.append(f"{color_sign}C")
    if dim is not None:
        cmd += ["-dim", *[str(d) for d in dim]]
    if enforce_window:
        cmd.append("-W")
        required = set(("m", "n", "t"))
        if set(kwargs).intersection(required) != required:
            raise ValueError("enforce_window requires m, n, and t to be specified")
    fields = []
    for key in ("n", "m", "d", "c", "ef", "eb", "eo", "t", "h", "w"):
        if key in kwargs:
            fields.append(f"{key}={kwargs[key]}")
    cmd += ["-s", ";".join(fields)]
    cmd.extend([str(i) for i in inp])
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


@handle_called_process_error
def gendaylit(
    dt: datetime,
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
    """Generates a RADIANCE description of the daylight sources using
    Perez models for direct and diffuse components.

    Args:
        dt: python datetime object
        latitude: latitude in degrees
        longitude: longitude in degrees
        timezone: standard meridian timezone, e.g., 120 for PST
        year: Need to set it explicitly, won't use year in datetime object
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
    return sp.run(cmd, stderr=sp.PIPE, stdout=sp.PIPE, check=True).stdout


@handle_called_process_error
def gendaymtx(
    weather_data: Union[str, Path, bytes],
    verbose: bool = False,
    header: bool = True,
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
    """Generate an annual Perez sky matrix from a weather tape.

    Args:
        weather_data: weather data
        mfactor: multiplication factor
        verbose: verbose
        header: header
        average: average
        sun_only: sun only
        sky_only: sky only
        sun_file: sun file
        sun_mods: sun mods
        daylight_hours_only: daylight hours only
        dryrun: dryrun
        sky_color: sky color
        ground_color: ground color
        rotate: rotate
        outform: outform
        onesun: onesun
        solar_radiance: solar radiance

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
        stdin = weather_data
    elif isinstance(weather_data, (str, Path)):
        cmd.append(str(weather_data))
    else:
        raise TypeError("weather_data must be a string, Path, or bytes")
    out = sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE, stderr=sp.PIPE)
    return out.stdout


@handle_called_process_error
def gensky(
    dt: Optional[datetime] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[int] = None,
    altitude: Optional[float] = None,
    azimuth: Optional[float] = None,
    year: Optional[int] = None,
    sunny_with_sun: bool = False,
    sunny_without_sun: bool = False,
    cloudy: bool = False,
    intermediate_with_sun: bool = False,
    intermediate_without_sun: bool = False,
    uniform: bool = False,
    ground_reflectance: Optional[float] = None,
    zenith_brightness: Optional[float] = None,
    horizontal_brightness: Optional[float] = None,
    solar_radiance: Optional[float] = None,
    horizontal_direct_irradiance: Optional[float] = None,
    turbidity: Optional[float] = None,
) -> bytes:
    """Generate a RADIANCE description of the sky.

    Args:
        dt: datetime object, mutally exclusive with altitude and azimuth
        latitude: latitude, only apply if dt is not None
        longitude: longitude, only apply if dt is not None
        timezone: timezone, only apply if dt is not None
        altitude: solar altitude, mutally exclusive with dt
        azimuth: solar azimuth, mutally exclusive with dt
        year: year, only apply if dt is not None
        sunny_with_sun: sunny with sun
        sunny_without_sun: sunny without sun
        cloudy: CIE overcast sky
        intermediate_with_sun: intermediate with sun
        intermediate_without_sun: intermediate without sun
        uniform: uniform sky
        ground_reflectance: ground reflectance
        zenith_brightness: zenith brightness in watts/steradian/meter^2
        horizontal_brightness: horizontal brightness in watts/metere^2
        solar_radiance: solar radiance in watts/steradian/meter^2
        horizontal_direct_irradiance: horizontal direct irradiance in watts/meter^2
        turbidity: turbidity factor
    Returns:
        str: output of gensky
    """
    cmd = [str(BINPATH / "gensky")]
    if dt is not None:
        cmd.append(str(dt.month))
        cmd.append(str(dt.day))
        cmd.append(str(dt.hour + dt.minute / 60))
        if latitude is not None:
            cmd.extend(["-a", str(latitude)])
        if longitude is not None:
            cmd.extend(["-o", str(longitude)])
        if timezone is not None:
            cmd.extend(["-m", str(timezone)])
        if year is not None:
            cmd += ["-y", str(year)]
    elif None not in (altitude, azimuth):
        cmd.extend(["-ang", str(altitude), str(azimuth)])
    else:
        raise ValueError("Must provide either dt or altitude and azimuth")
    if sunny_with_sun:
        cmd.append("+s")
    elif sunny_without_sun:
        cmd.append("-s")
    elif cloudy:
        cmd.append("-c")
    elif intermediate_with_sun:
        cmd.append("+i")
    elif intermediate_without_sun:
        cmd.append("-i")
    elif uniform:
        cmd.append("-u")
    if ground_reflectance is not None:
        cmd.extend(["-g", str(ground_reflectance)])
    if zenith_brightness is not None:
        cmd.extend(["-b", str(zenith_brightness)])
    elif horizontal_brightness is not None:
        cmd.extend(["-B", str(horizontal_brightness)])
    if solar_radiance is not None:
        cmd.extend(["-r", str(solar_radiance)])
    elif horizontal_direct_irradiance is not None:
        cmd.extend(["-R", str(horizontal_direct_irradiance)])
    if turbidity is not None:
        cmd.extend(["-t", str(turbidity)])
    return sp.run(cmd, stderr=sp.PIPE, stdout=sp.PIPE, check=True).stdout


@handle_called_process_error
def mkillum(
    inp: bytes,
    octree: Union[str, Path],
    nproc: int = 1,
    params: Optional[Sequence[str]] = None,
) -> bytes:
    """Compute illum sources for a RADIANCE scene

    Args:
        inp: input file content as bytes
        octree: octree file
        nproc: number of processes
        params: additional parameters
    Returns:
        Output of mkillum in bytes
    """
    cmd = [str(BINPATH / "mkillum")]
    if nproc:
        cmd.extend(["-n", str(nproc)])
    if params:
        cmd.extend(params)
    cmd.append(str(octree))
    return sp.run(cmd, input=inp, stderr=sp.PIPE, stdout=sp.PIPE, check=True).stdout
