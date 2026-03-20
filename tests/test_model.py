"""
Tests for pyradiance.model — Primitive and Scene.
"""

import os
import tempfile
import unittest
from pathlib import Path

import pyradiance as pr
from pyradiance.model import Primitive, Scene


class TestPrimitive(unittest.TestCase):
    """Tests for the Primitive dataclass."""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def test_basic_fields(self):
        p = Primitive("void", "plastic", "white", [], [0.5, 0.6, 0.7, 0, 0])
        self.assertEqual(p.modifier, "void")
        self.assertEqual(p.ptype, "plastic")
        self.assertEqual(p.identifier, "white")
        self.assertEqual(p.sargs, [])
        self.assertEqual(p.fargs, [0.5, 0.6, 0.7, 0, 0])

    def test_empty_args(self):
        p = Primitive("void", "plastic", "black", [], [])
        self.assertEqual(p.sargs, [])
        self.assertEqual(p.fargs, [])

    def test_with_string_args(self):
        p = Primitive("void", "trans", "glass", ["mat.cal"], [])
        self.assertEqual(p.sargs, ["mat.cal"])

    # ------------------------------------------------------------------
    # bytes property
    # ------------------------------------------------------------------

    def test_bytes_with_fargs(self):
        p = Primitive("void", "plastic", "white", [], [0.5, 0.6, 0.7, 0, 0])
        self.assertEqual(p.bytes, b"void plastic white 0 0 5 0.5 0.6 0.7 0 0 ")

    def test_bytes_empty_fargs(self):
        p = Primitive("void", "plastic", "black", [], [])
        self.assertEqual(p.bytes, b"void plastic black 0 0 0 ")

    def test_bytes_with_sargs(self):
        p = Primitive("void", "mixfunc", "mf", ["f1", "f2"], [])
        result = p.bytes.decode()
        self.assertIn("2 f1 f2", result)

    def test_bytes_roundtrip(self):
        """bytes output can be parsed back into an equivalent Primitive."""
        p = Primitive("void", "plastic", "mat", [], [0.3, 0.3, 0.3, 0, 0])
        parsed = pr.parse_primitive(p.bytes.decode())
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].modifier, p.modifier)
        self.assertEqual(parsed[0].ptype, p.ptype)
        self.assertEqual(parsed[0].identifier, p.identifier)
        for v, t in zip(parsed[0].fargs, p.fargs):
            self.assertAlmostEqual(v, t, places=6)

    def test_bytes_works_with_tuple_fargs(self):
        """fargs typed as Sequence[float] — must work with a tuple, not just list."""
        p = Primitive("void", "plastic", "mat", [], (0.1, 0.2, 0.3, 0.0, 0.0))
        result = p.bytes.decode()
        self.assertIn("5 0.1 0.2 0.3 0.0 0.0", result)

    # ------------------------------------------------------------------
    # __str__
    # ------------------------------------------------------------------

    def test_str_format(self):
        p = Primitive("void", "plastic", "white", [], [0.5, 0.6, 0.7, 0, 0])
        s = str(p)
        lines = s.strip().splitlines()
        self.assertEqual(lines[0], "void plastic white")
        self.assertEqual(lines[1], "0 ")          # 0 sargs
        self.assertEqual(lines[2], "0")            # always 0 in middle field
        self.assertIn("0.5", lines[3])
        self.assertIn("0.6", lines[3])

    def test_str_roundtrip(self):
        """__str__ output must parse back into an equivalent Primitive."""
        p = Primitive("void", "plastic", "mat", [], [0.3, 0.3, 0.3, 0, 0])
        parsed = pr.parse_primitive(str(p))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].identifier, p.identifier)
        for v, t in zip(parsed[0].fargs, p.fargs):
            self.assertAlmostEqual(v, t, places=6)

    def test_str_no_comma_in_fargs(self):
        """Legacy bug: str(list) produces commas; our implementation must not."""
        p = Primitive("void", "plastic", "mat", [], [1.0, 2.0, 3.0])
        self.assertNotIn(",", str(p))
        self.assertNotIn(",", p.bytes.decode())


class TestScene(unittest.TestCase):
    """Tests for the Scene class."""

    resources_dir = os.path.join(os.path.dirname(__file__), "Resources")
    floor = os.path.join(resources_dir, "floor 1.rad")
    ceiling = os.path.join(resources_dir, "ceiling.rad")
    material = os.path.join(resources_dir, "materials.mat")
    source = os.path.join(resources_dir, "sky.rad")

    # ------------------------------------------------------------------
    # Construction & properties
    # ------------------------------------------------------------------

    def test_sid_and_octree_names(self):
        s = Scene("myroom")
        self.assertEqual(s.sid, "myroom")
        self.assertEqual(s.octree, "myroom.oct")
        self.assertEqual(s._moctree, "mmyroom.oct")

    def test_empty_sid_raises(self):
        with self.assertRaises(ValueError):
            Scene("")

    def test_initial_collections_empty(self):
        s = Scene("s")
        self.assertEqual(len(s.surfaces), 0)
        self.assertEqual(len(s.materials), 0)
        self.assertEqual(len(s.sources), 0)
        self.assertEqual(len(s.views), 0)
        self.assertEqual(len(s.sensors), 0)

    def test_changed_flag_starts_true(self):
        s = Scene("s")
        self.assertTrue(s.changed)

    # ------------------------------------------------------------------
    # add / remove with file paths
    # ------------------------------------------------------------------

    def test_add_surface_str(self):
        s = Scene("s")
        s.add_surface(self.floor)
        self.assertIn(self.floor, s.surfaces)

    def test_add_surface_path(self):
        s = Scene("s")
        s.add_surface(Path(self.floor))
        self.assertIn(self.floor, s.surfaces)

    def test_add_surface_str_and_path_same_key(self):
        """Adding the same file as str and Path must deduplicate to one entry."""
        s = Scene("s")
        s.add_surface(self.floor)
        s.add_surface(Path(self.floor))
        self.assertEqual(len(s.surfaces), 1)

    def test_add_nonexistent_file_raises(self):
        s = Scene("s")
        with self.assertRaises(FileNotFoundError):
            s.add_surface("/no/such/file.rad")

    def test_add_surface_marks_changed(self):
        s = Scene("s")
        s._changed = False
        s.add_surface(self.floor)
        self.assertTrue(s.changed)

    def test_remove_surface_str(self):
        s = Scene("s")
        s.add_surface(self.floor)
        s.remove_surface(self.floor)
        self.assertNotIn(self.floor, s.surfaces)
        self.assertEqual(len(s.surfaces), 0)

    def test_remove_surface_path_after_adding_str(self):
        """remove_surface(Path(...)) must work even if the surface was added as a str."""
        s = Scene("s")
        s.add_surface(self.floor)
        s.remove_surface(Path(self.floor))   # was Bug 3
        self.assertEqual(len(s.surfaces), 0)

    def test_remove_str_after_adding_path(self):
        """The reverse: added as Path, removed as str."""
        s = Scene("s")
        s.add_surface(Path(self.floor))
        s.remove_surface(self.floor)
        self.assertEqual(len(s.surfaces), 0)

    def test_remove_surface_marks_changed(self):
        s = Scene("s")
        s.add_surface(self.floor)
        s._changed = False
        s.remove_surface(self.floor)
        self.assertTrue(s.changed)

    def test_remove_nonexistent_raises(self):
        s = Scene("s")
        with self.assertRaises(KeyError):
            s.remove_surface(self.floor)

    # ------------------------------------------------------------------
    # add / remove with Primitive objects
    # ------------------------------------------------------------------

    def test_add_primitive_surface(self):
        s = Scene("s")
        p = Primitive("void", "plastic", "white", [], [0.5, 0.5, 0.5, 0, 0])
        s.add_surface(p)
        self.assertIn("white", s.surfaces)
        self.assertIs(s.surfaces["white"], p)

    def test_remove_primitive_surface(self):
        s = Scene("s")
        p = Primitive("void", "plastic", "white", [], [0.5, 0.5, 0.5, 0, 0])
        s.add_surface(p)
        s.remove_surface(p)
        self.assertNotIn("white", s.surfaces)

    def test_add_duplicate_primitive_replaces(self):
        """Adding a Primitive with the same identifier overwrites the old one."""
        s = Scene("s")
        p1 = Primitive("void", "plastic", "mat", [], [0.5, 0.5, 0.5, 0, 0])
        p2 = Primitive("void", "plastic", "mat", [], [0.8, 0.8, 0.8, 0, 0])
        s.add_material(p1)
        s.add_material(p2)
        self.assertEqual(len(s.materials), 1)
        self.assertIs(s.materials["mat"], p2)

    def test_add_unsupported_type_raises(self):
        s = Scene("s")
        with self.assertRaises(TypeError):
            s._add(42, "_surfaces")

    # ------------------------------------------------------------------
    # materials and sources
    # ------------------------------------------------------------------

    def test_add_remove_material(self):
        s = Scene("s")
        s.add_material(self.material)
        self.assertIn(self.material, s.materials)
        s.remove_material(self.material)
        self.assertNotIn(self.material, s.materials)

    def test_add_remove_source(self):
        s = Scene("s")
        s.add_source(self.source)
        self.assertIn(self.source, s.sources)
        s.remove_source(self.source)
        self.assertNotIn(self.source, s.sources)

    # ------------------------------------------------------------------
    # views and sensors
    # ------------------------------------------------------------------

    def test_add_view(self):
        s = Scene("s")
        v = pr.create_default_view()
        s.add_view(v)
        self.assertEqual(len(s.views), 1)
        self.assertIs(s.views[0], v)

    def test_add_multiple_views(self):
        s = Scene("s")
        v1 = pr.create_default_view()
        v2 = pr.create_default_view()
        s.add_view(v1)
        s.add_view(v2)
        self.assertEqual(len(s.views), 2)

    def test_add_sensor_valid(self):
        s = Scene("s")
        sensor = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
        s.add_sensor(sensor)
        self.assertEqual(len(s.sensors), 1)
        self.assertEqual(s.sensors[0], sensor)

    def test_add_sensor_wrong_length_raises(self):
        s = Scene("s")
        with self.assertRaises(ValueError):
            s.add_sensor([0.0, 0.0, 0.0])

    # ------------------------------------------------------------------
    # kwargs constructor
    # ------------------------------------------------------------------

    def test_constructor_kwargs(self):
        s = Scene(
            "s",
            surfaces=[self.floor],
            materials=[self.material],
            sources=[self.source],
        )
        self.assertIn(self.floor, s.surfaces)
        self.assertIn(self.material, s.materials)
        self.assertIn(self.source, s.sources)

    # ------------------------------------------------------------------
    # build / changed flag
    # ------------------------------------------------------------------

    def test_build_creates_octrees(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = os.getcwd()
            os.chdir(tmpdir)
            try:
                s = Scene("room")
                s.add_material(Path(self.material))
                s.add_surface(Path(self.floor))
                s.add_surface(Path(self.ceiling))
                s.build()
                self.assertTrue(os.path.exists("room.oct"))
                self.assertTrue(os.path.exists("mroom.oct"))
                self.assertFalse(s.changed)
            finally:
                os.chdir(orig)

    def test_build_not_called_twice_unchanged(self):
        """build() must skip the rebuild if nothing changed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = os.getcwd()
            os.chdir(tmpdir)
            try:
                s = Scene("room2")
                s.add_material(Path(self.material))
                s.add_surface(Path(self.floor))
                s.build()
                mtime = os.path.getmtime("room2.oct")
                s.build()   # second call — should be a no-op
                self.assertEqual(os.path.getmtime("room2.oct"), mtime)
            finally:
                os.chdir(orig)

    def test_build_reruns_after_change(self):
        """build() must rebuild after a surface is added post first build."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = os.getcwd()
            os.chdir(tmpdir)
            try:
                s = Scene("room3")
                s.add_material(Path(self.material))
                s.add_surface(Path(self.floor))
                s.build()
                import time; time.sleep(0.05)   # ensure mtime would differ
                s.add_surface(Path(self.ceiling))
                self.assertTrue(s.changed)
                s.build()
                self.assertFalse(s.changed)
            finally:
                os.chdir(orig)

    def test_build_stdin_not_leaked_between_octrees(self):
        """
        Regression for Bug 4: stdin from the material octree must not leak
        into the surface octree build.  A Primitive material (sent via stdin
        to the first oconv) must not corrupt the second oconv that only takes
        file-path surfaces.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = os.getcwd()
            os.chdir(tmpdir)
            try:
                # Use a self-contained plastic material as a Primitive so
                # the surfaces (floor/ceiling) reference a known modifier.
                mat = Primitive("void", "plastic", "white", [], [0.5, 0.5, 0.5, 0, 0])
                # Build a minimal surface that only uses "white"
                surf = Primitive(
                    "white", "polygon", "floor",
                    [],
                    [0, 0, 0,  1, 0, 0,  1, 1, 0,  0, 1, 0],
                )
                s = Scene("room4")
                s.add_material(mat)   # Primitive → stdin in first oconv
                s.add_surface(surf)   # Primitive → stdin in second oconv (no file paths)
                s.build()             # must not raise
                self.assertTrue(os.path.getsize("room4.oct") > 0)
            finally:
                os.chdir(orig)


if __name__ == "__main__":
    unittest.main()
