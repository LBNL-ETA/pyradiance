"""
Radiance picture processing utilities.
"""

from pathlib import Path
import subprocess as sp
from typing import List, Optional, Union


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
    cmd = ["pcond"]
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
    cmd = ["pfilt"]
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
    cmd = ["pvalue"]
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
    cmd = ["pvalue", "-r"]
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
