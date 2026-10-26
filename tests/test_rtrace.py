import os
import unittest

import numpy as np
import pyradiance as pr

result = []


def cooked_callback(ray, client_data):
    print("\nCooked callback called!")
    try:
        print(f"Ray origin: {ray.rorg}")
        print(f"Ray direction: {ray.rdir}")
        print(f"Ray max distance: {ray.rmax}")
        print(f"Ray weight: {ray.rweight}")
        print(f"Ray number: {ray.rno}")
        print(f"Ray type: {ray.rtype}")
        print(f"Radiance {ray.rcol}")
        result.append(ray.rcol)
    except Exception as e:
        print(f"Error in cooked callback: {e}")
        import traceback

        traceback.print_exc()
    return 0


def trace_callback(ray, client_data):
    print("\nTrace callback called!")
    try:
        print(f"Ray origin: {ray.rorg}")
        print(f"Ray direction: {ray.rdir}")
        print(f"Ray max distance: {ray.rmax}")
        print(f"Ray weight: {ray.rweight}")
        print(f"Ray number: {ray.rno}")
        print(f"Ray type: {ray.rtype}")
        print(f"Radiance {ray.rcol}")
        result.append(ray.rcol)
    except Exception as e:
        print(f"Error in trace callback: {e}")
        import traceback

        traceback.print_exc()
    return 0


class TestRtraceSimulManager(unittest.TestCase):
    octree = os.path.join(os.path.dirname(__file__), "Resources", "trace.oct")

    @unittest.skipIf(os.name == "nt", "test not supported on Windows")
    def test_rtrace(self):
        rays = np.array(
            [
                [1.0, 2.0, 3.0],
                [0.0, 0.0, 1.0],  # Ray 1 origin and direction
                [4.0, 5.0, 6.0],
                [0.0, 1.0, 0.0],  # Ray 2 origin and direction
            ]
        )
        rparam = pr.get_ray_params()
        rparam.ab = 0
        pr.set_ray_params(rparam)
        mgr = pr.RtraceSimulManager()
        mgr.load_octree(self.octree)
        mgr.set_thread_count(1)
        mgr.set_cooked_call(cooked_callback)
        mgr.set_trace_call(trace_callback)
        mgr.rt_flags = pr.RTdoFIFO
        mgr.enqueue_bundle(rays)
        mgr.flush_queue()
        mgr.cleanup(True)
        del mgr
        self.assertEqual(len(result), 4)


@unittest.skipIf(os.name == "nt", "test not supported on Windows")
class TestRtraceSimulManagerAPI(unittest.TestCase):
    octree = os.path.join(os.path.dirname(__file__), "Resources", "trace.oct")
    rays = np.array(
        [
            [1.0, 2.0, 3.0],
            [0.0, 0.0, 1.0],
            [4.0, 5.0, 6.0],
            [0.0, 1.0, 0.0],
            [1.0, 2.0, 1.0],
            [0.0, 0.0, -1.0],
        ]
    )

    def setUp(self):
        rparam = pr.get_ray_params()
        rparam.ab = 0
        pr.set_ray_params(rparam)
        self.mgr = pr.RtraceSimulManager()
        self.mgr.load_octree(self.octree)

    def tearDown(self):
        self.mgr.cleanup(True)
        del self.mgr
        pr.set_ray_params()

    def test_trace(self):
        self.mgr.set_thread_count(1)
        res = self.mgr.trace(self.rays)
        self.assertEqual(res.shape, (3, 3))
        self.assertEqual(res.dtype, np.float32)
        self.assertTrue(np.all(res[1:] > 0))

    def test_trace_matches_callback(self):
        self.mgr.set_thread_count(1)
        got = {}

        def cooked(ray, client_data):
            got[ray.rno] = ray.rcol
            self.assertEqual(client_data, "data")
            return 0

        self.mgr.set_cooked_call(cooked, "data")
        self.mgr.rt_flags = pr.RTdoFIFO
        self.mgr.enqueue_bundle(self.rays)
        self.mgr.flush_queue()
        bulk = self.mgr.trace(self.rays)
        # trace() must restore the cooked callback and flags
        self.assertEqual(self.mgr.rt_flags, pr.RTdoFIFO)
        expected = np.array([got[i + 1] for i in range(3)])
        np.testing.assert_allclose(bulk, expected, rtol=1e-6)
        self.mgr.enqueue_bundle(self.rays)
        self.mgr.flush_queue()
        self.assertEqual(len(got), 6)

    def test_trace_multiprocess(self):
        self.mgr.set_thread_count(1)
        single = self.mgr.trace(self.rays)
        self.mgr.set_thread_count(2)
        multi = self.mgr.trace(self.rays)
        np.testing.assert_allclose(single, multi, rtol=1e-6)

    def test_callback_exception_propagates(self):
        self.mgr.set_thread_count(2)
        self.mgr.rt_flags = pr.RTdoFIFO

        def bad(ray, client_data):
            raise KeyError("boom")

        self.mgr.set_cooked_call(bad)
        with self.assertRaises(KeyError):
            self.mgr.enqueue_bundle(self.rays)
            self.mgr.flush_queue()
        self.mgr.set_cooked_call(None)
        self.assertEqual(self.mgr.trace(self.rays).shape, (3, 3))

    def test_enqueue_validation(self):
        with self.assertRaises(ValueError):
            self.mgr.enqueue_bundle(self.rays[:3])
        self.mgr.rt_flags = pr.RTdoFIFO
        with self.assertRaises(ValueError):
            self.mgr.enqueue_bundle(self.rays, 5)
        with self.assertRaises(ValueError):
            self.mgr.enqueue_ray([0, 0], [0, 0, 1])

    def test_enqueue_ray(self):
        got = []
        self.mgr.set_cooked_call(lambda ray, cd: got.append(ray.rcol))
        self.mgr.enqueue_ray([4.0, 5.0, 6.0], [0.0, 1.0, 0.0])
        self.mgr.flush_queue()
        self.assertEqual(len(got), 1)
        self.assertGreater(got[0][0], 0)


if __name__ == "__main__":
    unittest.main()
