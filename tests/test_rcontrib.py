import os

import numpy as np

import pyradiance as pr

rays = np.array(
    [
        [10, 10, 3],
        [0.0, 0.0, 1.0],  # Ray 1 origin and direction
        [4.0, 5.0, 3.0],
        [0.0, 0.0, 1.0],  # Ray 2 origin and direction
    ]
)

outfile = "test.mtx"

pr.initfunc()
pr.calcontext(pr.RCCONTEXT)

ray_count = 1
pr.set_u(1)
pr.set_dj(0.9)
pr.set_dr(3)
pr.set_dp(512)
pr.set_ds(0.2)
pr.set_st(0.02)
pr.set_ss(1)
pr.set_lr(-10)
pr.set_lw(2e-3)
pr.set_ar(256)
pr.set_ad(350)
pr.set_ab(6)
cndx = [0, 1, 2, 3]
wlpart = [780, 588, 480, 380]
mgr = pr.RcontribSimulManager()
# mgr.set_data_format(ord("f"))
mgr.accum = 1
pr.loadfunc("reinhartb.cal")
params = "MF=1,rNx=0,rNy=0,rNz=-1,Ux=0,Uy=1,Uz=0,RHS=+1"
pr.set_eparams(params)
bincnt = int(pr.eval("Nrbins") + 0.5)
mgr.yres = rays.shape[0] // 2
print(f"{mgr.yres=}")
print(f"{mgr.set_flag(pr.RTimmIrrad, True)=}")
print(
    f"{mgr.add_modifier(
    modn="groundglow", outspec=outfile, binval="if(-Dx*0-Dy*0-Dz*-1,0,-1)", bincnt=1
)=}"
)
print(
    f"{mgr.add_modifier(
    modn="skyglow", outspec=outfile, prms=params, binval="rbin", bincnt=bincnt
)=}"
)
pr.set_dt(0)
pr.set_as(0)
pr.set_aa(0)
out = mgr.get_output()
pr.setspectrsamp(cndx, wlpart)
mgr.load_octree("test.oct")
mgr.add_header("rcontrib -ab -I")
mgr.out_op = pr.RcOutputOp.FORCE
rval = mgr.prep_output()
mgr.set_thread_count(2)
mgr.rcontrib(rays)
print(mgr.get_output_array())
