# How to compute per-modifier contributions with Rcontrib

`Rcontrib` is a builder class that wraps the `rcontrib` CLI tool. It traces
rays through a scene and records how much each ray's radiance was contributed
by each named modifier (material or light source). This makes it the core
tool for:

- Computing daylight coefficients per window group
- Separating direct and indirect contributions
- The view matrix step in matrix-based methods (3PM, 4PM, 5PM)

## Basic usage

Instantiate `Rcontrib` with the input rays (as bytes), the octree path, and
any ray-tracing parameters. Then call `.add_modifier()` for each modifier you
want to track, and finally call the object to execute.

``` python
import pyradiance as pr

# Input rays: one "ox oy oz dx dy dz" line per ray
rays = b"0.5 0.5 0.8  0 0 1\n"

rc = pr.Rcontrib(
    inp=rays,
    octree="scene.oct",
    params=["-ab", "1", "-ad", "1000", "-lw", "1e-4"],
)
rc.add_modifier(modifier="sky_glow")

result = rc()
print(result.decode())
```

Each output row contains the RGB contribution from `sky_glow` to the
corresponding input ray. The row order matches the input rays one-to-one.

## Tracking multiple modifiers

Call `.add_modifier()` once per modifier. `Rcontrib` supports method chaining:

``` python
rc = (
    pr.Rcontrib(inp=rays, octree="scene.oct", params=["-ab", "1"])
    .add_modifier(modifier="window_north", output="north.hdr")
    .add_modifier(modifier="window_south", output="south.hdr")
)
rc()
```

When `output` is set, each modifier's result is written to a separate file
instead of stdout.

## Using cal expressions and binning

`rcontrib` can bin contributions by direction using a cal expression. This is
the basis for the view matrix (V-matrix) in the 3-phase method, where each
sky patch is a separate bin.

``` python
import pyradiance as pr

with open("sensors.txt", "rb") as f:
    rays = f.read()

rc = pr.Rcontrib(
    inp=rays,
    octree="scene.oct",
    params=["-ab", "5", "-ad", "10000", "-lw", "1e-4", "-c", "1000"],
    yres=len(rays.splitlines()),   # one row per sensor
    inform="a",
    outform="f",
)
rc.add_modifier(
    modifier="skyglow",
    calfile="reinhart.cal",        # binning cal file from Radiance library
    expression="MF:4",             # Reinhart MF:4 subdivision
    nbins="Nrbins",                # number of bins expression from cal file
    binv="rbin",                   # bin index expression from cal file
    output="vmtx.dmx",
)
rc()
```

The resulting `vmtx.dmx` is the V-matrix used in `dctimestep()` or `Rmtxop`.

## Loading modifier names from a file

For scenes with many modifiers (e.g., multiple window groups defined in a
separate file), use `modifier_path` instead of `modifier` to pass a file
containing one modifier name per line:

``` python
rc = pr.Rcontrib(inp=rays, octree="scene.oct")
rc.add_modifier(modifier_path="window_modifiers.txt")
result = rc()
```

## Parallel processing

Set `nproc` to use multiple CPU cores. Multi-process support on Windows is
experimental; on Linux/macOS it is fully supported.

``` python
rc = pr.Rcontrib(
    inp=rays,
    octree="scene.oct",
    nproc=8,
    params=["-ab", "2"],
)
rc.add_modifier(modifier="skyglow")
result = rc()
```

## Complete example: separating window contributions

This example shows how to compute the contribution of two window groups
(`win_east` and `win_west`) to a grid of floor sensors.

``` python
import pyradiance as pr
import numpy as np

# Build the sensor ray list: 5×5 grid on the floor at z=0.8 m, facing up
xs = np.linspace(0.5, 4.5, 5)
ys = np.linspace(0.5, 4.5, 5)
rays = b""
for x in xs:
    for y in ys:
        rays += f"{x:.2f} {y:.2f} 0.8  0 0 1\n".encode()

# Run rcontrib for both window modifiers simultaneously
rc = (
    pr.Rcontrib(
        inp=rays,
        octree="room.oct",
        params=["-ab", "2", "-ad", "4096", "-lw", "1e-5"],
    )
    .add_modifier(modifier="win_east")
    .add_modifier(modifier="win_west")
)
result = rc()

# Parse ASCII output into a numpy array
# With the default outform="a", values are space-separated floats.
# rcontrib writes all modifier outputs concatenated: first all rays for
# modifier 1, then all rays for modifier 2.
nrays = len(rays.splitlines())
values = list(map(float, result.decode().split()))
# Shape: (n_modifiers, n_rays, 3_channels)
arr = np.array(values).reshape(2, nrays, 3)

# Luminance via standard RGB coefficients
east_luminance = arr[0] @ [47.4, 119.9, 11.6]   # shape (nrays,)
west_luminance = arr[1] @ [47.4, 119.9, 11.6]
```
