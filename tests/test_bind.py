import pyradiance as pr

mgr = pr.RtraceSimulManager()

mgr.load_octree("test.oct")

print(mgr.set_thread_count(1))


def cooked_callback(ray):
    # Process the ray
    return 0  # Return appropriate integer

def trace_callback(ray):
    # Process the trace
    return 0  # Return appropriate integer


# Set callbacks
mgr.set_cooked_call(cooked_callback)
mgr.set_trace_call(trace_callback)

# Enqueue rays
orig_direc = [
    [1.0, 2.0, 3.0, 0.0, 0.0, 1.0],  # Ray 1 origin and direction
    [4.0, 5.0, 6.0, 0.0, 1.0, 0.0],  # Ray 2 origin and direction
]
mgr.EnqueueBundle(orig_direc)

# Start processing
mgr.FlushQueue()
