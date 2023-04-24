import os
import platform
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Dict

import requests
from setuptools import setup, Extension

from distutils.command.build_ext import build_ext as build_ext_orig

from auditwheel.wheeltools import InWheel
from wheel.bdist_wheel import bdist_wheel

RADTAG = "2f5bc2ef"

RADBINS = [
    'bsdf2ttree',
    'bsdf2klems',
    'cnt',
    'dctimestep',
    'evalglare',
    'getbbox',
    'getinfo',
    'genblinds',
    'genBSDF',
    'gendaylit',
    'gendaymtx',
    'gensky',
    'ies2rad',
    'mgf2rad',
    'mkillum',
    'obj2rad',
    'oconv',
    'pabopto2bsdf',
    'pcomb',
    'pcond',
    'pfilt',
    'pkgBSDF',
    'pvalue',
    'rad',
    'rcode_depth',
    'rcode_ident',
    'rcode_norm',
    'rcontrib',
    'rfluxmtx',
    'rlam',
    'rmtxop',
    'robjutil',
    'rpict',
    'rsensor',
    'rtpict',
    'rtrace',
    'total',
    'vwrays',
    'vwright',
    'wrapBSDF',
    'xform',
    # For Windows Perl scripts
    'perl530',
    'libgcc_s_seh-1',
    'libstdc++-6',
    'libwinpthread-1',
]

RADLIB = [
    'Ashikhmin.cal',
    'LaFortune.cal',
    'LaFortune1.cal',
    'WGMDaniso.cal',
    'WGMDiso.cal',
    'WINDOW6BSDFt.xml',
    'WalterBSDF.cal',
    'WalterBTDF.cal',
    'ambient.fmt',
    'ambpos.cal',
    'bezier2.cal',
    'blackbody.cal',
    'blinds.cal',
    'boxw.plt',
    'bsdf2rad.cal',
    'cartesian.plt',
    'cct.cal',
    'cielab.cal',
    'cieluv.cal',
    'cieresp.cal',
    'circle.cal',
    'clamp.cal',
    'clockface.hex',
    'clouds.cal',
    'cmat.fmt',
    'color.fmt',
    'colorcal.csh',
    'conv1.cal',
    'conv2.cal',
    'cri.cal',
    'cubic.cal',
    'curve.plt',
    'denom.cal',
    'disk2square.cal',
    'errfile.fmt',
    'ferwerda.cal',
    'filt.cal',
    'fisheye_corr.cal',
    'fitSH.cal',
    'fog.cal',
    'fovsample.cal',
    'function.plt',
    'gauss.cal',
    'gaussian.cal',
    'genSH.cal',
    'gensky+s.fmt',
    'gensky-s.fmt',
    'glaze1.cal',
    'glaze2.cal',
    'graypatch.cal',
    'helvet.fnt',
    'hermite.cal',
    'hsv_rgb.cal',
    'illum.cal',
    'illum.fmt',
    'illumcal.csh',
    'klems_ang.cal',
    'klems_full.cal',
    'klems_half.cal',
    'klems_quarter.cal',
    'lamp.tab',
    'landscape.cal',
    'line.plt',
    'log3G10.cal',
    'lumdist.cal',
    'macbeth.cal',
    'mat3.cal',
    'metals.cal',
    'minimalBSDFt.xml',
    'noise.cal',
    'noise2.cal',
    'noise3.cal',
    'norm.cal',
    'normcomp.cal',
    'patch3w.cal',
    'peerless.cal',
    'perezlum.cal',
    'perezlum_c.cal',
    'picdiff.cal',
    'polar.plt',
    'polynomial.cal',
    'pq.cal',
    'printwarp.cal',
    'quadratic.cal',
    'rambpos.cal',
    'rayinit.cal',
    'reinhard.cal',
    'reinhard.csh',
    'reinhart.cal',
    'reinhartb.cal',
    'reinsrc.cal',
    'rev.cal',
    'rgb.cal',
    'rgb_ycc.cal',
    'root.cal',
    'rskysrc.cal',
    'scatter.plt',
    'screen.cal',
    'sf.cal',
    'skybright.cal',
    'source.cal',
    'spharm.cal',
    'sphsamp.cal',
    'spline.cal',
    'standard.plt',
    'stdrefl.cal',
    'sun.cal',
    'sun2.cal',
    'suncal.fmt',
    'superellipsoid.cal',
    'surf.cal',
    'symbols.met',
    'symbols.mta',
    'testimg.cal',
    'testsuncal.csh',
    'tilt.cal',
    'tmesh.cal',
    'trans.cal',
    'trans2.cal',
    'tregenza.cal',
    'tregsamp.dat',
    'tregsrc.cal',
    'trix.dat',
    'triy.dat',
    'triz.dat',
    'tumblin.cal',
    'uniq_rgb.cal',
    'vchars.met',
    'vchars.mta',
    'veil.cal',
    'view.fmt',
    'view360stereo.cal',
    'vl.cal',
    'vonKries.cal',
    'vwparab.cal',
    'vwplanis.cal',
    'window.cal',
    'xyz_rgb.cal',
    'xyz_srgb.cal',
]



csources=[
    "Radiance/src/common/badarg.c",
    "Radiance/src/common/bmalloc.c",
    "Radiance/src/common/bsdf.c",
    "Radiance/src/common/bsdf_m.c",
    "Radiance/src/common/bsdf_t.c",
    "Radiance/src/common/caldefn.c",
    "Radiance/src/common/calexpr.c",
    "Radiance/src/common/calfunc.c",
    "Radiance/src/common/ccolor.c",
    "Radiance/src/common/ccyrgb.c",
    "Radiance/src/common/color.c",
    "Radiance/src/common/cone.c",
    "Radiance/src/common/dircode.c",
    "Radiance/src/common/disk2square.c",
    "Radiance/src/common/ealloc.c",
    "Radiance/src/common/eputs.c",
    "Radiance/src/common/error.c",
    "Radiance/src/common/ezxml.c",
    "Radiance/src/common/face.c",
    "Radiance/src/common/fgetline.c",
    "Radiance/src/common/fgetval.c",
    "Radiance/src/common/fgetword.c",
    "Radiance/src/common/font.c",
    "Radiance/src/common/fputword.c",
    "Radiance/src/common/fvect.c",
    "Radiance/src/common/gethomedir.c",
    "Radiance/src/common/getlibpath.c",
    "Radiance/src/common/getpath.c",
    "Radiance/src/common/header.c",
    "Radiance/src/common/hilbert.c",
    "Radiance/src/common/image.c",
    "Radiance/src/common/instance.c",
    "Radiance/src/common/loadbsdf.c",
    "Radiance/src/common/lookup.c",
    "Radiance/src/common/mat4.c",
    "Radiance/src/common/mesh.c",
    "Radiance/src/common/modobject.c",
    "Radiance/src/common/multisamp.c",
    "Radiance/src/common/objset.c",
    "Radiance/src/common/octree.c",
    "Radiance/src/common/otypes.c",
    "Radiance/src/common/portio.c",
    "Radiance/src/common/quit.c",
    "Radiance/src/common/readfargs.c",
    "Radiance/src/common/readmesh.c",
    "Radiance/src/common/readobj.c",
    "Radiance/src/common/readoct.c",
    "Radiance/src/common/resolu.c",
    "Radiance/src/common/savestr.c",
    "Radiance/src/common/savqstr.c",
    "Radiance/src/common/sceneio.c",
    "Radiance/src/common/spec_rgb.c",
    "Radiance/src/common/tcos.c",
    "Radiance/src/common/tmap16bit.c",
    "Radiance/src/common/tmapcolrs.c",
    "Radiance/src/common/tmesh.c",
    "Radiance/src/common/tonemap.c",
    "Radiance/src/common/urand.c",
    "Radiance/src/common/wordfile.c",
    "Radiance/src/common/words.c",
    "Radiance/src/common/wputs.c",
    "Radiance/src/common/xf.c",
    "Radiance/src/common/zeroes.c",
    "Radiance/src/rt/noise3.c",
    "Radiance/src/rt/fprism.c",
    "Radiance/src/rt/t_data.c",
    "Radiance/src/rt/t_func.c",
    "Radiance/src/rt/pmapray.c",
    "Radiance/src/rt/p_data.c",
    "Radiance/src/rt/p_func.c",
    "Radiance/src/rt/pmaptype.c",
    "Radiance/src/rt/sphere.c",
    "Radiance/src/rt/m_alias.c",
    "Radiance/src/rt/aniso.c",
    "Radiance/src/rt/ashikhmin.c",
    "Radiance/src/rt/m_clip.c",
    "Radiance/src/rt/dielectric.c",
    "Radiance/src/rt/m_mirror.c",
    "Radiance/src/rt/m_mist.c",
    "Radiance/src/rt/normal.c",
    "Radiance/src/rt/virtuals.c",
    "Radiance/src/rt/mx_data.c",
    "Radiance/src/rt/mx_func.c",
    "Radiance/src/rt/o_cone.c",
    "Radiance/src/rt/o_face.c",
    "Radiance/src/rt/o_instance.c",
    "Radiance/src/rt/o_mesh.c",
    "Radiance/src/rt/pmapio.c",
    "Radiance/src/rt/pmapopt.c",
    "Radiance/src/rt/ambio.c",
    "Radiance/src/rt/pmapsrc.c",
    "Radiance/src/rt/pmutil.c",
    "Radiance/src/rt/pmapbias.c",
    "Radiance/src/rt/pmapdata.c",
    "Radiance/src/rt/pmaprand.c",
    "Radiance/src/rt/pmapparm.c",
    "Radiance/src/rt/srcobstr.c",
    "Radiance/src/rt/func.c",
    "Radiance/src/rt/freeobjmem.c",
    "Radiance/src/rt/raytrace.c",
    "Radiance/src/rt/source.c",
    "Radiance/src/rt/srcsupp.c",
    "Radiance/src/rt/srcsamp.c",
    "Radiance/src/rt/raycalls.c",
    "Radiance/src/rt/initotypes.c",
    "Radiance/src/rt/text.c",
    "Radiance/src/rt/m_brdf.c",
    "Radiance/src/rt/m_bsdf.c",
    "Radiance/src/rt/glass.c",
    "Radiance/src/rt/data.c",
    "Radiance/src/rt/m_direct.c",
    "Radiance/src/rt/ambcomp.c",
    "Radiance/src/rt/ambient.c",
    "Radiance/src/rt/Version.c",
    "Radiance/src/rt/pmapamb.c",
    "Radiance/src/rt/renderopts.c",
] 


if platform.system().lower() == "linux":
    csources += ["Radiance/src/common/strcmp.c", "Radiance/src/common/strlcpy.c"]
elif platform.system().lower() == "windows":
    csources += ["Radiance/src/common/strlcpy.c", "Radiance/src/common/timegm.c", "Radiance/src/common/fixargv0.c"]

# Need to explictly set these for Windows?
export_symbols = [
    "SDcacheFile",
    "SDfreeCache",
    "SDsizeBSDF",
    "SDevalBSDF",
    "SDsampBSDF",
    "SDdirectHemi",
    "readobj", 
    "objblock", 
    "nobjects", 
    "freeobjects", 
    "viewfile",
    "abase_list",
]

class PyradianceBDistWheel(bdist_wheel):

    def initialize_options(self) -> None:
        super().initialize_options()
        self.all = False

    def run(self) -> None:
        shutil.rmtree("build", ignore_errors=True)
        shutil.rmtree("dist", ignore_errors=True)
        shutil.rmtree("pyradiance.egg-info", ignore_errors=True)
        super().run()
        wheels = {
            "darwin": {
                "x86_64": {
                    "wheel": "macosx_10_13_x86_64.whl",
                    "zip_tag": "OSX",
                },
                "arm64": {
                    "wheel": "macosx_11_0_arm64.whl",
                    "zip_tag": "OSX_arm64",
                },
            },
            "linux": {
                "x86_64": {
                    "wheel": "manylinux1_x86_64.whl",
                    "zip_tag": "Linux",
                }
            },
            "windows": {
                "i386": {
                    "wheel": "win32.whl",
                    "zip_tag": "Windows",
                },
                "amd64": {
                    "wheel": "win_amd64.whl",
                    "zip_tag": "Windows",
                },
            },
        }
        wheel = wheels[platform.system().lower()][platform.machine().lower()]
        self._build_wheels(wheel)

    def _build_wheels(self, wheel: Dict[str, str]) -> None:
        assert self.dist_dir is not None
        dist_dir = Path(self.dist_dir)
        wheel_path = list(dist_dir.glob("*.whl"))[0]
        without_platform = wheel_path.stem[:18] + "-py3-none-"
        platform_wheel_path = os.path.join(self.dist_dir, without_platform + wheel["wheel"])
        zip_name = f'Radiance_{RADTAG}_{wheel["zip_tag"]}.zip'
        if not os.path.exists(zip_name):
            url = f'https://github.com/LBNL-ETA/Radiance/releases/download/{RADTAG}/{zip_name}'
            with open(zip_name, 'wb') as wtr:
                wtr.write(requests.get(url).content)
        radiance_dir = "radiance"
        os.makedirs(radiance_dir, exist_ok=True)
        if wheel["zip_tag"] == "Linux":
            # tarball inside zip need to be extracted
            with zipfile.ZipFile(zip_name, "r") as zip_ref:
                zip_ref.extractall()
            tarpath = [i for i in Path().glob("radiance*Linux.tar.gz")]
            if len(tarpath) == 1:
                tarpath = tarpath[0]
            else:
                raise ValueError("Could not find Linux tar.gz file")
            with tarfile.open(tarpath) as tarf:
                tarf.extractall(radiance_dir)
            os.remove(tarpath)
        else:
            with zipfile.ZipFile(zip_name, "r") as zip_ref:
                zip_ref.extractall(radiance_dir)
        os.remove(zip_name)
        shutil.copy(wheel_path, platform_wheel_path)
        with zipfile.ZipFile(platform_wheel_path, "a") as zip:
            _root = os.path.abspath(radiance_dir)
            for dir_path, _, files in os.walk(_root):
                for file in files:
                    from_path = os.path.join(dir_path, file)
                    to_path = Path(file).name
                    if Path(file).stem in RADBINS and Path(file).suffix not in (".1", '.c', '.h', '.txt', '.mtx'):
                        # Windows need .exe suffix
                        os.chmod(from_path, 0o755)
                        zip.write(from_path, f"pyradiance/bin/{to_path}")
                    if Path(file).name in RADLIB:
                        zip.write(from_path, f"pyradiance/lib/{to_path}")
        os.remove(wheel_path)
        for whlfile in list(dist_dir.glob("*.whl")):
            os.makedirs("wheelhouse", exist_ok=True)
            with InWheel(in_wheel=str(whlfile), out_wheel=os.path.join("wheelhouse", os.path.basename(whlfile)),):
                print(f"Updating RECORD file of {whlfile}")
        shutil.rmtree(self.dist_dir)
        shutil.move("wheelhouse", self.dist_dir)
        shutil.rmtree(radiance_dir)
        

class CTypesExtension(Extension):
    pass


class build_ext(build_ext_orig):
    def build_extension(self, ext):
        self._ctypes = isinstance(ext, CTypesExtension)
        with open("Radiance/src/rt/VERSION", "r") as f:
            version = f.read().strip()
        with open("Radiance/src/rt/Version.c", "w") as wtr:
            wtr.write(f'char VersionID[] = "{version}";')
        return super().build_extension(ext)

    def get_export_symbols(self, ext):
        if self._ctypes:
            # Need this for Windows
            return export_symbols
        return super().get_export_symbols(ext)

    def get_ext_filename(self, ext_name):
        if self._ctypes:
            return ext_name + ".so"
        return super().get_ext_filename(ext_name)


setup(
    name="pyradiance",
    author="LBNL",
    author_email="taoningwang@lbl.gov",
    version="0.0.8a1",
    description="Python interface for Radiance command-line tools",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    license="BSD-3-Clause",
    url="",
    packages=["pyradiance"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    py_modules=["pyradiance.lib"],
    ext_modules=[
        CTypesExtension(
            name="pyradiance.libraycalls",
            include_dirs=["Radiance/src/common", "Radiance/src/rt"],
            sources=csources,
        ),
    ],
    cmdclass={"build_ext": build_ext, "bdist_wheel": PyradianceBDistWheel},
)
