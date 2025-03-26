import os
import unittest

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


if __name__ == "__main__":
    unittest.main()
