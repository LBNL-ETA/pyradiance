import os
import unittest

import numpy as np

import pyradiance as pr


class TestRcontribSimulManager(unittest.TestCase):
    octree = os.path.join(os.path.dirname(__file__), "Resources", "contrib.oct")

    @unittest.skipIf(os.name == "nt", "test not supported on Windows")
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
        rparams.as_ = 0
        rparams.st = 0
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
        # pr.setspectrsamp(cndx, wlpart)
        pr.set_ray_params(rparams)
        mgr.load_octree(self.octree)
        mgr.out_op = pr.RcOutputOp.FORCE
        rval = mgr.prep_output()
        mgr.set_thread_count(1)
        mgr.rcontrib(rays)
        result_array = mgr.get_output_array()
        self.assertTrue(result_array.sum() > 5.0)
        mgr.cleanup(True)
        os.remove(outfile)


@unittest.skipIf(os.name == "nt", "test not supported on Windows")
class TestRcontribSimulManagerAPI(unittest.TestCase):
    octree = os.path.join(os.path.dirname(__file__), "Resources", "contrib.oct")
    # row 0 looks up at the sky, row 1 looks down at the ground
    rays = np.array([[10, 10, 3], [0, 0, 1], [4, 5, 3], [0, 0, -1]], dtype=float)
    outputs = ("test_sky.mtx", "test_ground.mtx")

    def setUp(self):
        pr.initfunc()
        pr.calcontext(pr.RCCONTEXT)
        rparams = pr.get_ray_params()
        rparams.ab = 1
        rparams.ad = 1024
        rparams.aa = 0
        rparams.lw = 1e-4
        pr.set_ray_params(rparams)

    def tearDown(self):
        pr.set_ray_params()
        for fname in self.outputs:
            if os.path.exists(fname):
                os.remove(fname)

    def run_contrib(self, rays, accum=1, fmt="f"):
        sky, ground = self.outputs
        with pr.RcontribSimulManager() as mgr:
            mgr.set_data_format(fmt)
            self.assertEqual(mgr.get_format()[0], fmt)
            mgr.accum = accum
            mgr.yres = rays.shape[0] // (2 * accum)
            mgr.set_flag(pr.RTimmIrrad, True)
            mgr.add_modifier(modn="skyglow", outspec=sky)
            mgr.add_modifier(modn="groundglow", outspec=ground)
            mgr.load_octree(self.octree)
            mgr.out_op = pr.RcOutputOp.FORCE
            mgr.prep_output()
            self.assertEqual(mgr.get_output(sky).get_name(), sky)
            self.assertEqual(mgr.get_output(ground).get_name(), ground)
            with self.assertRaises(ValueError):
                mgr.rcontrib(rays[:2])
            mgr.rcontrib(rays)
            sky_arr = mgr.get_output_array(sky)
            ground_arr = mgr.get_output_array(ground)
            with self.assertRaises(ValueError):
                mgr.get_output_array("missing.mtx")
        return sky_arr, ground_arr

    def test_named_outputs(self):
        sky, ground = self.run_contrib(self.rays)
        self.assertEqual(sky.dtype, np.float32)
        self.assertEqual(sky.shape, (2, 3))
        self.assertTrue(np.all(sky[0] > 0))
        self.assertTrue(np.all(sky[1] == 0))
        self.assertTrue(np.all(ground[0] == 0))
        self.assertTrue(np.all(ground[1] > 0))

    def test_accum_double(self):
        # each record accumulates 2 copies of the same ray
        rays = np.repeat(self.rays.reshape(2, 2, 3), 2, axis=0).reshape(-1, 3)
        sky, ground = self.run_contrib(rays, accum=2, fmt="d")
        self.assertEqual(sky.dtype, np.float64)
        self.assertEqual(sky.shape, (2, 3))
        self.assertTrue(np.all(sky[0] > 0))
        self.assertTrue(np.all(sky[1] == 0))
        self.assertTrue(np.all(ground[0] == 0))
        self.assertTrue(np.all(ground[1] > 0))

    def test_data_share(self):
        mgr = pr.RcontribSimulManager()
        self.assertEqual(mgr.data_share, "map")
        mgr.data_share = "file"
        self.assertEqual(mgr.data_share, "file")
        with self.assertRaises(ValueError):
            mgr.data_share = "other"
        with self.assertRaises(ValueError):
            mgr.set_data_format("x")
        mgr.cleanup(True)


if __name__ == "__main__":
    unittest.main()
