
from typing import Tuple
from math import floor, sqrt, radians, sin, cos, tan, atan2, degrees, pi

import pyradiance as pr

def lrand(x: float) -> float:
    """Psudo-random number generator."""
    x *= 1.0/(1.0 + x*x) + 2.71828182845904
    x += .785398163397447 - floor(x)
    x = 1e5 / x
    return x - floor(x);

def vec_from_deg(theta: float, phi: float) -> Tuple[float, float, float]:
    theta = radians(theta)
    phi = radians(phi)
    v0 = v1 = sin(theta)
    v0 *= cos(phi)
    v1 *= sin(phi)
    v2 = round(cos(theta), 2)
    return v0, v1, v2

def deg_from_vec(x: float, y: float, z: float) -> Tuple[float, float]:
    theta = atan2(sqrt(x*x + y*y), z)
    phi = atan2(y, x)
    return degrees(theta), degrees(phi)


def apex_to_solid_angle(apex: float) -> float:
    """Convert apex angle to solid angle.

    Args:
        apex: Apex angle in radians.

    Returns:
        Solid angle in steradians.
    """
    return 2 * pi * (1 - cos(apex))

# Input file
xml_path = "t3.xml"

# Cone radius
max_gamma = 2.5

# Incident directions, theta, phi
idirs = [
    [0, 0],
    [10, 0],
    [20, 0],
    [30, 0],
    [40, 0],
    [50, 0],
    [60, 0],
    [70, 0],
    [80, 0],
    [87.5, 0],
]

# Number of samples per incident direction
nsamps = 10000

# Incident direction vectors
idirsn = [vec_from_deg(*d) for d in idirs]

isdir_bundles = []

nsamps_root = sqrt(nsamps)
max_gamma_r = radians(max_gamma)
for id, d in enumerate(idirsn):
    isdirs = []
    for ins in range(nsamps):
        recno = id * nsamps + ins + 1
        og = max_gamma_r / nsamps_root * sqrt(ins+.5)
        refDx = -d[0]
        refDy = -d[1]
        refDz = -d[2]
        randDx = 1 - 2 * lrand(0.5813*recno-18.387)
        randDy = 1 - 2 * lrand(-7.3885*recno + 5.6192)
        randDz = 1 - 2 * lrand(3.57174*recno + 6.261943)
        upDx = randDy * refDz - randDz * refDy
        upDy = randDz * refDx - randDx * refDz
        upDz  =randDx * refDy - randDy * refDx
        tanTn = tan(og) / sqrt(upDx**2+upDy**2+upDz**2+1e-10)
        sDx = refDx + tanTn * upDx
        sDy = refDy + tanTn * upDy
        sDz = refDz + tanTn * upDz
        isdirs.append([*idirs[id], *deg_from_vec(sDx, sDy, sDz)])
    isdir_bundles.append(isdirs)

assert len(isdir_bundles[0][0]) == 4
assert len(isdir_bundles[0]) == nsamps

with pr.BSDF(xml_path) as sd:
    for bundle in isdir_bundles:
        sample_results = [sd.eval(*d)[1] for d in bundle]
        print(bundle[0][:2], sum(sample_results) / nsamps * apex_to_solid_angle(max_gamma_r))
