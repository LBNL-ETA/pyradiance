from dataclasses import dataclass
import os
import tempfile
import shutil
from typing import Optional, Literal

from .util import rmtxop, rfluxmtx, strip_header, WrapBSDF
from .cv import xform, getbbox
from .ot import oconv
from .gen import genblinds


@dataclass
class Dimension:
    __slots__ = ["xmin", "xmax", "ymin", "ymax", "zmin", "zmax"]
    xmin: float = 0
    xmax: float = 0
    ymin: float = 0
    ymax: float = 0
    zmin: float = 0
    zmax: float = 0


@dataclass
class BSDFResult:
    __slots__ = ["tf", "tb", "rf", "rb"]
    tf: bytes = b""
    tb: bytes = b""
    rf: bytes = b""
    rb: bytes = b""


@dataclass
class BlindsGeometry:
    __slots__ = ["depth", "width", "height", "nslats", "angle", "rcurv"]
    depth: float = 0
    width: float = 0
    height: float = 0
    nslats: int = 0
    angle: float = 0
    rcurv: float = 0
    unit: str = "meter"


@dataclass
class ShadingMaterial:
    diffuse_reflectance: float = 0
    specular_reflectance: float = 0
    roughness: float = 0


def generate_blinds_from_cross_section():
    pass


def generate_blinds(mat: ShadingMaterial, geom: BlindsGeometry):
    blinds = genblinds(
        geom.depth,
        geom.width,
        geom.width,
        geom.height,
        geom.nslats,
        geom.angle,
        geom.rcurv,
    )
    return mat + blinds


def write_senders_receiver(
    fsender, bsender, receiver, facedat, behinddat, basis, dim: Dimension
):
    FEPS = 1e-6
    receiver_str = (
        f"#@rfluxmtx h=-{basis}\n"
        f"#@rfluxmtx u=-Y o={facedat}\n\n"
        "void glow receiver_face\n0\n0\n4 1 1 1 0\n\n"
        "receiver_face source f_receiver\n0\n0\n4 0 0 1 180\n\n"
        f"#@rfluxmtx h=+{basis}\n"
        f'#@rfluxmtx "u=-Y o={behinddat}\n\n"'
        "void glow receiver_behind\n0\n0\n4 1 1 1 0\n\n"
        "receiver_behind source b_receiver\n0\n0\n4 0 0 -1 180\n"
    )
    with open(receiver, "w") as f:
        f.write(receiver_str)

    fsender_str = (
        f"#@rfluxmtx u=-Y h=-{basis}\n\n"
        "void polygon fwd_sender\n0\n0\n12\n"
        f"\t{dim.xmin}\t{dim.ymin}\t{dim.zmin - FEPS}\n"
        f"\t{dim.xmin}\t{dim.ymax}\t{dim.zmin - FEPS}\n"
        f"\t{dim.xmax}\t{dim.ymax}\t{dim.zmin - FEPS}\n"
        f"\t{dim.xmax}\t{dim.ymin}\t{dim.zmin - FEPS}\n"
    )
    with open(fsender, "w") as f:
        f.write(fsender_str)

    bsender_str = (
        f"#@rfluxmtx u=-Y h=+{basis}\n\n"
        "void polygon bwd_sender\n0\n0\n12\n"
        f"\t{dim.xmin}\t{dim.ymin}\t{dim.zmax + FEPS}\n"
        f"\t{dim.xmax}\t{dim.ymin}\t{dim.zmax + FEPS}\n"
        f"\t{dim.xmax}\t{dim.ymax}\t{dim.zmax + FEPS}\n"
        f"\t{dim.xmin}\t{dim.ymax}\t{dim.zmax + FEPS}\n"
    )
    with open(bsender, "w") as f:
        f.write(bsender_str)


# TODO: Add tensortree out
# TODO: Add color out
def generate_bsdf(
    *inp,
    unit=None,
    params: Optional[list[str]] = None,
    forward=False,
    backward=True,
    color=False,
    recip=True,
    nsamp=2000,
    pctcull=90,
    nproc=1,
    geout=True,
    gunit="meter",
    basis: Literal["kf", "kh", "kq", "u", "r1", "r2", "r4"] = "kf",
    dim: Optional[Dimension] = None,
) -> BSDFResult:
    result = BSDFResult()

    if not backward and not forward:
        print("Neither forward nor backward calculation requested")
        return result

    tempdir = tempfile.mkdtemp()
    octree = os.path.join(tempdir, "device.oct")
    fsender = os.path.join(tempdir, "fsender.rad")
    bsender = os.path.join(tempdir, "bsender.rad")
    receivers = os.path.join(tempdir, "receivers.rad")
    facedat = os.path.join(tempdir, "face.dat")
    behinddat = os.path.join(tempdir, "behind.dat")

    param_args = ["-ab", "5", "-ad", "700", "-lw", "3e-6", "-w-"]
    if params is not None:
        param_args.extend(params)
    geout = 1

    device = xform(inp)

    # NOTE: getbbox -h -w device.rad
    if dim is None:
        dims = getbbox(device)
        dim = Dimension(*dims)

    if dim.zmin >= 0:
        print("Device entirely inside room!")
        return
    if dim.zmax > 1e-5:
        print("Warning: Device extends into room")
    elif dim.zmax * dim.zmax > 0.01 * (dim.xmax - dim.xmin) * (dim.ymax - dim.ymin):
        print("Warning: Device far behind Z==0 plane")

    with open(octree, "wb") as fp:
        fp.write(oconv(device, warning=False))

    # TODO: handle geometry output
    if geout:
        # NOTE: rad2mgf device >> mgfscn
        pass

    write_senders_receiver(fsender, bsender, receivers, facedat, behinddat, basis, dim)

    # backward:
    rfluxmtx(
        surface=bsender,
        outform="d",
        receivers=receivers,
        octree=octree,
        params=param_args,
    )
    result.tb = strip_header(rmtxop(behinddat, transform=(0.2651, 0.6701, 0.0648)))
    result.rb = strip_header(rmtxop(facedat, transform=(0.2651, 0.6701, 0.0648)))

    # forward:
    rfluxmtx(
        surface=fsender,
        outform="d",
        receivers=receivers,
        octree=octree,
        params=param_args,
    )
    result.tf = strip_header(rmtxop(facedat, transform=(0.2651, 0.6701, 0.0648)))
    result.rf = strip_header(rmtxop(behinddat, transform=(0.2651, 0.6701, 0.0648)))

    shutil.rmtree(tempdir)
    return result


def generate_xml(
    sol_results=None,
    vis_results=None,
    ir_results=None,
    basis="kf",
    name="unnamed",
    manufacturer="unnamed",
    unit="meter",
    thickness=0,
) -> Optional[bytes]:
    emissivity_front = 1
    emissivity_back = 1
    if ir_results is not None:
        emissivity_front = 1 - float(ir_results.tf) - float(ir_results.rf)
        emissivity_back = 1 - float(ir_results.tb) - float(ir_results.rb)

    wrapper = WrapBSDF(
        basis=basis,
        enforce_window=True,
        correct_solid_angle=True,
        unit=unit,
        unlink=True,
        n=name,
        m=manufacturer,
        thickness=thickness,
        ef=emissivity_front,
        eb=emissivity_back,
    )

    if sol_results is not None:
        fd, tfs = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(sol_results.tf)

        fd, tbs = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(sol_results.tb)

        fd, rfs = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(sol_results.rf)

        fd, rbs = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(sol_results.rb)

        wrapper = wrapper.add_solar(tb=tbs, tf=tfs, rb=rbs, rf=rfs)

    if vis_results is not None:
        fd, tfv = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(vis_results.tf)

        fd, tbv = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(vis_results.tb)

        fd, rfv = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(vis_results.rf)

        fd, rbv = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(vis_results.rb)
        wrapper = wrapper.add_visible(tb=tbv, tf=tfv, rb=rbv, rf=rfv)

    return wrapper()
