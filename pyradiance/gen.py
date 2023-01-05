"""
Radiance generators and scene Manipulators
"""
from pathlib import Path
import subprocess as sp
from typing import List, Optional, Sequence


BINPATH = Path(__file__).parent / "bin"


def genbsdf(
    *inp,
    nsamp=1,
    nproc=1,
    params: Optional[Sequence[str]] = None,
    enforce_window=False,
    ttree_rank: Optional[int] = None,
    ttree_res: Optional[int] = None,
    color=False,
    reciprocity=True,
    recover_dir=None,
    forward=False,
    backward=True,
    mgf=None,
    geom=False,
    geom_unit=None,
    dim: Optional[Sequence[float]] = None,
    **kwargs,
):
    """Run genBSDF to generate a BSDF file from a Radiance scene."""
    cmd = [str(BINPATH / "genBSDF")]
    if recover_dir is not None:
        cmd += ["-recover", recover_dir]
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
    reciprocity = "+" if reciprocity else "-"
    cmd.append(f"{reciprocity}a")
    if geom:
        if geom_unit is None:
            raise ValueError("geom_unit must be specified if geom is True")
        geom = "+" if geom else "-"
        cmd += [f"{geom}geom", geom_unit]
    forward = "+" if forward else "-"
    cmd.append(f"{forward}f")
    backward = "+" if backward else "-"
    cmd.append(f"{backward}b")
    mgf = "+" if mgf else "-"
    cmd.append(f"{mgf}mgf")
    color = "+" if color else "-"
    cmd.append(f"{color}C")
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
    cmd += inp
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


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
    cmd += ["-a", str(latitude), "-o", str(longitude), "-m", str(timezone)]
    if year is not None:
        cmd += ["-y", str(year)]
    if None not in (dirnorm, diffhor):
        cmd += ["-W", str(dirnorm), str(diffhor)]
    if None not in (dirhor, diffhor):
        cmd += ["-G", str(dirhor), str(diffhor)]
    if None not in (dirnormp, diffhorp):
        cmd += ["-L", str(dirnormp), str(diffhorp)]
    if solar:
        cmd += ["-O", "1"]
    return sp.run(cmd, stdout=sp.PIPE, check=True).stdout.decode().strip()
