import os
import unittest

import numpy as np

import pyradiance as pr


class TestRcontribSimulManager(unittest.TestCase):

    octree = os.path.join(os.path.dirname(__file__), "Resources", "contrib.oct")

    def test_rcontrib(self):
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

        rparams = pr.get_ray_params()
        rparams.u = True
        rparams.dj = 0.9
        rparams.dr = 3
        rparams.dp = 512
        rparams.ds = 0.2
        rparams.st = 0.02
        rparams.ss = 1
        rparams.lr = -10
        rparams.lw = 2e-3
        rparams.ar = 256
        rparams.ad = 350
        rparams.ab = 6
        rparams.aa = 0
        rparams.abs = 0
        rparams.st = 0
        pr.set_ray_params(rparams)
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
        mgr.set_flag(pr.RTimmIrrad, True)
        mgr.add_modifier(
            modn="groundglow",
            outspec=outfile,
            binval="if(-Dx*0-Dy*0-Dz*-1,0,-1)",
            bincnt=1,
        )
        mgr.add_modifier(
            modn="skyglow", outspec=outfile, prms=params, binval="rbin", bincnt=bincnt
        )
        out = mgr.get_output()
        pr.setspectrsamp(cndx, wlpart)
        mgr.load_octree(self.octree)
        mgr.add_header("rcontrib -ab -I")
        mgr.out_op = pr.RcOutputOp.FORCE
        rval = mgr.prep_output()
        mgr.set_thread_count(2)
        mgr.rcontrib(rays)
        # print(mgr.get_output_array())
        os.remove(outfile)
        del mgr
