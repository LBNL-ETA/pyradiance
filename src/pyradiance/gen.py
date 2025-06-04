"""
Radiance generators and scene Manipulators
"""

import subprocess as sp
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
import os
import json
import tempfile
from typing import Sequence, NamedTuple
from enum import Enum

from .anci import BINPATH, handle_called_process_error

NM_PER_MICRON = 1e3
M_PER_MM = 1e-3
DEFAULT_THICKNESS_MM = 3

class GlazingType(Enum):
    monolithic = "monolithic"
    coated = "coated"
    laminate = "laminate"


class SpectralPoint(NamedTuple):
    wavelength_nm: int
    rf: float
    rb: float
    t: float


@dataclass(slots=True)
class GlazingLayerData:
    name: str
    glazing_type: GlazingType
    thickness_m: float
    spectral_points: list[SpectralPoint] = field(default_factory=list)

    def to_datstr(self) -> str:
        """
        Generates the string content for a 2 dimensional .dat file
        from this layer's spectral points.
        """
        num_points = len(self.spectral_points)
        if not self.spectral_points or num_points <= 0:
            return ""
        wavelength_nm_str = ' '.join(str(p.wavelength_nm) for p in self.spectral_points)
        rf_values_str = [f"{p.rf:.6f}" for p in self.spectral_points]
        rb_values_str = [f"{p.rb:.6f}" for p in self.spectral_points]
        t_values_str = [f"{p.t:.6f}" for p in self.spectral_points]

        dat_parts: list[str] = [
            f"2\n0 2 3\n0 0 {num_points} {wavelength_nm_str}"
        ]
        dat_parts.extend(rf_values_str)
        dat_parts.extend(rb_values_str)
        dat_parts.extend(t_values_str)

        return "\n".join(dat_parts)


@handle_called_process_error
def genblinds(
    mat: str,
    name: str,
    depth: float,
    width: float,
    height: float,
    nslats: int,
    angle: float,
    rcurv: None | float = None,
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
    cmd = [str(BINPATH / "genblinds"), mat, name, str(depth), str(width), str(height)]
    cmd.extend([str(nslats), str(angle)])
    if rcurv is not None:
        cmd.append("+r") if rcurv > 0 else cmd.append("-r")
        cmd.append(str(rcurv))
    return sp.run(cmd, check=True, stdout=sp.PIPE).stdout


@handle_called_process_error
def genbox(
    mat: str,
    name: str,
    xsiz: float,
    ysiz: float,
    zsiz: float,
    inward: bool = False,
    beveled: None | float = None,
    rounded: None | float = None,
    nsegs: None | int = None,
    smoothing: bool = False,
    waveout: bool = False,
) -> bytes:
    """Generate a box.

    Args:
        mat: material name
        name: box name
        xsiz: size in x dimension
        ysiz: size in y dimension
        zsiz: size in z dimension
        inward: box facing inward
        beveled: beveled size
        rounded: rounded corner size
        nsegs: number of segments
        smoothing: to smooth
        waveout: wavefront (.obj) out

    Returns:
        the box
    """
    cmd = [str(BINPATH / "genbox")]
    cmd.append(mat)
    cmd.append(name)
    cmd.append(str(xsiz))
    cmd.append(str(ysiz))
    cmd.append(str(zsiz))
    if inward:
        cmd.append("-i")
    if beveled is not None:
        cmd.extend(["-b", str(beveled)])
    if rounded is not None:
        cmd.extend(["-r", str(rounded)])
    if nsegs is not None:
        cmd.extend(["-n", str(nsegs)])
    if smoothing:
        cmd.append("-s")
    if waveout:
        cmd.append("-o")
    return sp.run(cmd, stdout=sp.PIPE).stdout


@handle_called_process_error
def gendaylit(
    dt: datetime,
    latitude: float,
    longitude: float,
    timezone: int,
    year: None | int = None,
    dirnorm: None | float = None,
    diffhor: None | float = None,
    dirhor: None | float = None,
    dirnorm_illum: None | float = None,
    diffhor_illum: None | float = None,
    solar: bool = False,
    sky_only: bool = False,
    silent: bool = False,
    grefl: None | float = None,
    interval: None | int = None,
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
        dirnorm_illum: direct normal illuminance
        diffhor_illum: diffuse horizontal illuminance
        solar: if True, include solar position
        sky_only: sky description only
        silent: supress warnings,
        grefl: ground reflectance
        interval: interval for epw data

    Returns:
        output of gendaylit
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
    weather_data: str | Path | bytes,
    verbose: bool = False,
    header: bool = True,
    average: bool = False,
    sun_only: bool = False,
    sky_only: bool = False,
    sun_file: None | str = None,
    sun_mods: None | str = None,
    daylight_hours_only: bool = False,
    dryrun: bool = False,
    sky_color: None | list[float] = None,
    ground_color: None | list[float] = None,
    rotate: None | float = None,
    outform: None | str = None,
    onesun: bool = False,
    solar_radiance: bool = False,
    mfactor: int = 1,
) -> bytes:
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


class GenGlaze:
    def __init__(
        self,
        wavelength_start: int = 380,
        wavelength_end: int = 780,
        wavelength_interval: int = 5,
        prefix: str = "unnamed",
    ):
        self.cmd = [
            str(BINPATH / "genglaze"),
            "-s", str(wavelength_start), str(wavelength_end), str(wavelength_interval),
            "-p", prefix,
        ]

    def add_monolithic(self, fpath: str, thickness: float):
        if not fpath.endswith(".dat"):
            raise ValueError(f"Expect a .dat input file, got {fpath}")
        self.cmd.extend(["-m", fpath, thickness])
        return self

    def add_coated(self, fpath: str):
        if not fpath.endswith(".dat"):
            raise ValueError(f"Expect a .dat input file, got {fpath}")
        self.cmd.extend(["-c", fpath])
        return self

    @handle_called_process_error
    def __call__(self) -> bytes:
        return sp.run(self.cmd, check=True, stdout=sp.PIPE, stderr=sp.PIPE).stdout


@handle_called_process_error
def genglaze_data(
    layers: list[GlazingLayerData],
    prefix: str = "unnamed",
    wavelength_start: int = 380,
    wavelength_end: int = 780,
    wavelength_interval: int = 5,
) -> bytes:
    """
    Calls genglaze with a list of processed GlazingLayerData objects.
    Each GlazingLayerData object can format itself for the genglaze .dat file.
    """
    if not layers or len(layers) < 1:
        return b""
    cmd: list[str] = [
        str(BINPATH / "genglaze"),
        "-s",
        str(wavelength_start),
        str(wavelength_end),
        str(wavelength_interval),
        "-p",
        prefix,
    ]
    output_lines: list[bytes] = []

    with tempfile.TemporaryDirectory(prefix="pyradiance_genglaze_layers_") as tmpdir:
        for idx, layer in enumerate(layers):
            output_lines.append(
                (
                    f"# Layer {idx + 1}: {layer.name}({layer.thickness_m:.4f}m) {layer.glazing_type}"
                ).encode()
            )

            dat_fpath = os.path.join(tmpdir, f"layer{idx}.dat")
            with open(dat_fpath, "w") as f:
                f.write(layer.to_datstr())

            if layer.glazing_type == GlazingType.monolithic.value:
                cmd.extend(["-m", dat_fpath, str(layer.thickness_m)])
            else:
                cmd.extend(["-c", dat_fpath])

        output_lines.append(b"")

        process_result = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE, check=True)
        output_lines.append(process_result.stdout)

    return b"\n".join(output_lines)


@handle_called_process_error
def genglaze_json(
    fpaths: Sequence[str],
    prefix: str = "unnamed",
    wavelength_start: int = 380,
    wavelength_end: int = 780,
    wavelength_interval: int = 5,
) -> bytes:
    """Call genglaze from IGSDB glazing records (.json)."""
    layers: list[GlazingLayerData] = []
    out: list[str] = []
    for fpath in fpaths:
        with open(fpath, "r") as f:
            data = json.load(f)
        if data["type"] != "glazing":
            raise ValueError(
                f"{fpath}: This is not a glazing product (It's a {data['type']})"
            )
        name: str = data["name"] or data["product_name"] or "unnamed"
        glazing_type: str = data["subtype"]
        thickness_mm = data["measured_data"]["thickness"] or DEFAULT_THICKNESS_MM
        thickness_m = thickness_mm * M_PER_MM
        spectral_data_points = [
            SpectralPoint(
                wavelength_nm=sdata["wavelength"] * NM_PER_MICRON,
                rf=sdata["Rf"],
                rb=sdata["Rb"],
                t=sdata["T"],
            ) for sdata in data["spectral_data"]["spectral_data"]]
        spectral_data_points.sort(key=lambda a: a.wavelength_nm)
        layers.append(
            GlazingLayerData(
                name=name,
                glazing_type=glazing_type,
                thickness_m=thickness_m,
                spectral_points=spectral_data_points
            )
        )
    return genglaze_data(
        layers=layers,
        prefix=prefix,
        wavelength_start=wavelength_start,
        wavelength_end=wavelength_end,
        wavelength_interval=wavelength_interval
    )


@handle_called_process_error
def genrev(
    mat: str,
    name: str,
    z_t: str,
    r_t: str,
    nseg: int,
    expr: None | str = None,
    file: None | str = None,
    smooth: bool = False,
) -> bytes:
    cmd = [str(BINPATH / "genrev")]
    cmd.append(mat)
    cmd.append(name)
    cmd.append(z_t)
    cmd.append(r_t)
    cmd.append(str(nseg))
    if expr is not None:
        cmd.extend(["-e", expr])
    if file is not None:
        cmd.extend(["-f", file])
    if smooth:
        cmd.append("-s")
    return sp.run(cmd, stdout=sp.PIPE).stdout


@handle_called_process_error
def gensdaymtx(
    weather_data: str | Path | bytes,
    verbose: bool = False,
    header: bool = True,
    sun_only: bool = False,
    sky_only: bool = False,
    daylight_hours_only: bool = False,
    ground_reflectance: None | list[float] = None,
    rotate: None | float = None,
    outform: None | str = None,
    onesun: bool = False,
    mfactor: int = 1,
    nthreads: int = 1,
) -> bytes:
    """Generate an annual spectral sky matrix from a weather tape.

    Args:
        weather_data: weather data
        mfactor: multiplication factor
        verbose: verbose
        header: header
        sun_only: sun only
        sky_only: sky only
        daylight_hours_only: daylight hours only
        ground_reflectance: ground color
        rotate: rotate
        outform: outform
        onesun: onesun
        nthreads: number of threads to use for precomputations

    Returns:
        bytes: output of gensdaymtx
    """
    stdin = None
    cmd = [str(BINPATH / "gensdaymtx")]
    cmd.extend(["-m", str(mfactor)])
    if verbose:
        cmd.append("-v")
    if not header:
        cmd.append("-h")
    if sun_only:
        cmd.append("-d")
    elif sky_only:
        cmd.append("-s")
    if onesun:
        cmd.extend(["-5", ".533"])
    if ground_reflectance:
        cmd.extend(["-g", str(ground_reflectance)])
    cmd.extend(["-n", str(nthreads)])
    if daylight_hours_only:
        cmd.append("-u")
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
    dt: None | datetime = None,
    latitude: None | float = None,
    longitude: None | float = None,
    timezone: None | int = None,
    altitude: None | float = None,
    azimuth: None | float = None,
    year: None | int = None,
    sunny_with_sun: bool = False,
    sunny_without_sun: bool = False,
    cloudy: bool = False,
    intermediate_with_sun: bool = False,
    intermediate_without_sun: bool = False,
    uniform: bool = False,
    ground_reflectance: None | float = None,
    zenith_brightness: None | float = None,
    horizontal_brightness: None | float = None,
    solar_radiance: None | float = None,
    horizontal_direct_irradiance: None | float = None,
    turbidity: None | float = None,
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
def genssky(
    dt: datetime,
    latitude: float = 37.7,
    longitude: float = 122.2,
    timezone: int = 120,
    year: None | int = None,
    res: int = 64,
    cloud_cover: float = 0.0,
    ground_reflectance: float = 0.2,
    broadband_aerosol_optical_depth: float = 0.115,
    mie_file: None | str = None,
    nthreads: int = 1,
    out_dir: str = ".",
    out_name: str = "out",
    dir_norm_illum: None | float = None,
    diff_hor_illum: None | float = None,
) -> bytes:
    """Generate a RADIANCE description of the spectral sky.

    Args:
        dt: datetime object, mutally exclusive with altitude and azimuth
        latitude: latitude, only apply if dt is not None
        longitude: longitude, only apply if dt is not None
        timezone: timezone, only apply if dt is not None
        year: year, only apply if dt is not None
        res: hsr image resolution, default: 64,
        cloud_cover: cloud cover 0.0: clear, 1.0: overcast,
        ground_reflectance: default: 0.2,
        broadband_aerosol_optical_depth: default: 0.115,
        mie_file: mie scattering coefficient source file
        nthreads: number of threads used for precomputation, default:1,
        out_dir: directory to save precomputed data that can be reused, default to current working directory.
            This can be changed to RAYPATH for cross-section data reused.
        out_name: output file name, defautl: "out"
        dir_norm_illum: direct normal illuminance to calibrate the output against,
        diff_hor_illum: diffuse horizontal illuminance to calibrate the output against.


    Returns:
        str: output of gensky
    """
    cmd = [str(BINPATH / "genssky")]
    cmd.append(str(dt.month))
    cmd.append(str(dt.day))
    cmd.append(str(dt.hour + dt.minute / 60))
    cmd.extend(["-a", str(latitude)])
    cmd.extend(["-o", str(longitude)])
    cmd.extend(["-m", str(timezone)])
    cmd.extend(["-n", str(nthreads)])
    cmd.extend(["-r", str(res)])
    if year is not None:
        cmd += ["-y", str(year)]
    cmd.extend(["-c", str(cloud_cover)])
    cmd.extend(["-d", str(broadband_aerosol_optical_depth)])
    cmd.extend(["-g", str(ground_reflectance)])
    if mie_file is not None:
        cmd.extend(["-l", str(mie_file)])
    cmd.extend(["-p", out_dir])
    cmd.extend(["-f", out_name])
    if (dir_norm_illum is not None) and (diff_hor_illum is not None):
        cmd.extend(["-L", str(dir_norm_illum), str(diff_hor_illum)])
    return sp.run(cmd, stderr=sp.PIPE, stdout=sp.PIPE, check=False).stdout


@handle_called_process_error
def mkillum(
    inp: bytes,
    octree: str | Path,
    nproc: int = 1,
    params: None | Sequence[str] = None,
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
