# How to load a WaveFront (.obj) model

## Load .obj

```
room = pr.robjutil("room.obj")
```

## Define .obj materials

Getting all the modifiers
``` python
[p.omod for p in pr.read_rad(room)]
```
Displaying all the modifiers that we need to define
```
```
``` python
primitives = []
primitives.append(Primitive("void", "plastic", "white50", [], [.5, .5, .5, 0, 0]))
primitives.append(Primitive("void", "plastic", "white50", [], [.5, .5, .5, 0, 0]))
primitives.append(Primitive("void", "plastic", "white50", [], [.5, .5, .5, 0, 0]))
primitives.append(Primitive("void", "plastic", "white50", [], [.5, .5, .5, 0, 0]))
```

## Create an octree

``` python
with open("room.oct", "wb") as wtr:
    wtr.write(pr.oconv(primitives, stdin=True))
```

## Trace a ray

``` python
pr.rtrace(b"0 0 0 0 0 1", "room.oct")
```


