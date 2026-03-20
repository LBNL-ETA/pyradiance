# How to parse and query a tabulated BSDF file (.xml)

The `pyradiance.bsdf` module provides functions for loading and analyzing a
tabulated BSDF file. See sections below for examples.

``` python
from pyradiance import bsdf
```

Load a BSDF file using `bsdf.load_file()`, which returns an `SDData` object:

``` python
sd = bsdf.load_file("bsdf.xml")
```

When you are done with the object, release its memory with `bsdf.free()`:

``` python
bsdf.free(sd)
```

## Basic information

An `SDData` object exposes several attributes describing the BSDF:

``` python
sd = bsdf.load_file("bsdf.xml")
print(sd.name)   # file name (without extension)
print(sd.matn)   # material name
print(sd.makr)   # manufacturer
print(sd.dim)    # (width, height, thickness) in metres
print(sd.mgf)    # embedded MGF geometry string, or empty string
```

Lambertian (diffuse) components are available as `SDValue` objects with a
`cie_y` attribute (CIE Y luminance):

``` python
print(sd.rLambFront.cie_y)  # diffuse front reflectance
print(sd.rLambBack.cie_y)   # diffuse back reflectance
print(sd.tLambFront.cie_y)  # diffuse front transmittance
print(sd.tLambBack.cie_y)   # diffuse back transmittance
```

Specular distribution components (`SDSpectralDF`) are accessible via `sd.rf`,
`sd.rb`, `sd.tf`, and `sd.tb`:

``` python
print(sd.rf.maxHemi)    # peak front hemispherical reflectance
print(sd.tf.maxHemi)    # peak front hemispherical transmittance
print(sd.rf.minProjSA)  # minimum projected solid angle
```

## Direct hemispherical values

Use `bsdf.direct_hemi()` to query the hemispherical integral over a given
component at an incident direction specified as (theta, phi) in degrees.
The third argument is a bitwise combination of `SAMPLE_*` flags:

- `bsdf.SAMPLE_T` — diffuse transmittance
- `bsdf.SAMPLE_R` — diffuse reflectance
- `bsdf.SAMPLE_ALL` — all components combined
- `bsdf.SAMPLE_ALL & ~bsdf.SAMPLE_R` — all transmittance (exclude reflectance)

``` python
sd = bsdf.load_file("bsdf.xml")

# hemispherical transmittance at normal incidence (theta=0°, phi=0°)
t = bsdf.direct_hemi(sd, 0, 0, bsdf.SAMPLE_T)

# hemispherical reflectance at theta=30°, phi=0°
r = bsdf.direct_hemi(sd, 30, 0, bsdf.SAMPLE_R)

# all transmittance (direct + diffuse) at theta=40°, phi=45°
t_all = bsdf.direct_hemi(sd, 40, 45, bsdf.SAMPLE_ALL & ~bsdf.SAMPLE_R)

bsdf.free(sd)
```

## Querying the projected solid angle given an incident angle

Use `bsdf.size()` to retrieve the minimum and maximum projected solid angles
for a given incident direction. The third argument is `QUERY_MIN + QUERY_MAX`
to request both bounds:

``` python
sd = bsdf.load_file("bsdf.xml")

mn, mx = bsdf.size(sd, 0, 0, bsdf.QUERY_MIN + bsdf.QUERY_MAX)
print("min solid angle:", mn, "max solid angle:", mx)

bsdf.free(sd)
```

You can also specify an outgoing direction with `bsdf.size2()`, which returns
identical min and max values for that exact direction:

``` python
sd = bsdf.load_file("bsdf.xml")

mn, mx = bsdf.size2(sd, 0, 0, 180, 0, bsdf.QUERY_MIN + bsdf.QUERY_MAX)

bsdf.free(sd)
```

## Evaluating the BSDF given an incident and outgoing angle

Use `bsdf.query()` to evaluate the BSDF value at a pair of incident and
outgoing directions. Angles are in degrees; the result is a numpy array of
CIE XYZ tristimulus values.

Here is an example with incident theta=0°, phi=0° and outgoing theta=180°,
phi=0° (normal transmission):

``` python
sd = bsdf.load_file("bsdf.xml")

xyz = bsdf.query(sd, 0, 0, 180, 0)
print("CIE XYZ:", xyz)

bsdf.free(sd)
```

## Generating random scattering samples given an incident direction

Use `bsdf.sample()` to generate N random scattering samples for a given
incident direction. The fourth argument is the number of samples; the fifth
is a `SAMPLE_*` flag selecting the component to sample. The result is an
Nx6 numpy array with each row being (x, y, z, R, G, B).

Here is an example of generating 10 transmittance samples at incident
theta=30°, phi=45°:

``` python
sd = bsdf.load_file("bsdf.xml")

samples = bsdf.sample(sd, 30, 45, 10, bsdf.SAMPLE_T)
# samples.shape == (10, 6): columns are (x, y, z, R, G, B)

bsdf.free(sd)
```
