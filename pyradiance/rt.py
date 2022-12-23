"""
Radiannce rendering programs
=============
This module contains the main API for pyradiance.
"""

from dataclasses import dataclass
from pathlib import Path
import os
import shlex
import subprocess as sp
import sys
from typing import List, Optional, Union, Tuple

from .parameter import Levels, SamplingParameters
from .model import Primitive, Scene, View
from .parsers import parse_rtrace_args

from .cal import cnt
from .ot import getbbox, oconv
from .util import append_to_header, rad, vwrays


BINPATH = Path(__file__).parent / "bin"


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


@dataclass
class Modifier:
    """Modifier for rcontrib command.

    Args:
        modifier: Modifier name.
        value: Modifier value.
    """

    modifier = None
    modifier_path = None
    calfile = None
    expression = None
    nbins = None
    binv = None
    param = None
    xres = None
    yres = None
    output = None

    def args(self):
        """Return modifier as a list of arguments."""
        arglist = []
        if self.calfile is not None:
            arglist.extend(["-f", str(self.calfile)])
        if self.expression is not None:
            arglist.extend(["-e", str(self.expression)])
        if self.nbins is not None:
            arglist.extend(["-bn", str(self.nbins)])
        if self.binv is not None:
            arglist.extend(["-b", str(self.binv)])
        if self.param is not None:
            arglist.extend(["-p", str(self.param)])
        if self.xres is not None:
            arglist.extend(["-x", str(self.xres)])
        if self.yres is not None:
            arglist.extend(["-y", str(self.yres)])
        if self.output is not None:
            arglist.extend(["-o", str(self.output)])
        if self.modifier is not None:
            arglist.extend(["-m", self.modifier])
        elif self.modifier_path is not None:
            arglist.extend(["-M", self.modifier_path])
        else:
            raise ValueError("Modifier or modifier path must be provided.")
        return arglist


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
    cmd = ["rpict"]
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
    version: bool = False,
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
    cmd = ["rtrace"]
    if version:
        cmd.append("-version")
        return sp.run(cmd, check=True, stdout=sp.PIPE).stdout
    if not isinstance(rays, bytes):
        raise TypeError("Rays must be bytes")
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
