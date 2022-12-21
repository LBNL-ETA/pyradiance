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
    'cnt',
    'evalglare',
    'getbbox',
    'getinfo',
    'gendaylit',
    'gensky',
    'mkillum',
    'obj2rad',
    'oconv',
    'pcomb',
    'pcond',
    'pfilt',
    'pvalue',
    'rad',
    'rcalc',
    'rcontrib',
    'rfluxmtx',
    'rlam',
    'rmtxop',
    'rpict',
    'rtrace',
    'total',
    'vwrays',
    'vwright',
    'xform',
]

RADCALS = [
    'klems_full.cal',
    'perezlum.cal',
    'rayinit.cal',
    'reinhartb.cal',
    'surf.cal',
    'tmesh.cal',
    'minimalBSDFt.xml',
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
                    to_path = os.path.basename(file)
                    if Path(file).stem in RADBINS and Path(file).suffix != ".1":
                        os.chmod(from_path, 0o755)
                        zip.write(from_path, f"pyradiance/bin/{to_path}")
                    if Path(file).name in RADCALS:
                        zip.write(from_path, f"pyradiance/lib/{to_path}")
        os.remove(wheel_path)
        for whlfile in list(dist_dir.glob("*.whl")):
        # for whlfile in glob.glob(os.path.join(self.dist_dir, "*.whl")):
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
    description="Wrapper for Radiance command-line tools",
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
        # "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    cmdclass={"bdist_wheel": PyradianceBDistWheel},
)
