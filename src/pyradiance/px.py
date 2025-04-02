"""
Radiance picture processing utilities.
"""

import subprocess as sp
from pathlib import Path
from typing import Sequence

from .anci import BINPATH, handle_called_process_error


class Pcomb:
    def __init__(
        self,
        xres: None | int = None,
        yres: None | int = None,
        inform: str = "a",
        fout: bool = True,
        header: bool = False,
        expression: None | str = None,
        source: None | str = None,
    ):
        """combine Radiance pictures and/or float matrices

        Args:
            xres: horizontal resolution
            yres: vertical resolution
            inform: input data format. Default is "a" for ascii.
            fout: if True, write output to file
            header: if True, write header
            expression: expression
            source: source
        """
        self.has_input = False
        self.stdin: None | bytes = None
        self.cmd = [str(BINPATH / "pcomb")]
        if xres is not None:
            self.cmd.extend(["-x", str(xres)])
        if yres is not None:
            self.cmd.extend(["-y", str(yres)])
        if inform != "a":
            self.cmd.extend(["-i", inform])
        if fout:
            self.cmd.append("-ff")
        if header:
            self.cmd.append("-h")
        if expression is not None:
            self.cmd.extend(["-e", expression])
        if source is not None:
            self.cmd.extend(["-f", source])

    def add(
        self,
        image: Path | str | bytes,
        original: bool = False,
        scaler: float = 1.0,
    ) -> "Pcomb":
        """Add images to command.

        Args:
            image: Input image file or bytes
            original: keep original exposure
            scaler: Scaling factor

        Returns:
            self
        """
        if original:
            self.cmd.append("-o")
        self.cmd.extend(["-s", str(scaler)])
        if isinstance(image, bytes):
            if self.stdin is not None:
                raise ValueError("Only one bytes input is allowed with pcomb.")
            self.stdin = image
            self.cmd.append("-")
        elif isinstance(image, (str, Path)):
            self.cmd.append(str(image))
        else:
            raise ValueError(f"Unsupported input type: {type(image)}")
        self.has_input = True
        return self

    @handle_called_process_error
    def __call__(self):
        if not self.has_input:
            raise ValueError("No input images, call .add() to add one")
        return sp.run(self.cmd, input=self.stdin, stdout=sp.PIPE).stdout


@handle_called_process_error
def pcompos(
    inputs: Sequence[Path | str | bytes],
    pos: None | Sequence[Sequence[float]] = None,
    xres: None | int = None,
    yres: None | int = None,
    spacing: int = 0,
    background: None | tuple[float, float, float] = None,
    anchors: None | Sequence[str] = None,
    header: bool = True,
    lower_threashold: None | float = None,
    upper_threshold: None | float = None,
    label: None | str = None,
    label_height: None | int = None,
    ncols: None | int = None,
    anchor_point: None | Sequence[str] = None,
) -> bytes:
    """Composite Radiance pictures

    Args:
        inputs: list of input files
        pos: list of positions
        xres: horizontal resolution
        yres: vertical resolution
        spacing: spacing between images
        background: background color
        anchors: list of anchors
        header: set to False if want to reduce header
        lower_threashold: lower threshold
        upper_threshold: upper threshold
        label: label
        label_height: label height
        ncols: number of columns
        anchor_point: anchor point

    Returns:
        bytes: output of pcompos
    """
    cmd = [str(BINPATH / "pcompos")]
    stdin = None
    if ncols is not None:
        cmd.extend(["-a", str(ncols)])
        if spacing > 0:
            cmd.extend(["-s", str(spacing)])
        if anchor_point is not None:
            cmd.extend(["-o", *anchor_point])
    else:
        if pos is None:
            raise ValueError("Either pos or ncols must be specified")
        if len(pos) != len(inputs):
            raise ValueError("pos must have the same number of elements as inputs")
        if xres is not None:
            cmd.extend(["-x", str(xres)])
        if yres is not None:
            cmd.extend(["-y", str(yres)])
        if background is not None:
            cmd.extend(
                ["-b", str(background[0]), str(background[1]), str(background[2])]
            )
        if lower_threashold is not None:
            cmd.extend(["-t", str(lower_threashold)])
        if upper_threshold is not None:
            cmd.extend(["+t", str(upper_threshold)])
        if label is not None:
            if label == "":
                cmd.append("-la")
            else:
                cmd.extend(["-l", label])
            if label_height is not None:
                cmd.extend(["-lh", str(label_height)])
        if not header:
            cmd.append("-h")
        for i, input in enumerate(inputs):
            if anchors is not None:
                if anchors[i] is not None:
                    cmd.append(f"={anchors[i]}")
            if isinstance(input, (str, Path)):
                cmd.append(str(input))
            elif isinstance(input, bytes):
                if stdin is not None:
                    raise ValueError("Only one bytes input is allowed with pcompos.")
                stdin = input
                cmd.append("-")
            else:
                raise ValueError(f"Unsupported input type: {type(input)}")
            cmd.extend(list(map(str, pos[i])))
    return sp.run(cmd, input=stdin, stdout=sp.PIPE).stdout


@handle_called_process_error
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
    fixpoints: None | list[tuple] = None,
    histo: str = "",
    expval: str = "",
    ldmax: float = 100.0,
    lddyn: float = 100.0,
    primaries: None | list[float] = None,
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


@handle_called_process_error
def pfilt(
    image: str | Path | bytes,
    xres: None | str = None,
    yres: None | str = None,
    pixel_aspect: float = 0,
    pa_correct: bool = False,
    exposure: None | float = 0,
    lamp: None | str = None,
    lampdat: None | str = None,
    one_pass: bool = False,
    gaussian_filter_radius: None | float = None,
    limitfrac: None | float = None,
    hot_threshold: float = 100,
    star_points: int = 0,
    star_spread: float = 0.0001,
    average_hot: bool = False,
) -> bytes:
    """filter a Radiance picture.
    By default, it uses two passes on the input, using a box filter.

    Args:
        image: input image
        xres: horizontal resolution
        yres: vertical resolution
        pixel_aspect: pixel aspect ratio
        exposure: exposure value
        lamp: lamp file
        lampdat: lamp data file
        one_pass: use one pass filter
        gaussian_filter_radius: gaussian filter radius
        limitfrac: limit fraction
        hot_threshold: Set intensity considered 'hot', default 100 watts/sr/m2
        star_points: Number of points on a start pattern.
        star_spread: star pattern spread
        average_hot: average hot spots

    Returns:
        bytes: output of pfilt
    """
    stdin = None
    cmd = [str(BINPATH / "pfilt")]
    if xres:
        cmd.extend(["-x", xres])
    if yres:
        cmd.extend(["-y", yres])
    if pixel_aspect:
        cmd.extend(["-p", str(pixel_aspect)])
    if pa_correct:
        cmd.append("-c")
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
    if hot_threshold != 100:
        cmd.extend(["-h", str(hot_threshold)])
    if star_points:
        cmd.extend(["-n", str(star_points)])
    if star_spread != 0.0001:
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


@handle_called_process_error
def psign(
    text: str,
    background: tuple[float, float, float] = (1.0, 1.0, 1.0),
    foreground: tuple[float, float, float] = (0.0, 0.0, 0.0),
    reads_to_right: bool = True,
    reads_upwards: bool = False,
    reads_to_left: bool = False,
    reads_downwards: bool = False,
    height: int = 32,
    aspect: float = 1.67,
    xsize: None | int = None,
    ysize: None | int = None,
    spacing: float = 0.0,
    fontfile: str = "helvet.fnt",
) -> bytes:
    """product a Radiance picture from text

    Args:
        text: text
        background: background color
        foreground: foreground color
        reads_to_right: reads to right
        reads_upwards: reads upwards
        reads_to_left: reads to left
        reads_downwards: reads downwards
        height: height
        aspect: aspect
        xsize: xsize
        ysize: ysize
        spacing: spacing
        fontfile: fontfile

    Returns:
        bytes: output of psign
    """
    cmd = [str(BINPATH / "psign")]
    cmd.extend(["-cb", str(background[0]), str(background[1]), str(background[2])])
    cmd.extend(["-cf", str(foreground[0]), str(foreground[1]), str(foreground[2])])
    if reads_to_right:
        cmd.append("-dr")
    elif reads_to_left:
        cmd.append("-dl")
    if reads_upwards:
        cmd.append("-du")
    elif reads_downwards:
        cmd.append("-dd")
    cmd.extend(["-h", str(height)])
    cmd.extend(["-a", str(aspect)])
    if xsize:
        cmd.extend(["-x", str(xsize)])
    if ysize:
        cmd.extend(["-y", str(ysize)])
    cmd.extend(["-s", str(spacing)])
    if fontfile:
        cmd.extend(["-f", fontfile])
    cmd.append(text)
    return sp.run(cmd, stdout=sp.PIPE, check=True).stdout


@handle_called_process_error
def pvalue(
    pic: Path | str | bytes,
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
    outprimary: None | str = None,
) -> bytes:
    """convert RADIANCE picture to/from alternate formats
    Pvalue converts the pixels of a RADIANCE picture to or from another format.
    In the default mode, pixels are sent to the standard output, one per line,
    in the following ascii format: xpos ypos red  green     blue

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


@handle_called_process_error
def pvaluer(
    pic: Path | str | bytes,
    xres: None | int = None,
    yres: None | int = None,
    inform: str = "a",
    resstr: bool = True,
    dataonly: bool = False,
    header: bool = True,
    primaries: None | list[float] = None,
    pxyz: bool = False,
) -> bytes:
    """
    Run Radiance pvalue tools reverse mode:
    constructing a image from pixel values.

    Args:
        pic: Path or bytes of the input pixel data.
        xres: X resolution.
        yres: Y resolution.
        inform: input data format. Default is "a" for ascii.
        header: Set to True if the picture file has a header. Default is False.
        primaries: list of primaries for XYZ calculation. Default is None.
        pxyz: Set to True to calculate XYZ values. Default is False.

    Returns:
        Bytes of the pvalue output
    """
    stdin = None
    cmd = [str(BINPATH / "pvalue"), "-r"]
    if not header:
        cmd.append("-h")
    if not resstr:
        cmd.append("-H")
    if dataonly:
        cmd.append("-d")
    if inform != "a":
        cmd.append(f"-d{inform}")
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


@handle_called_process_error
def ra_tiff(
    inp: str | Path | bytes,
    out: None | str = None,
    gamma: float = 2.2,
    greyscale: bool = False,
    lzw: bool = False,
    sgilog: bool = False,
    sgilog24: bool = False,
    ieee32: bool = False,
    primary: bool = False,
    exposure: int = 0,
    reverse: bool = False,
    xyze: bool = False,
) -> None | bytes:
    """ra_tiff - convert RADIANCE picture to/from a TIFF color
    or greyscale image

    Args:
        inp: Path or bytes to input picture file.
        out: Path to output file, required when output is a TIFF file.
        gamma: Gamma value for the output image. Default is 2.2.
        greyscale: Set to True to convert to greyscale. Default is False.
        lzw: Set to True to use LZW compression. Default is False.
        sgilog: Set to True to use SGI log compression. Default is False.
        sgilog24: Set to True to use SGI log 24 compression. Default is False.
        ieee32: Set to True to use IEEE 32-bit floating point compression.
        primary: Set to True to use 16-bit/primary output. Default is False.
        reverse: Set to True to invoke a reverse conversion, from a TIFF
            to a RADIANCE picture. Default is False.
        xyze: Set to True to use XYZE output when invoking a reverse
            conversion. Default is False.

    Returns:
        bytes: output of ra_tiff
    """
    cmd = [str(BINPATH / "ra_tiff")]
    if reverse:
        if isinstance(inp, bytes):
            raise ValueError("Input should be a file when input is TIFF.")
        cmd.append("-r")
        if xyze:
            cmd.append("-e")
        if gamma:
            cmd.extend(["-g", str(gamma)])
        if exposure:
            cmd.extend(["-e", str(exposure)])
    else:
        if out is None:
            raise ValueError(
                "Output should be specified when input is a RADIANCE picture."
            )
        if lzw:
            cmd.append("-z")
        elif sgilog:
            cmd.append("-L")
        elif sgilog24:
            cmd.append("-l")
        elif ieee32:
            cmd.append("-f")
        elif primary:
            cmd.append("-w")
        if greyscale:
            cmd.append("-b")
        if gamma:
            cmd.extend(["-g", str(gamma)])
        if exposure:
            cmd.extend(["-e", str(exposure)])
    stdin = None
    if isinstance(inp, (Path, str)):
        cmd.append(str(inp))
    elif isinstance(inp, bytes):
        stdin = inp
        cmd.append("-")
    cmd.append(str(out))
    pout = sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout
    if out is None:
        return pout
    return None


@handle_called_process_error
def ra_ppm(
    inp: str | Path | bytes,
    gamma: float = 2.2,
    greyscale: bool = False,
    reverse: bool = False,
    exposure: int = 0,
    ascii: bool = False,
    outscale: int = 255,
) -> bytes:
    """convert RADIANCE picture to/from a Poskanzer Portable Pixmap

    Args:
        inp: Path or bytes to input picture file.
        gamma: Gamma value for the output image. Default is 2.2.
        reverse: Set to True to invoke a reverse conversion, from a PPM
            to a RADIANCE picture. Default is False.
        exposure: Exposure value for the output image. Default is 0.
        ascii: Set to True to use ASCII Pixmap output. Default is False.
        outscale: Output scale value. Default is 255.

    Returns:
        bytes: output of ra_ppm
    """
    cmd = [str(BINPATH / "ra_ppm")]
    if reverse:
        cmd.append("-r")
    if gamma:
        cmd.extend(["-g", str(gamma)])
    if greyscale:
        cmd.append("-b")
    if exposure:
        cmd.extend(["-e", str(exposure)])
    if ascii:
        cmd.append("-a")
    if outscale != 255:
        cmd.extend(["-s", str(outscale)])
    stdin = None
    if isinstance(inp, (Path, str)):
        cmd.append(str(inp))
    elif isinstance(inp, bytes):
        stdin = inp
    return sp.run(cmd, check=True, input=stdin, stdout=sp.PIPE).stdout


@handle_called_process_error
def falsecolor(
    inp: str | Path | bytes,
    pic_overlay: None | str = None,
    contour: None | str = None,
    extrema: bool = False,
    scale: None | str = None,
    digits: None | int = None,
    label: None | str = None,
    ndivs: None | int = None,
    lwidth: None | int = None,
    lheight: None | int = None,
    decades: None | int = None,
    multiplier: None | float = None,
    palette: None | str = None,
    redv: None | str = None,
    grnv: None | str = None,
    bluv: None | str = None,
) -> bytes:
    """
    Generate a falsecolor Radiance picture.

    Args:
        inp: Path or bytes to input picture file.
        pic_overlay: Path to another picture to overlay with contours.
        contour: Type of contour ('b' for bands, 'l' for lines, 'p' for posterization).
        extrema: Flag to print extrema points on the brightest and darkest pixels.
        scale: Scale for the false color (e.g., 'auto' or specific scale).
        digits: Max number of decimal places for legend entries.
        label: Label for the new image.
        ndivs: Number of contours and corresponding legend entries.
        lwidth: Width of the legend.
        lheight: Height of the legend.
        decades: Number of decades below the maximum scale for logarithmic mapping.
        multiplier: Multiplier for the scale (e.g., to convert units).
        palette: Color palette to use for false color.
        redv: Expression for mapping values to red.
        grnv: Expression for mapping values to green.
        bluv: Expression for mapping values to blue.

    Returns:
        bytes: Output of falsecolor.
    """
    cmd = [str(BINPATH / "falsecolor")]

    # In the man-page, it is mentioned that stdin is used if no input file is specified.
    if isinstance(inp, (str, Path)):
        cmd.extend(["-i", str(inp)])
        stdin = None
    else:
        stdin = inp

    if pic_overlay:
        cmd.extend(["-p", pic_overlay])

    if contour:
        if contour in ["b", "l", "p"]:
            cmd.append(f"-c{contour}")
        else:
            raise ValueError(
                "Invalid value for contour. Allowed values are 'b', 'l', or 'p'."
            )

    if extrema:
        cmd.append("-e")

    if scale:
        cmd.extend(["-s", scale])

    if digits is not None:
        cmd.extend(["-d", str(digits)])

    if label:
        cmd.extend(["-l", label])

    if ndivs is not None:
        cmd.extend(["-n", str(ndivs)])

    if lwidth is not None:
        cmd.extend(["-lw", str(lwidth)])

    if lheight is not None:
        cmd.extend(["-lh", str(lheight)])

    if decades is not None:
        cmd.extend(["-log", str(decades)])

    if multiplier is not None:
        cmd.extend(["-m", str(multiplier)])

    if palette:
        cmd.extend(["-pal", palette])

    if redv:
        cmd.extend(["-r", redv])

    if grnv:
        cmd.extend(["-g", grnv])

    if bluv:
        cmd.extend(["-b", bluv])

    return sp.run(cmd, stdout=sp.PIPE, check=True, input=stdin).stdout
