import pyradiance as pr


def cooked_callback(ray, client_data):
    print("\nCooked callback called!")
    try:
        # Access ray properties directly
        print(f"Ray origin: {ray.rorg}")
        print(f"Ray direction: {ray.rdir}")
        print(f"Ray max distance: {ray.rmax}")
        print(f"Ray weight: {ray.rweight}")
        print(f"Ray number: {ray.rno}")
        print(f"Ray type: {ray.rtype}")
        print(f"Radiance {ray.rcol}")
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
    except Exception as e:
        print(f"Error in trace callback: {e}")
        import traceback

        traceback.print_exc()
    return 0


rays = [
    [1.0, 2.0, 3.0],
    [0.0, 0.0, 1.0],  # Ray 1 origin and direction
    [4.0, 5.0, 6.0],
    [0.0, 1.0, 0.0],  # Ray 2 origin and direction
]

mgr = pr.RtraceSimulManager()
mgr.load_octree("test.oct")
mgr.set_thread_count(2)
mgr.set_cooked_call(cooked_callback)
mgr.set_trace_call(trace_callback)
mgr.rt_flags = pr.RTFlags.RTdoFIFO.value
mgr.enqueue_bundle(rays)
mgr.flush_queue()
mgr.cleanup(True)
del mgr

# ray_count = 1
# mgr = pr.RcontribSimulManager("test.oct")
# mgr.set_flag()
# mgr.yres = 2
# mgr.set_data_format("f")
# mgr.accum = ray_count
# # mgr.add_modifier(mod_name, curout, prms, binval, bincnt)
# if not mgr.get_output():
#     raise RuntimeError("Missing modifier")
# mgr.prep_output()
# mgr.compute_record()
# del mgr
