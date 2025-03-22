from dataclasses import dataclass
import math
import os
import random
import string
import shutil
import tempfile
from typing import Optional, Literal

from .util import rmtxop, rfluxmtx, strip_header, WrapBSDF, Xform
from .ot import oconv, getbbox
from .gen import genblinds
from .model import Primitive


@dataclass(slots=True)
class Dimension:
    xmin: float = 0
    xmax: float = 0
    ymin: float = 0
    ymax: float = 0
    zmin: float = 0
    zmax: float = 0


@dataclass(slots=True)
class BSDFResult:
    tf: bytes = b""
    tb: bytes = b""
    rf: bytes = b""
    rb: bytes = b""


@dataclass(slots=True)
class BlindsGeometry:
    depth: float = 0
    width: float = 0
    height: float = 0
    nslats: int = 0
    angle: float = 0
    rcurv: float = 0
    unit: str = "meter"


# TODO: support full color/spectral material
# TODO: support translucent material
@dataclass(slots=True)
class ShadingMaterial:
    diffuse_reflectance: float = 0
    specular_reflectance: float = 0
    roughness: float = 0


def generate_blinds_from_cross_section():
    pass


def generate_blinds(mat: ShadingMaterial, geom: BlindsGeometry) -> bytes:
    fargs = [
        mat.diffuse_reflectance,
        mat.diffuse_reflectance,
        mat.diffuse_reflectance,
        mat.specular_reflectance,
        mat.roughness,
    ]
    mat_random_strings = "".join(
        random.choices(string.ascii_letters + string.digits, k=5)
    )
    name_random_strings = "".join(
        random.choices(string.ascii_letters + string.digits, k=8)
    )
    material_name = f"blinds_material_{mat_random_strings}"
    blinds_name = f"blinds_{name_random_strings}"
    material = Primitive("void", "plastic", material_name, [], fargs)
    blinds = genblinds(
        material_name,
        blinds_name,
        geom.depth,
        geom.width,
        geom.height,
        geom.nslats,
        geom.angle,
        geom.rcurv,
    )
    # xform -rz -90 -rx -90 -t 0 0 -0.939693
    thickness = geom.depth * math.cos(math.radians(geom.angle))
    return (
        material.bytes
        + Xform(blinds).rotatez(-90).rotatex(-90).translate(0, 0, -thickness)()
    )


def write_senders_receiver(
    fsender: str,
    bsender: str,
    receiver: str,
    facedat: str,
    behinddat: str,
    basis: str,
    dim: Dimension,
):
    FEPS = 1e-6
    header_templ = "#@rfluxmtx {hemis} {up} {out}\n\n"
    receiver_templ = (
        "{face_header}"
        "void glow receiver_face\n0\n0\n4 1 1 1 0\n\n"
        "receiver_face source f_receiver\n0\n0\n4 0 0 1 180\n\n"
        "{behind_header}"
        "void glow receiver_behind\n0\n0\n4 1 1 1 0\n\n"
        "receiver_behind source b_receiver\n0\n0\n4 0 0 -1 180\n"
    )
    fsender_templ = (
        "{header}"
        "void polygon fwd_sender\n0\n0\n12\n"
        "\t{xmin}\t{ymin}\t{zmin}\n"
        "\t{xmin}\t{ymax}\t{zmin}\n"
        "\t{xmax}\t{ymax}\t{zmin}\n"
        "\t{xmax}\t{ymin}\t{zmin}\n"
    )
    bsender_templ = (
        "{header}"
        "void polygon fwd_sender\n0\n0\n12\n"
        "\t{xmin}\t{ymin}\t{zmax}\n"
        "\t{xmax}\t{ymin}\t{zmax}\n"
        "\t{xmax}\t{ymax}\t{zmax}\n"
        "\t{xmin}\t{ymax}\t{zmax}\n"
    )

    face_out = f"o={facedat}"
    behind_out = f"o={behinddat}"
    up = ""
    if basis == "u":
        face_hemis = behind_hemis = "h=u"
    else:
        face_hemis = f"h=-{basis}"
        behind_hemis = f"h=+{basis}"
        up = "u=-Y"

    with open(receiver, "w") as f:
        f.write(
            receiver_templ.format(
                face_header=header_templ.format(hemis=face_hemis, up=up, out=face_out),
                behind_header=header_templ.format(
                    hemis=behind_hemis, up=up, out=behind_out
                ),
            )
        )
    with open(fsender, "w") as f:
        f.write(
            fsender_templ.format(
                header=header_templ.format(up=up, hemis=face_hemis, out=""),
                xmin=dim.xmin,
                xmax=dim.xmax,
                ymin=dim.ymin,
                ymax=dim.ymax,
                zmin=dim.zmin - FEPS,
            )
        )
    with open(bsender, "w") as f:
        f.write(
            bsender_templ.format(
                header=header_templ.format(up=up, hemis=behind_hemis, out=""),
                xmin=dim.xmin,
                xmax=dim.xmax,
                ymin=dim.ymin,
                ymax=dim.ymax,
                zmax=dim.zmax + FEPS,
            )
        )


# TODO: Add tensortree out
# TODO: Add color out
def generate_bsdf(
    *inp,
    unit=None,
    params: Optional[list[str]] = None,
    recip=True,
    nsamp=2000,
    pctcull=90,
    nproc=1,
    geout=True,
    basis: Literal["kf", "kh", "kq", "u", "r1", "r2", "r4"] = "kf",
    dim: Optional[Dimension] = None,
) -> BSDFResult:
    result = BSDFResult()

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
    param_args.extend(["-n", str(nproc)])

    geout = 1

    device = Xform(*inp)()

    # NOTE: getbbox -h -w device.rad
    dim = Dimension(*getbbox(device, warning=False)) if dim is None else dim

    if dim.zmin >= 0:
        print("Device entirely inside room!")
        return
    if dim.zmax > 1e-5:
        print("Warning: Device extends into room")
    elif dim.zmax * dim.zmax > 0.01 * (dim.xmax - dim.xmin) * (dim.ymax - dim.ymin):
        print("Warning: Device far behind Z==0 plane")

    nx = int(math.sqrt(nsamp * (dim.xmax - dim.xmin) / (dim.ymax - dim.ymin)) + 1)
    ny = int(nsamp / nx + 1)
    param_args.extend(["-c", str(nx * ny)])
    param_args.extend(["-cs", "3"])

    with open(octree, "wb") as fp:
        fp.write(oconv(stdin=device, warning=False))

    # TODO: handle geometry output
    if geout:
        # NOTE: rad2mgf device >> mgfscn
        pass

    write_senders_receiver(fsender, bsender, receivers, facedat, behinddat, basis, dim)

    visible_coeffs = (0.2651, 0.6701, 0.0648)
    param_args.append("-fd")
    # backward:
    rfluxmtx(
        surface=bsender,
        receiver=receivers,
        octree=octree,
        params=param_args,
    )
    result.tb = strip_header(rmtxop(behinddat, transpose=True, transform=visible_coeffs))
    result.rb = strip_header(rmtxop(facedat, transpose=True, transform=visible_coeffs))

    # forward:
    rfluxmtx(
        surface=fsender,
        receiver=receivers,
        octree=octree,
        params=param_args,
    )
    result.tf = strip_header(rmtxop(facedat, transpose=True, transform=visible_coeffs))
    result.rf = strip_header(rmtxop(behinddat, transpose=True, transform=visible_coeffs))

    shutil.rmtree(tempdir)
    return result


def generate_xml(
    sol_results=None,
    vis_results=None,
    ir_results=None,
    basis="kf",
    unit="meter",
    **kwargs,
) -> bytes:
    emissivity_front = emissivity_back = 1.0
    if ir_results is not None:
        emissivity_front = 1 - float(ir_results.tf) - float(ir_results.rf)
        emissivity_back = 1 - float(ir_results.tb) - float(ir_results.rb)

    wrapper = WrapBSDF(
        basis=basis,
        correct_solid_angle=True,
        unit=unit,
        unlink=True,
        ef=emissivity_front,
        eb=emissivity_back,
        **kwargs,
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


Point3D = tuple[float, float, float]
Rectangle3D = tuple[Point3D, Point3D, Point3D, Point3D]


def generate_blinds_bsdf_for_windows(
    window_rects: list[Rectangle3D],
    slat_depth: float,
    nslats: int,
    slat_angle: list[float],
    slat_rcurv: float,
    diff_refl: float,
    spec_refl: float,
    ir_refl: float,
    roughness: float,
):
    FEPS = 1e-5
    window_dimensions: list[tuple[float, float]] = []
    for window_rect in window_rects:
        zdiff1 = abs(window_rect[1][2] - window_rect[0][2])
        zdiff2 = abs(window_rect[2][2] - window_rect[1][2])
        dim1 = math.sqrt(
            sum((window_rect[1][i] - window_rect[0][i]) ** 2 for i in range(3))
        )
        dim2 = math.sqrt(
            sum((window_rect[2][i] - window_rect[1][i]) ** 2 for i in range(3))
        )
        if zdiff1 <= FEPS:
            window_dimensions.append((dim1, dim2))
        elif zdiff2 <= FEPS:
            window_dimensions.append((dim2, dim1))
        else:
            print("Error: Skewed window not supported: ")
            print(window_rect)
            return
    return generate_blinds_bsdf(
        slat_depth,
        window_width,
        window_height,
        nslats,
        slat_angle,
        slat_rcurv,
        diff_refl,
        spec_refl,
        ir_refl,
        roughness,
    )
