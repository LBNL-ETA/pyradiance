import os
import platform
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Dict

import requests
from setuptools import setup

from auditwheel.wheeltools import InWheel
from wheel.bdist_wheel import bdist_wheel

RADTAG = "b39cf30b"

RADBINS = [
    'bsdf2ttree',
    'bsdf2klems',
    'cnt',
    'dctimestep',
    'evalglare',
    'getbbox',
    'getinfo',
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
        without_platform = str(wheel_path)[:-7] 
        platform_wheel_path = without_platform + wheel["wheel"]
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
                    if Path(file).stem in RADBINS and Path(file).suffix != ".1":
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
        

setup(
    name="pyradiance",
    author="LBNL",
    author_email="taoningwang@lbl.gov",
    version="0.0.2a1",
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
    cmdclass={"bdist_wheel": PyradianceBDistWheel},
)
