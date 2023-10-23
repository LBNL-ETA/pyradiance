"""
"""

from pathlib import Path
import math

import pyradiance as pr

def get_dir_dir(fpath: str | Path, idirs: list[list[float]]) -> float:
    if not isinstance(fpath, Path):
        fpath = Path(fpath)
    if fpath.suffix != '.xml' and fpath.suffix != ".sir":
        raise ValueError(f"File {fpath} must be an XML or SIR file")
    ndirs = len(idirs)
    nsamps: int = 10000
    cnt = pr.cnt(ndirs, nsamps)
    pr.rcalc(cnt, source="", expr=rcalc_e)
    res = pr.bsdfquery()
    pr.total(res)
    res = pr.rcalc()
    return float(res.decode())

rcalc_e = (
'nf=1/sqrt(iDx($1+1)^2+iDy($1+1)^2+iDz($1+1)^2);'
'inDx=nf*iDx($1+1);inDy=nf*iDy($1+1);inDz=nf*iDz($1+1);'
'refDx=-inDx;refDy=-inDy;refDz=-inDz;'
'randDx=1-2*rand(.5813*recno-18.387);randDy=1-2*rand(-7.3885*recno+5.6192);'
'randDz=1-2*rand(3.57174*recno+6.261943);'
'upDx=randDy*refDz-randDz*refDy;'
'upDy=randDz*refDx-randDx*refDz;upDz=randDx*refDy-randDy*refDx'
'tanTn=tan(og)/sqrt(upDx*upDx+upDy*upDy+upDz*upDz+1e-10)'
'sDx=refDx+tanTn*upDx;sDy=refDy+tanTn*upDy;sDz=refDz+tanTn*upDz'
'$1=inDx;$2=inDy;$3=inDz;$4=sDx;$5=sDy;$6=sDz'
)
