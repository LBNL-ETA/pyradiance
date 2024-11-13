import pyradiance as pr

mgr = pr.RtraceSimulManager()

mgr.load_octree("test.oct")

print(mgr.set_thread_count(1))
