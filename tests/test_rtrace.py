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
