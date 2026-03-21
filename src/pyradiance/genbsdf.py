from dataclasses import dataclass, field
import math
import os
import random
import string
import shutil
import tempfile
from typing import Literal, NamedTuple

from .cal import cnt, rcalc
from .util import Rcomb, Rmtxop, rfluxmtx, rttree_reduce, strip_header, WrapBSDF, Xform
from .ot import oconv, getbbox
from .gen import genblinds
from .model import Primitive

BasisType = Literal["kf", "kh", "kq", "u", "r1", "r2", "r4"]
OutSpec = Literal["rgb", "xyz", "y", "m", "s"]
TensorTreeType = Literal[0, 3, 4]


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


def _get_tensortree_hemis(ns: int) -> tuple[str, str, str]:
    """Return (face_hemis, behind_hemis, up) strings for tensor tree sampling."""
    return f"h=-sc{ns}", f"h=+sc{ns}", "u=-Y"


def _generate_isotropic_rays(
    ns: int, nx: int, ny: int, dim: SamplingBox, forw: bool
) -> bytes:
    """Generate ray bytes for t3 isotropic tensor tree sampling via cnt|rcalc pipeline.

    Args:
        ns: tensor tree resolution (2**ttlog2)
        nx: number of x sample positions
        ny: number of y sample positions
        dim: scene bounding box
        forw: True for front (forward), False for back

    Returns:
        Ray bytes suitable for rfluxmtx stdin
    """
    ns2 = ns // 2
    zp = dim.zmin if forw else dim.zmax
    dz_sign = 1 if forw else -1
    cnt_bytes = cnt(ns2, ny, nx)
    expr = ";".join([
        "r1=rand(.8681*recno-.673892)",
        "r2=rand(-5.37138*recno+67.1737811)",
        "r3=rand(+3.17603772*recno+83.766771)",
        "r4=rand(-1.5839226*recno-59.82712)",
        "odds(n):if(.5*n-floor(.5*n)-.25,-1,1)",
        f"Dx=1-($1+r1)/{ns2}",
        f"Dy=min(1/{ns},sqrt(1-Dx*Dx))*odds($1)*r2",
        "Dz=sqrt(1-Dx*Dx-Dy*Dy)",
        f"xp=($3+r3)*(({dim.xmax}-{dim.xmin})/{nx})+{dim.xmin}",
        f"yp=($2+r4)*(({dim.ymax}-{dim.ymin})/{ny})+{dim.ymin}",
        f"zp={zp}",
        f"myDz=Dz*{dz_sign}",
        "$1=xp-Dx;$2=yp-Dy;$3=zp-myDz",
        "$4=Dx;$5=Dy;$6=myDz",
    ])
    outform = None if os.name == "nt" else "f"
    return rcalc(cnt_bytes, outform=outform, expr=expr)


def _ttree_comp(
    src: str,
    dest: str,
    tensortree: int,
    ttlog2: int,
    ns: int,
    pctcull: float,
    reciprocal: bool,
    is_trans: bool,
) -> None:
    """Post-process rfluxmtx output to tensor tree format.

    Runs Rcomb | strip_header | rcalc | rttree_reduce pipeline and writes
    the result to dest.

    Args:
        src: path to rfluxmtx output .dat file (RGB flux)
        dest: path to write tensor tree output
        tensortree: 3 (isotropic) or 4 (anisotropic)
        ttlog2: log2 of tree resolution
        ns: tree resolution (2**ttlog2)
        pctcull: culling percentage for rttree_reduce
        reciprocal: apply reciprocity averaging
        is_trans: True for transmission component, False for reflection
    """
    inform = None if os.name == "nt" else "f"
    fmt = "a" if os.name == "nt" else "f"

    # Convert RGB flux to XYZ and strip Radiance header
    xyz_data = Rcomb(outform=fmt, transform="xyz").add_input(src)()
    stripped = strip_header(xyz_data)

    # Extract Y luminance normalized by solid angle Omega = pi/ns^2
    expr = f"Xi=$1;Yi=$2;Zi=$3;Omega:PI/({ns}*{ns});$1=Yi/Omega"
    luminance = rcalc(stripped, inform=inform, incount=3, outform=fmt, expr=expr)

    # Reciprocity: always for t3; for t4 only on reflection components
    use_recip = reciprocal and (tensortree == 3 or not is_trans)
    tree_data = rttree_reduce(
        luminance,
        ttree=tensortree,
        log2res=ttlog2,
        pctcull=pctcull,
        inform=fmt,
        reciprocal=use_recip,
        header=False,
    )

    with open(dest, "wb") as f:
        f.write(tree_data)


def generate_tensortree_sdf(
    forw: bool,
    tensortree: int,
    ttlog2: int,
    octree_file: str,
    dim: SamplingBox,
    nx: int,
    ny: int,
    tmpdir: str,
    params: list[str],
    pctcull: float = 90,
    recip: bool = True,
) -> SDFDataBytes:
    """Generate SDF data using tensor tree sampling.

    Args:
        forw: True for front (forward) side, False for back
        tensortree: 3 (isotropic) or 4 (anisotropic)
        ttlog2: log2 of sampling resolution (ns = 2**ttlog2)
        octree_file: path to compiled scene octree
        dim: scene bounding box
        nx: number of x sample positions
        ny: number of y sample positions
        tmpdir: working directory for temporary files
        params: rfluxmtx parameters (must include format flag)
        pctcull: culling percentage for rttree_reduce (< 100)
        recip: apply reciprocity averaging in rttree_reduce

    Returns:
        SDFDataBytes with transmittance and reflectance as tensor tree bytes
    """
    ns = 2**ttlog2
    face_hemis, behind_hemis, up = _get_tensortree_hemis(ns)

    facedat = os.path.join(tmpdir, "face.dat")
    behinddat = os.path.join(tmpdir, "behind.dat")

    face_receiver, behind_receiver = get_hemisphere_receivers(
        face_hemis=face_hemis,
        behind_hemis=behind_hemis,
        up=up,
        face_out=facedat,
        behind_out=behinddat,
    )
    receiver_file = os.path.join(tmpdir, "receiver.rad")
    with open(receiver_file, "w") as f:
        f.write(face_receiver + behind_receiver)

    if tensortree == 3:
        # Isotropic: cnt|rcalc pipeline generates rays, passed as rfluxmtx stdin
        ns2 = ns // 2
        rays = _generate_isotropic_rays(ns, nx, ny, dim, forw)
        rfluxmtx(
            receiver=receiver_file,
            rays=rays,
            octree=octree_file,
            params=params + ["-y", str(ns2)],
        )
    else:
        # Anisotropic (t4): polygon sender with tensor tree hemisphere basis
        sender_hemis = face_hemis if forw else behind_hemis
        sender = get_sender(sender_hemis, up, dim, forw)
        sender_file = os.path.join(tmpdir, "sender.rad")
        with open(sender_file, "w") as f:
            f.write(sender)
        rfluxmtx(
            receiver=receiver_file,
            surface=sender_file,
            octree=octree_file,
            params=params,
        )

    transdat, refldat = (facedat, behinddat) if forw else (behinddat, facedat)
    trans_dest = os.path.join(tmpdir, "trans.dat")
    refl_dest = os.path.join(tmpdir, "refl.dat")

    _ttree_comp(transdat, trans_dest, tensortree, ttlog2, ns, pctcull, recip, is_trans=True)
    _ttree_comp(refldat, refl_dest, tensortree, ttlog2, ns, pctcull, recip, is_trans=False)

    with open(trans_dest, "rb") as f:
        trans = f.read()
    with open(refl_dest, "rb") as f:
        refl = f.read()

    return SDFDataBytes(transmittance=trans, reflectance=refl)


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
    tensortree: TensorTreeType = 0,
    ttlog2: int = 4,
    dim: None | SamplingBox = None,
    front: bool = True,
    outspec: OutSpec = "y",
    cleanup: bool = True,
) -> BSDFDataBytes:
    """Generate BSDF data by simulating flux transfer through a device.

    Args:
        inp: input scene files or bytes
        params: additional rfluxmtx parameters
        recip: apply reciprocity averaging (tensor tree only)
        nsamp: number of ray samples
        pctcull: tensor tree culling percentage (< 100)
        nproc: number of parallel processes
        geout: include geometry output (unused, kept for API compatibility)
        nspec: number of spectral channels
        working_dir: directory for temporary files (auto-created if empty)
        basis: Klems hemisphere basis type (used when tensortree=0)
        tensortree: 0 for Klems matrix, 3 for isotropic tensor tree,
                    4 for anisotropic tensor tree
        ttlog2: log2 of tensor tree angular resolution (ns = 2**ttlog2)
        dim: override scene bounding box
        front: also compute front-side SDF
        outspec: output spectrum for Klems matrix mode
        cleanup: remove working directory on completion

    Returns:
        BSDFDataBytes with front and back SDF data
    """
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
    octree_file = os.path.join(working_dir, "device.oct")
    with open(octree_file, "wb") as fp:
        fp.write(oconv(stdin=device, warning=False))

    if tensortree:
        fmt = "a" if os.name == "nt" else "f"
        param_args.append(f"-f{fmt}")
        tt_kwargs = dict(
            tensortree=tensortree,
            ttlog2=ttlog2,
            octree_file=octree_file,
            dim=dim,
            nx=nx,
            ny=ny,
            tmpdir=working_dir,
            params=param_args,
            pctcull=pctcull,
            recip=recip,
        )
        result.back = generate_tensortree_sdf(forw=False, **tt_kwargs)
        if front:
            result.front = generate_tensortree_sdf(forw=True, **tt_kwargs)
    else:
        param_args.append("-fd")
        result.back = generate_back_sdf(
            octree_file, basis, dim, working_dir, params=param_args, outspec=outspec
        )
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
    correct_solid_angle: None | bool = None,
    **kwargs,
) -> bytes:
    # Klems matrix requires solid angle correction; tensor tree ("t3"/"t4") does not
    if correct_solid_angle is None:
        correct_solid_angle = not basis.startswith("t")
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
        correct_solid_angle=correct_solid_angle,
        unit=unit,
        unlink=True,
        ef=emissivity_front,
        eb=emissivity_back,
        **kwargs,
    )

    def _write(path: str, data: bytes) -> str:
        with open(path, "wb") as f:
            f.write(data)
        return path

    with tempfile.TemporaryDirectory(prefix="pyradiance_xml_") as tmpdir:
        if sol_results is not None:
            tfs = _write(os.path.join(tmpdir, "sol_tf.dat"), sol_results.front.transmittance)
            tbs = _write(os.path.join(tmpdir, "sol_tb.dat"), sol_results.back.transmittance)
            rfs = _write(os.path.join(tmpdir, "sol_rf.dat"), sol_results.front.reflectance)
            rbs = _write(os.path.join(tmpdir, "sol_rb.dat"), sol_results.back.reflectance)
            wrapper = wrapper.add_solar(tb=tbs, tf=tfs, rb=rbs, rf=rfs)

        if vis_results is not None:
            tfv = _write(os.path.join(tmpdir, "vis_tf.dat"), vis_results.front.transmittance)
            tbv = _write(os.path.join(tmpdir, "vis_tb.dat"), vis_results.back.transmittance)
            rfv = _write(os.path.join(tmpdir, "vis_rf.dat"), vis_results.front.reflectance)
            rbv = _write(os.path.join(tmpdir, "vis_rb.dat"), vis_results.back.reflectance)
            wrapper = wrapper.add_visible(tb=tbv, tf=tfv, rb=rbv, rf=rfv)

        return wrapper()
