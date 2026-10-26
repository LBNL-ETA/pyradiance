import os
import unittest

import numpy as np

import pyradiance as pr


@unittest.skipIf(os.name == "nt", "test not supported on Windows")
class TestRpictSimulManager(unittest.TestCase):
    octree = os.path.join(os.path.dirname(__file__), "Resources", "trace.oct")
    picture = "test_rpict.hdr"

    def setUp(self):
        rparams = pr.get_ray_params()
        rparams.ab = 0
        pr.set_ray_params(rparams)
        self.view = pr.parse_view(
            "-vtv -vp 5 5 1.5 -vd 1 0 0 -vu 0 0 1 -vh 60 -vv 45"
        )
        self.mgr = pr.RpictSimulManager()
        self.mgr.load_octree(self.octree)

    def tearDown(self):
        del self.mgr
        pr.set_ray_params()
        if os.path.exists(self.picture):
            os.remove(self.picture)

    def test_render_tile(self):
        self.mgr.prims = "rgb"
        self.assertEqual(self.mgr.prims, "rgb")
        xres, yres, _ = self.mgr.new_frame(self.view, [32, 32])
        self.assertEqual(xres, 32)
        self.assertLess(yres, 32)
        color, depth = self.mgr.render_tile()
        self.assertEqual(color.shape, (yres, xres, 3))
        self.assertEqual(depth.shape, (yres, xres))
        self.assertGreater(color.mean(), 0)

    def test_tile_grid(self):
        xres, yres, _ = self.mgr.new_frame(self.view, [64, 64], 1.0, [2, 2])
        self.assertEqual(self.mgr.t_width() * 2, xres)
        self.assertEqual(self.mgr.t_height() * 2, yres)
        with self.assertRaises(ValueError):
            self.mgr.render_tile()
        with self.assertRaises(ValueError):
            self.mgr.render_tile([2, 0])
        color, _ = self.mgr.render_tile([1, 1])
        self.assertEqual(color.shape[:2], (self.mgr.t_height(), self.mgr.t_width()))

    def test_render_before_frame(self):
        with self.assertRaises(RuntimeError):
            self.mgr.render_tile()

    def test_render_frame(self):
        self.mgr.new_frame(self.view, [32, 32])
        dtype = self.mgr.render_frame(self.picture)
        self.assertEqual(dtype, pr.RenderDataType.RDTrgbe)
        self.assertEqual(pr.get_image_dimensions(self.picture)[:2], (32, 23))

    def test_reference_depth(self):
        self.assertTrue(self.mgr.set_reference_depth(2.0, "meter"))
        self.assertEqual(self.mgr.get_reference_depth(), (2.0, "2/meter"))
        self.assertTrue(self.mgr.set_reference_depth("3.5/foot"))
        self.assertEqual(self.mgr.get_reference_depth(), (3.5, "3.5/foot"))


if __name__ == "__main__":
    unittest.main()
