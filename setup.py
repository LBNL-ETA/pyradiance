# Copyright (c) Microsoft Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import glob
import os
import platform
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Dict, List

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

def extractall(zip: zipfile.ZipFile, path: str) -> None:
    for name in zip.namelist():
        member = zip.getinfo(name)
        extracted_path = zip.extract(member, path)
        attr = member.external_attr >> 16
        if attr != 0:
            os.chmod(extracted_path, attr)
# 
# 
def download(zip_name: str) -> None:
    zip_file = f'Radiance_{RADTAG}_{zip_name}.zip'
    if os.path.exists("radiance/" + zip_file):
        return
    url = f'https://github.com/LBNL-ETA/Radiance/releases/download/{RADTAG}/'
    url = url + zip_file
    print(f"Fetching {url}")
    with open("radiance/" + zip_file, 'wb') as f:
        f.write(requests.get(url).content)


class PyradianceBDistWheel(bdist_wheel):
    user_options = bdist_wheel.user_options + [
        ("all", "a", "create wheels for all platforms")
    ]
    boolean_options = bdist_wheel.boolean_options + ["all"]

    def initialize_options(self) -> None:
        super().initialize_options()
        self.all = False

    def run(self) -> None:
        shutil.rmtree("build", ignore_errors=True)
        shutil.rmtree("dist", ignore_errors=True)
        shutil.rmtree("pyradiance.egg-info", ignore_errors=True)
        super().run()
        os.makedirs("radiance", exist_ok=True)
        # os.makedirs("pyradiance/radiance", exist_ok=True)
        base_wheel_bundles: List[Dict[str, str]] = [
            {
                "wheel": "macosx_10_13_x86_64.whl",
                "machine": "x86_64",
                "platform": "darwin",
                "zip_name": "OSX",
            },
            {
                "wheel": "macosx_11_0_universal2.whl",
                "machine": "x86_64",
                "platform": "darwin",
                "zip_name": "OSX",
            },
            {
                "wheel": "macosx_11_0_arm64.whl",
                "machine": "arm64",
                "platform": "darwin",
                "zip_name": "OSX_arm64",
            },
            {
                "wheel": "manylinux1_x86_64.whl",
                "machine": "x86_64",
                "platform": "linux",
                "zip_name": "Linux",
            },
            # {
            #     "wheel": "manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
            #     "machine": "aarch64",
            #     "platform": "linux",
            #     "zip_name": "linux-arm64",
            # },
            {
                "wheel": "win32.whl",
                "machine": "i386",
                "platform": "win32",
                "zip_name": "Windows",
            },
            {
                "wheel": "win_amd64.whl",
                "machine": "amd64",
                "platform": "win32",
                "zip_name": "Windows",
            },
        ]
        # self._download_and_extract_local_driver(base_wheel_bundles)

        wheels = base_wheel_bundles
        if not self.all:
            # Limit to 1, since for MacOS e.g. we have multiple wheels for the same platform and architecture and Conda expects 1.
            wheels = list(
                filter(
                    lambda wheel: wheel["platform"] == sys.platform
                    and wheel["machine"] == platform.machine().lower(),
                    base_wheel_bundles,
                )
            )[:1]
        self._build_wheels(wheels)

    def _build_wheels(
        self,
        wheels: List[Dict[str, str]],
    ) -> None:
        base_wheel_location: str = glob.glob(os.path.join(self.dist_dir, "*.whl"))[0]
        without_platform = base_wheel_location[:-7]
        for wheel_bundle in wheels:
            download(wheel_bundle["zip_name"])
            zip_file = (
                f"radiance/Radiance_{RADTAG}_{wheel_bundle['zip_name']}.zip"
            )
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                # extractall(zip, f"radiance/{wheel_bundle['zip_name']}")
                zip_ref.extractall(f"radiance/{wheel_bundle['zip_name']}")
            wheel_location = without_platform + wheel_bundle["wheel"]
            shutil.copy(base_wheel_location, wheel_location)
            with zipfile.ZipFile(wheel_location, "a") as zip:
                driver_root = os.path.abspath(f"radiance/{wheel_bundle['zip_name']}")
                for dir_path, _, files in os.walk(driver_root):
                    for file in files:
                        from_path = os.path.join(dir_path, file)
                        to_path = os.path.basename(file)
                        if Path(file).stem in RADBINS and Path(file).suffix != ".1":
                            zip.write(from_path, f"pyradiance/bin/{to_path}")
                        if Path(file).name in RADCALS:
                            zip.write(from_path, f"pyradiance/lib/{to_path}")
        os.remove(base_wheel_location)
        for whlfile in glob.glob(os.path.join(self.dist_dir, "*.whl")):
            os.makedirs("wheelhouse", exist_ok=True)
            with InWheel(
                in_wheel=whlfile,
                out_wheel=os.path.join("wheelhouse", os.path.basename(whlfile)),
            ):
                print(f"Updating RECORD file of {whlfile}")
        shutil.rmtree(self.dist_dir)
        print("Copying new wheels")
        shutil.move("wheelhouse", self.dist_dir)

    # def _download_and_extract_local_driver(
    #     self,
    #     wheels: List[Dict[str, str]],
    # ) -> None:
    #     zip_names_for_current_system = set(
    #         map(
    #             lambda wheel: wheel["zip_name"],
    #             filter(
    #                 lambda wheel: wheel["machine"] == platform.machine().lower()
    #                 and wheel["platform"] == sys.platform,
    #                 wheels,
    #             ),
    #         )
    #     )
    #     for wheel in wheels:
    #         if wheel["machine"] == platform.machine().lower() and wheel["platform"] == sys.platform:
    #             zip_name = wheel["zip_name"]
    #             break

    #     assert len(zip_names_for_current_system) == 1
    #     zip_name = zip_names_for_current_system.pop()
    #     download(zip_name)
    #     zip_file = f"radiance/radiance_{RADTAG}_{zip_name}.zip"
    #     print(zip_file)
    #     with zipfile.ZipFile(zip_file, "r") as zip:
    #         extractall(zip, "pyradiance/radiance")


setup(
    name="pyradiance",
    author="LBNL",
    author_email="taoningwang@lbl.gov",
    description="",
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
