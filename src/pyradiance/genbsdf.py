from dataclasses import dataclass, field
import math
import os
import random
import string
import shutil
import tempfile
from typing import Literal, NamedTuple

from .util import Rmtxop, rfluxmtx, strip_header, WrapBSDF, Xform
from .ot import oconv, getbbox
from .gen import genblinds
from .model import Primitive

BasisType = Literal["kf", "kh", "kq", "u", "r1", "r2", "r4"]
OutSpec = Literal["rgb", "xyz", "y", "m", "s"] 


class SamplingBox(NamedTuple):
    xmin: float = 0
    xmax: float = 0
    ymin: float = 0
    ymax: float = 0
    zmin: float = 0
    zmax: float = 0


@dataclass(slots=True)
class SDFDataBytes:
    transmittance: bytes = b""
    reflectance: bytes = b""


@dataclass(slots=True)
class BSDFDataBytes:
    front: SDFDataBytes = field(default_factory=lambda: SDFDataBytes())
    back: SDFDataBytes = field(default_factory=lambda: SDFDataBytes())


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
    mat_fargs = [
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
        random.choices(string.ascii_letters + string.digits, k=5)
    )
    material_name = f"blinds_material_{mat_random_strings}"
    blinds_name = f"blinds_{name_random_strings}"
    material = Primitive("void", "plastic", material_name, [], mat_fargs)
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
    return material.bytes + blinds


def generate_blinds_for_bsdf(mat: ShadingMaterial, geom: BlindsGeometry) -> bytes:
    prims = generate_blinds(mat, geom)
    thickness = geom.depth * math.cos(math.radians(geom.angle))
    return Xform(prims).rotatez(-90).rotatex(-90).translate(0, 0, -thickness)()


def get_basis_and_up(basis: BasisType) -> tuple[str, str, str]:
    if basis == "u":
        face_hemis = behind_hemis = f"h={basis}"
        up = ""
    else:
        face_hemis = f"h=-{basis}"
        behind_hemis = f"h=+{basis}"
        up = "u=-Y"
    return face_hemis, behind_hemis, up


def get_sampling_box(
    device: str | bytes, dim: None | SamplingBox = None
) -> SamplingBox:
    dim = SamplingBox(*getbbox(device, warning=False)) if dim is None else dim

    if dim.zmin >= 0:
        print("Device entirely inside room!")
    if dim.zmax > 1e-5:
        print("Warning: Device extends into room")
    elif dim.zmax * dim.zmax > 0.01 * (dim.xmax - dim.xmin) * (dim.ymax - dim.ymin):
        print("Warning: Device far behind Z==0 plane")
    return dim


def get_hemisphere_receivers(
    face_hemis: str,
    behind_hemis: str,
    up: str,
    face_out: str = "",
    behind_out: str = "",
):
    face_receiver = (
        f"#@rfluxmtx {face_hemis} {up} o={face_out}\n\n"
        "void glow receiver_face\n0\n0\n4 1 1 1 0\n\n"
        f"receiver_face source f_receiver\n0\n0\n4 0 0 1 180\n\n"
    )
    behind_receiver = (
        f"#@rfluxmtx {behind_hemis} {up} o={behind_out}\n\n"
        "void glow receiver_behind\n0\n0\n4 1 1 1 0\n\n"
        f"receiver_behind source b_receiver\n0\n0\n4 0 0 -1 180\n\n"
    )
    return face_receiver, behind_receiver


def get_sender(hemis: str, up: str, dim: SamplingBox, front: bool) -> str:
    FEPS = 1e-6
    sender = f"#@rfluxmtx {hemis} {up}\n\nvoid polygon sender\n0\n0\n12\n"
    if front:
        sender += (
            f"\t{dim.xmin}\t{dim.ymin}\t{dim.zmin - FEPS}\n"
            f"\t{dim.xmin}\t{dim.ymax}\t{dim.zmin - FEPS}\n"
            f"\t{dim.xmax}\t{dim.ymax}\t{dim.zmin - FEPS}\n"
            f"\t{dim.xmax}\t{dim.ymin}\t{dim.zmin - FEPS}\n"
        )
    else:
        sender += (
            f"\t{dim.xmin}\t{dim.ymin}\t{dim.zmax + FEPS}\n"
            f"\t{dim.xmax}\t{dim.ymin}\t{dim.zmax + FEPS}\n"
            f"\t{dim.xmax}\t{dim.ymax}\t{dim.zmax + FEPS}\n"
            f"\t{dim.xmin}\t{dim.ymax}\t{dim.zmax + FEPS}\n"
        )
    return sender


# TODO: handle colored BSDF out
def generate_sdf(
    sender: str,
    receiver: str,
    octree_file: str,
    tmpdir: str,
    transdat: str,
    refldat: str,
    params: None | list[str] = None,
    outspec: OutSpec = "y",
) -> SDFDataBytes:
    receiver_file = os.path.join(tmpdir, "receiver.rad")
    with open(receiver_file, "w") as f:
        f.write(receiver)
    sender_file = os.path.join(tmpdir, "sender.rad")
    with open(sender_file, "w") as f:
        f.write(sender)

    rfluxmtx(
        surface=sender_file,
        receiver=receiver_file,
        octree=octree_file,
        params=params,
    )
    trans = strip_header(
        Rmtxop().add_input(transdat, transpose=True, transform=outspec)()
    )
    refl = strip_header(
        Rmtxop().add_input(refldat, transpose=True, transform=outspec)()
    )
    return SDFDataBytes(transmittance=trans, reflectance=refl)


def generate_front_sdf(
    octree_file: str,
    basis: BasisType,
    dim: SamplingBox,
    tmpdir: str,
    params: None | list[str] = None,
    outspec: OutSpec = "y",
):
    facedat = os.path.join(tmpdir, "face.dat")
    behinddat = os.path.join(tmpdir, "behind.dat")
    face_hemis, behind_hemis, up = get_basis_and_up(basis)
    face_receiver, behind_receiver = get_hemisphere_receivers(
        face_hemis=face_hemis,
        behind_hemis=behind_hemis,
        up=up,
        face_out=facedat,
        behind_out=behinddat,
    )
    receiver = face_receiver + behind_receiver
    sender: str = get_sender(face_hemis, up, dim, True)
    return generate_sdf(
        sender,
        receiver,
        octree_file,
        tmpdir,
        transdat=facedat,
        refldat=behinddat,
        params=params,
        outspec=outspec,
    )


def generate_back_sdf(
    octree_file: str,
    basis: BasisType,
    dim: SamplingBox,
    tmpdir: str,
    params: None | list[str] = None,
    outspec: OutSpec = "y",
):
    facedat = os.path.join(tmpdir, "face.dat")
    behinddat = os.path.join(tmpdir, "behind.dat")
    face_hemis, behind_hemis, up = get_basis_and_up(basis)
    face_receiver, behind_receiver = get_hemisphere_receivers(
        face_hemis=face_hemis,
        behind_hemis=behind_hemis,
        up=up,
        face_out=facedat,
        behind_out=behinddat,
    )
    receiver = behind_receiver + face_receiver
    sender: str = get_sender(behind_hemis, up, dim, False)
    return generate_sdf(
        sender,
        receiver,
        octree_file,
        tmpdir,
        transdat=behinddat,
        refldat=facedat,
        params=params,
        outspec=outspec,
    )


# TODO: Add tensortree out
# TODO: Add color out
def generate_bsdf(
    *inp,
    params: None | list[str] = None,
    recip=True,
    nsamp=2000,
    pctcull=90,
    nproc=1,
    geout=True,
    nspec: int = 3,
    working_dir: str = "",
    basis: BasisType = "kf",
    dim: None | SamplingBox = None,
    front: bool = True,
    outspec: OutSpec = "y",
    cleanup: bool = True,
) -> BSDFDataBytes:
    result = BSDFDataBytes()
    param_args = ["-ab", "5", "-ad", "700", "-lw", "3e-6", "-w-"]
    if params is not None:
        param_args.extend(params)
    param_args.extend(["-n", str(nproc)])

    device = Xform(*inp)()
    dim = get_sampling_box(device=device, dim=dim)

    nx = int(math.sqrt(nsamp * (dim.xmax - dim.xmin) / (dim.ymax - dim.ymin)) + 1)
    ny = int(nsamp / nx + 1)
    param_args.extend(["-c", str(nx * ny)])
    param_args.extend(["-cs", str(nspec)])

    if working_dir == "":
        working_dir = tempfile.mkdtemp(prefix="genBSDF")

    working_dir = tempfile.mkdtemp(prefix="genBSDF")
    octree_file = os.path.join(working_dir, "device.oct")
    with open(octree_file, "wb") as fp:
        fp.write(oconv(stdin=device, warning=False))

    param_args.append("-fd")
    result.back = generate_back_sdf(octree_file, basis, dim, working_dir, params=param_args, outspec=outspec)
    if front:
        result.front = generate_front_sdf(
            octree_file, basis, dim, working_dir, params=param_args, outspec=outspec
        )

    os.remove(octree_file)
    if cleanup:
        shutil.rmtree(working_dir)
    return result


def generate_xml(
    sol_results: None | BSDFDataBytes = None,
    vis_results: None | BSDFDataBytes = None,
    ir_results: None | BSDFDataBytes = None,
    basis: str = "kf",
    unit: str = "meter",
    **kwargs,
) -> bytes:
    emissivity_front = emissivity_back = 1.0
    if ir_results is not None:
        emissivity_front = (
            1
            - float(ir_results.front.transmittance)
            - float(ir_results.front.reflectance)
        )
        emissivity_back = (
            1
            - float(ir_results.back.transmittance)
            - float(ir_results.back.reflectance)
        )

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
            f.write(sol_results.front.transmittance)

        fd, tbs = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(sol_results.back.transmittance)

        fd, rfs = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(sol_results.front.reflectance)

        fd, rbs = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(sol_results.back.reflectance)

        wrapper = wrapper.add_solar(tb=tbs, tf=tfs, rb=rbs, rf=rfs)

    if vis_results is not None:
        fd, tfv = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(vis_results.front.transmittance)

        fd, tbv = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(vis_results.back.transmittance)

        fd, rfv = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(vis_results.front.reflectance)

        fd, rbv = tempfile.mkstemp(suffix=".dat")
        with os.fdopen(fd, "wb") as f:
            f.write(vis_results.back.reflectance)
        wrapper = wrapper.add_visible(tb=tbv, tf=tfv, rb=rbv, rf=rfv)

    return wrapper()
