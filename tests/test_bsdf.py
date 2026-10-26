import gc
import os
import unittest

import numpy as np

from pyradiance import bsdf


class TestBSDF(unittest.TestCase):
    resources_dir = os.path.join(os.path.dirname(__file__), "Resources")

    def test_BSDF(self):
        """Test the bsdf function."""
        sddata = bsdf.load_file(os.path.join(self.resources_dir, "t3.xml"))
        _t = bsdf.direct_hemi(sddata, 30, 0, bsdf.SAMPLE_ALL & ~bsdf.SAMPLE_R)
        self.assertAlmostEqual(_t, 7.645609e-2)
        _a = bsdf.size(sddata, 30.0, 0.0, bsdf.QUERY_MIN + bsdf.QUERY_MAX)
        self.assertAlmostEqual(_a[0], 7.6699e-4)
        _sv = bsdf.query(sddata, 0, 0, 180, 0)
        self.assertAlmostEqual(_sv[1], 4.9971852)

    def test_query_result_owned(self):
        sddata = bsdf.load_file(os.path.join(self.resources_dir, "t3.xml"))
        sv = bsdf.query(sddata, 0, 0, 180, 0)
        # Overwrite the stack and heap; the result must not change
        gc.collect()
        bsdf.query(sddata, 30, 0, 150, 0)
        _ = np.random.rand(1000)
        self.assertAlmostEqual(sv[1], 4.9971852)

    def test_sample(self):
        sddata = bsdf.load_file(os.path.join(self.resources_dir, "t3.xml"))
        samples = bsdf.sample(sddata, 30, 0, 8, bsdf.SAMPLE_ALL)
        self.assertEqual(samples.shape, (8, 6))
        with self.assertRaises(ValueError):
            bsdf.sample(sddata, 30, 0, 0, bsdf.SAMPLE_ALL)

    def test_load_missing_file(self):
        with self.assertRaises(RuntimeError):
            bsdf.load_file(os.path.join(self.resources_dir, "missing.xml"))

    def test_xforms(self):
        mtx = bsdf.comp_xform(np.array([0.0, 0.0, 1.0]), np.array([0.0, 1.0, 0.0]))
        self.assertEqual(mtx.shape, (3, 3))
        np.testing.assert_allclose(mtx, np.eye(3), atol=1e-12)
        mtx = bsdf.comp_xform(np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]))
        inv = bsdf.inv_xform(mtx)
        np.testing.assert_allclose(mtx @ inv, np.eye(3), atol=1e-12)
        vec = bsdf.map_dir(np.array([1.0, 0.0, 0.0]), mtx)
        np.testing.assert_allclose(vec, mtx @ np.array([1.0, 0.0, 0.0]), atol=1e-12)

    def test_abase_list(self):
        bases = bsdf.abase_list()
        names = [b["name"] for b in bases]
        self.assertIn("LBNL/Klems Full", names)
        full = bases[names.index("LBNL/Klems Full")]
        self.assertEqual(full["nangles"], 145)
        self.assertEqual(full["lat"][-1], (90.0, 0))
        self.assertEqual(sum(n for _, n in full["lat"]), 145)


if __name__ == "__main__":
    unittest.main()
