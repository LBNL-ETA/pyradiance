# How to parse and query a tabulated BSDF file (.xml)

`Pyradiance` `BSDF` object provides a host of methods for parsing and analyzing a
tabulated BSDF file. See sectons below for examples.
You can instantiate a `BSDF` object by giving the file path to the BSDF (.xml) file.

You can either plainly instantiate the object like so:

``` python
import pyradiance as pr
sd = pr.BSDF("bsdf.xml")
```

You can also instantiate the BSDF object in a context manager, which will clear for you
the memory associated with the loaded BSDF once done:

``` python
with pr.BSDF('bsdf.xml') as sd:
    ...
```

## Basic information

A BSDF object has two attribtues desecribing basic information about the BSDF:
`info` and `components`. Here is an example of accessing the information:

``` python
with pr.BSDF('bsdf.xml') as sd:
    info  = sd.info
    cp = sd.components
```
Here are the results:
```
>>> print(info)
Materials: Name
Manufacturer: Manufacturer
Width x Height x Thickness (m): 0.0 x 0.0 x 0.0
Has geometry: no
>>> print(cp)
Peak front hemispherical reflectance: 0.48338043257526025
Peak front hemispherical transmittance: 0.09124324694247694
Diffuse front reflectance: (0.3883772003721621, 0.3883772003721621, 0.3883771656485355)
Diffuse back reflectance: (0, 0, 0)
Diffuse front transmittance: (0, 0, 0)
Diffuse back transmittance: (0, 0, 0)
```
 
## Direct hemispherical values

```python
with pr.BSDF("bsdf.xml") as sd:
    sd.direct_hemi(0, 0, 't')  # direct hemispherical transmittance at theta=0°, phi=0°
    sd.direct_hemi(30, 0, 'r')  # direct hemispherical reflectance at theta=30°, phi=0°
    sd.direct_hemi(40, 45, 'ts')  # direct - direct transmittance at theta=45°, phi=45°
```

## Querying the projected solid angle given an incident angle

You can query the scattering solid angle of a given incident direction.
Here is an example of query and minimum and maximum solid angle at normal incidence.

``` python
with pr.BSDF('bsdf.xml') as sd:
    min, max = sd.size(0, 0)
```

You can also specify the outgoing angle as well and, as a result, the minimum and maximum
angle will be the same.
``` python
with pr.BSDF('bsdf.xml') as sd:
    min, max = sd.size(0, 0, t2=180, p2=0)
```

## Evaluating the BSDF given an incident and outgoing angle

You can also explicitly evaulate the BSDF at a given incident and outgoing angle.

Here is an example of evaluating a BSDF with an incident theta=30°, phi=45° and outgoing
theta=145°, phi=90°.

``` python
with pr.BSDF('bsdf.xml') as sd:
    sval = sd.eval(30, 45, 145, 90)
```

## Generating random scattering samples given an incident direction

You can generate N random scattering sample given an incident direction. You'd also
need to specify the type of the hemispherical values.

Here is an example of generating 10 transmittance samples with an incident theta=30°, phi=45°.

``` python
with pr.BSDF("bsdf.mxl") as sd:
    vecs, clrs = sd.samples(30, 45, 10, 't')
```
