import os

import numpy as np

import pyradiance as pr

rays = np.array(
    [
        [1.0, 2.0, 3.0],
        [0.0, 0.0, 1.0],  # Ray 1 origin and direction
        # [4.0, 5.0, 6.0],
        # [0.0, 1.0, 0.0],  # Ray 2 origin and direction
    ]
)

curout = "test.mtx"
prms = None

pr.initfunc()
pr.calcontext(pr.RCCONTEXT)

ray_count = 1
mgr = pr.RcontribSimulManager("test.oct")
ds = mgr.cds_f("test2.mtx", pr.RcOutputOp.rco_new, 0)
mgr.yres = int(rays.shape[0] / 2)
mgr.set_data_format(ord("f"))
mgr.accum = ray_count
pr.loadfunc("reinhartb.cal")
params = "MF=1,rNx=0,rNy=0,rNz=-1,Ux=0,Uy=1,Uz=0,RHS=+1"
pr.set_eparams(params)
bincnt = int(pr.eval("Nrbins") + 0.5)
binval = "if(-Dx*0-Dy*0-Dz*-1,0,-1)"
mgr.add_modifier(modn="groundglow", outspec=curout, binval="if(-Dx*0-Dy*0-Dz*-1,0,-1)")
mgr.add_modifier("skyglow", outspec=curout, prms=params, binval="rbin", bincnt=bincnt)
test = mgr.get_output()
rval = mgr.prep_output()
mgr.contrib(rays)
breakpoint()
