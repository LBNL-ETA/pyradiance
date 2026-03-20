# How to load a WaveFront (.obj) model

This guide shows how to import a WaveFront `.obj` model into a Radiance scene,
assign materials, build an octree, and trace rays through it.

## Convert .obj to Radiance

Use `obj2rad()` to convert a `.obj` file to a Radiance scene description.
The result is returned as bytes.

``` python
import pyradiance as pr

room_rad = pr.obj2rad("room.obj")
```

## Inspect the modifiers

The converted scene will contain surfaces that reference modifiers (material
names) that need to be defined. Use `parse_primitive()` to extract the
primitives from the bytes and collect the unique modifier names:

``` python
primitives = pr.parse_primitive(room_rad)
modifiers = {p.modifier for p in primitives}
print(modifiers)
```

Alternatively, use `obj2rad()` with `quallist=True` to get just the list of
qualifiers (modifier names) without producing a full scene description:

``` python
qualifiers = pr.obj2rad("room.obj", quallist=True).decode().splitlines()
print(qualifiers)
```

## Define materials

Create a `Primitive` for each modifier. A diffuse plastic material takes five
real arguments: R, G, B reflectances, specularity, and roughness.

``` python
materials = [
    pr.Primitive("void", "plastic", "floor",   [], [0.3, 0.3, 0.3, 0, 0]),
    pr.Primitive("void", "plastic", "walls",   [], [0.5, 0.5, 0.5, 0, 0]),
    pr.Primitive("void", "plastic", "ceiling", [], [0.8, 0.8, 0.8, 0, 0]),
]
```

## Build an octree

Serialize the material primitives to bytes and pass them together with the
geometry bytes to `oconv()` via `stdin`. Both streams are concatenated before
being piped to `oconv`:

``` python
mat_bytes = b"".join(m.bytes for m in materials)
stdin_bytes = mat_bytes + room_rad

oct = pr.oconv(stdin=stdin_bytes)

# Write the octree to disk
with open("room.oct", "wb") as f:
    f.write(oct)
```

## Trace a ray

Pass input rays as bytes to `rtrace()`. Each ray is a line of six
space-separated floats: `ox oy oz dx dy dz`.

``` python
rays = b"0 1 1.5 0 0 1\n"
result = pr.rtrace(rays, "room.oct", outspec="v")
print(result.decode())
```

The `outspec="v"` argument requests radiance values (RGB) at each intersection.
See `help(pr.rtrace)` for the full list of output specifiers and options.
