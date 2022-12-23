"""
Radiance utilities
"""

from pathlib import Path
import subprocess as sp
from typing import List, Optional, Tuple, Union

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


def strip_header(inp) -> bytes:
    """Use getinfo to strip the header from a Radiance file."""
    cmd = ["getinfo", "-"]
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
