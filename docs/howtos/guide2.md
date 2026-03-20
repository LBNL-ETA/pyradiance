# How to run a two-phase matrix daylighting simulation

The two-phase (2PM) method decomposes an annual daylight simulation into:

1. A **view matrix** (V) — sensor responses to each sky patch, computed once
   with `rfluxmtx()`.
2. A **sky matrix** (D) — sky patch luminances for every timestep, computed
   with `gendaymtx()`.
3. A **matrix product** V × D — annual illuminance at each sensor, computed
   with `Rmtxop` or `dctimestep()`.

The key advantage is that steps 1 and 2 are independent: the scene geometry
only needs to be ray-traced once (step 1), and any number of weather files can
be substituted for step 2 without re-tracing.

## Prerequisites

You need:

- An octree of the scene (`scene.oct`)
- A sensor file (`sensors.txt`) — one `x y z dx dy dz` row per sensor
- A sky receiver file (`sky.rad`) marking the sky and ground hemisphere
- An EPW/TMY weather file (`weather.epw`)

A sky receiver file annotates sky and ground with `rfluxmtx` directives.
A minimal `sky.rad` looks like:

```
#@rfluxmtx h=u

void glow groundglow
0
0
4 1 1 1 0

groundglow source ground
0
0
4 0 0 -1 180

#@rfluxmtx u=+Y h=r4

void glow skyglow
0
0
4 1 1 1 0

skyglow source sky
0
0
4 0 0 1 180
```

The `h=r4` annotation sets the Reinhart MF:4 sky subdivision (2305 patches).

## Step 1 — Compute the view matrix

Use `rfluxmtx()` to ray-trace the sensor response to each sky patch. Pass the
sensor rays as bytes and list the scene geometry files:

``` python
import pyradiance as pr

# Read sensors as bytes (one "ox oy oz dx dy dz" line per sensor)
with open("sensors.txt", "rb") as f:
    rays = f.read()

view_mtx = pr.rfluxmtx(
    receiver="sky.rad",
    rays=rays,
    params=["-ab", "5", "-ad", "10000", "-lw", "1e-4", "-c", "1000"],
    octree="scene.oct",
    scene=["materials.mat", "geometry.rad"],
)

# Optionally write to disk for reuse
with open("vmtx.dmx", "wb") as f:
    f.write(view_mtx)
```

`-c 1000` sends 1000 ray samples per direction; `-ab 5` allows five ambient
bounces. Tune these for accuracy vs. speed.

## Step 2 — Generate the sky matrix

Use `gendaymtx()` with an EPW weather file to produce a sky matrix matching
the same Reinhart subdivision used in the receiver:

``` python
sky_mtx = pr.gendaymtx(
    "weather.epw",
    mfactor=4,       # matches h=r4 in sky.rad
    sky_only=True,   # separate sky from sun (diffuse only for 2PM)
    outform="f",     # binary float for speed
)

with open("smtx.dmx", "wb") as f:
    f.write(sky_mtx)
```

For the full 2PM with sun and sky combined, omit `sky_only=True`.

## Step 3 — Multiply V × D with dctimestep

`dctimestep()` takes exactly 2 or 4 matrix arguments. For 2PM, pass the view
matrix and sky matrix:

``` python
# Both matrices on disk
results = pr.dctimestep("vmtx.dmx", "smtx.dmx", outform="a")

with open("results.txt", "wb") as f:
    f.write(results)
```

Each row of `results.txt` contains the RGB (or luminance) value at one sensor
for one timestep. The row order matches the outer product of sensors × timesteps.

## Alternative: chain with Rmtxop

`Rmtxop` is the more flexible builder for multi-matrix operations. It supports
scaling, transposing, and combining matrices with `+` or `*` operators. Here
is the same V × D product expressed with `Rmtxop`:

``` python
result = (
    pr.Rmtxop(outform="a")
    .add_input("vmtx.dmx")
    .add_input("smtx.dmx")
    ()
)
```

`Rmtxop` is particularly useful when adding a direct subtraction term (as in
the 3PM or 5PM methods), or when converting units with a scaling factor:

``` python
# Convert RGB to luminance (cd/m²) using standard coefficients
luminance = (
    pr.Rmtxop(outform="a")
    .add_input("vmtx.dmx", transform=[47.4, 119.9, 11.6])
    .add_input("smtx.dmx")
    ()
)
```

## Putting it all together

``` python
import pyradiance as pr

# 1. View matrix
with open("sensors.txt", "rb") as f:
    rays = f.read()

view_mtx = pr.rfluxmtx(
    receiver="sky.rad",
    rays=rays,
    params=["-ab", "5", "-ad", "10000", "-lw", "1e-4", "-c", "1000"],
    octree="scene.oct",
    scene=["materials.mat", "geometry.rad"],
)

# 2. Sky matrix
sky_mtx = pr.gendaymtx("weather.epw", mfactor=4, outform="f")

# 3. Annual results (sensor × timestep rows)
results = pr.dctimestep(view_mtx, sky_mtx, outform="a")

with open("results.txt", "wb") as f:
    f.write(results)
```

!!! note
    For large scenes or fine Reinhart subdivisions (MF:4+), `rfluxmtx` can
    take significant time. Write `view_mtx` to disk so it can be reused when
    comparing different weather files or shading states.
