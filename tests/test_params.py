import gc
import os
import unittest

import pyradiance as pr


class TestRayParams(unittest.TestCase):
    def test_color_setters(self):
        rp = pr.get_default_ray_params()
        rp.me = (0.1, 0.2, 0.3)
        rp.ma = [0.5, 0.6, 0.7]
        rp.av = 1, 2, 3
        for got, want in zip(rp.me, (0.1, 0.2, 0.3)):
            self.assertAlmostEqual(got, want, places=6)
        for got, want in zip(rp.ma, (0.5, 0.6, 0.7)):
            self.assertAlmostEqual(got, want, places=6)
        self.assertEqual(rp.av, (1, 2, 3))
        with self.assertRaises(ValueError):
            rp.av = (1, 2)

    def test_amblist_stored_in_params(self):
        rp = pr.get_default_ray_params()
        rp.amblist = ["mod1", "mod2"]
        rp.ambincl = 0
        self.assertEqual(rp.amblist, ["mod1", "mod2"])
        args = pr.get_ray_params_args(rp)
        idx = args.index("-ae")
        self.assertEqual(args[idx : idx + 4], ["-ae", "mod1", "-ae", "mod2"])
        with self.assertRaises(ValueError):
            rp.ambincl = 2

    @unittest.skipIf(os.name == "nt", "test not supported on Windows")
    def test_set_ray_params_outlives_object(self):
        rp = pr.get_ray_params()
        rp.amblist = ["glass", "metal"]
        rp.ambincl = 1
        rp.af = "test.amb"
        pr.set_ray_params(rp)
        del rp
        gc.collect()
        rp2 = pr.get_ray_params()
        self.assertEqual(rp2.amblist, ["glass", "metal"])
        self.assertEqual(rp2.ambincl, 1)
        pr.set_ray_params()

    @unittest.skipIf(os.name == "nt", "test not supported on Windows")
    def test_set_option(self):
        pr.set_option(["-ab", "3", "-ai", "mod1", "-ai", "mod2"])
        rp = pr.get_ray_params()
        self.assertEqual(rp.ab, 3)
        self.assertEqual(rp.amblist, ["mod1", "mod2"])
        with self.assertRaises(ValueError):
            pr.set_option(["-not-an-option"])
        pr.set_ray_params()

    @unittest.skipIf(os.name == "nt", "test not supported on Windows")
    def test_setspectrsamp_validates(self):
        with self.assertRaises(ValueError):
            pr.setspectrsamp([0, 1], [780, 380])


class TestView(unittest.TestCase):
    def test_parse_view_derived_vectors(self):
        view = pr.parse_view("-vtv -vp 1 2 3 -vd 0 2 0 -vu 0 0 1 -vh 90 -vv 90")
        self.assertEqual(view.vdir, (0, 2, 0))
        # perspective hvec/vvec span 2*tan(angle/2) at unit distance
        self.assertAlmostEqual(view.hvec[0], 2.0)
        self.assertAlmostEqual(view.vvec[2], 2.0)
        self.assertAlmostEqual(view.hn2, 4.0)
        self.assertAlmostEqual(view.vn2, 4.0)

    def test_parse_view_defaults(self):
        view = pr.parse_view("-vp 1 2 3")
        self.assertEqual(view.type, "v")
        self.assertEqual(view.vdir, (0, 1, 0))
        self.assertEqual(view.horiz, 45)

    def test_parse_view_invalid(self):
        with self.assertRaises(ValueError):
            pr.parse_view("-vd 0 0 1 -vu 0 0 1")

    def test_default_view(self):
        view = pr.create_default_view()
        self.assertGreater(view.hn2, 0)
        self.assertGreater(view.vn2, 0)

    def test_setview(self):
        view = pr.create_default_view()
        view.horiz = 90
        view.setview()
        self.assertAlmostEqual(view.hn2, 4.0)
        view.vu = (0, 1, 0)
        with self.assertRaises(ValueError):
            view.setview()


if __name__ == "__main__":
    unittest.main()
