import os
import unittest
from datetime import datetime

import pyradiance as pr


class TestPyradianceAPI(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(__file__), "Resources")
    floor = os.path.join(resources_dir, "floor 1.rad")
    ceiling = os.path.join(resources_dir, "ceiling.rad")
    material = os.path.join(resources_dir, "materials.mat")
    source = os.path.join(resources_dir, "sky.rad")

    def test_primitive(self):
        prim = pr.Primitive("void", "plastic", "white", [], [0.5, 0.6, 0.7, 0, 0])
        self.assertEqual(prim.ptype, "plastic")
        self.assertEqual(prim.bytes, b"void plastic white 0 0 5 0.5 0.6 0.7 0 0 ")

    def test_load_scene(self):
        """Test the load_scene function."""
        # assert load_scene('test') == 'test'
        scene = pr.Scene("test_scene")
        scene.add_surface(self.floor)
        scene.add_surface(self.ceiling)
        scene.add_material(self.material)
        scene.add_source(os.path.join(self.resources_dir, "sky.rad"))
        self.assertEqual(scene.sid, "test_scene")
        self.assertTrue(self.floor in scene.surfaces)
        self.assertTrue(self.material in scene.materials)
        self.assertTrue(self.source in scene.sources)
        self.assertTrue(self.ceiling in scene.surfaces)

    def test_load_scene_at_once(self):
        """Test the load_scene function."""
        # assert load_scene('test') == 'test'
        scene = pr.Scene(
            "test_scene2",
            surfaces=[self.floor],
            materials=[self.material],
            sources=[self.source],
        )
        self.assertEqual(scene.sid, "test_scene2")
        self.assertTrue(self.floor in scene.surfaces)
        self.assertTrue(self.material in scene.materials)
        self.assertTrue(self.source in scene.sources)

    def test_parse_view(self):
        inp_str = "-vta -vv 180 -vh 180 -vp 0 0 0 -vd 0 -1 0"
        res = pr.parse_view(inp_str)
        self.assertEqual(res.vp, (0, 0, 0))
        self.assertEqual(res.vdir, (0, -1, 0))
        self.assertEqual(res.type, "a")
        self.assertEqual(res.horiz, 180)

    def test_parse_opt(self):
        inp_str = "-ab 8 -ad 1024 -u- -aa .1 -lw 1e-8 -av 1 2 3 -af test.amf"
        pr.set_option(inp_str.split())
        rparams = pr.get_ray_params()
        self.assertEqual(rparams.ab, 8)
        self.assertEqual(rparams.ad, 1024)
        self.assertEqual(rparams.u, False)
        self.assertEqual(rparams.aa, 0.1)
        self.assertEqual(rparams.lw, 1e-8)
        self.assertEqual(rparams.av, (1, 2, 3))
        self.assertEqual(rparams.af, "test.amf")

    def test_ray_param(self):
        rp = pr.get_ray_params()
        rp.amblist = ["a1", "a2"]
        rp.ab = 2
        rp.ambincl = True
        rp.ad = 1024
        rp.u = True
        rp.i = False
        rp.av = 1.0, 2.0, 3.0
        rp.af = "test.amb"
        pr.set_ray_params(rp)
        rp2 = pr.get_ray_params()
        self.assertEqual(rp.amblist, rp2.amblist)
        self.assertEqual(rp.ab, rp2.ab)
        self.assertEqual(rp.ad, rp2.ad)
        self.assertEqual(rp.av, rp2.av)
        self.assertEqual(rp.af, rp2.af)
        self.assertEqual(rp.ambincl, rp2.ambincl)
        self.assertEqual(rp.u, rp2.u)
        self.assertEqual(rp.i, rp2.i)
        pr.set_ray_params(pr.get_default_ray_params())


class TestPyradianceCLI(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(__file__), "Resources")
    floor = os.path.join(resources_dir, "floor 1.rad")
    ceiling = os.path.join(resources_dir, "ceiling.rad")
    material = os.path.join(resources_dir, "materials.mat")
    source = os.path.join(resources_dir, "sky.rad")

    def test_gendaylit(self):
        res = pr.gendaylit(
            datetime(2022, 2, 1, 12), 37, 122, 120, dirnorm=800, diffhor=100
        )
        ptypes = {p.ptype for p in pr.parse_primitive(res.decode())}
        self.assertEqual(ptypes, {"light", "brightfunc", "source"})

    # def test_render(resources_dir: Path):
    #     """Test the render function."""
    #     aview = pr.View(
    #         position=(1, 1, 1),
    #         direction=(0, -1, 0),
    #     )
    #     scene = pr.Scene("test_scene")
    #     scene.add_surface(resources_dir / "floor 1.rad")
    #     scene.add_surface(resources_dir / "ceiling.rad")
    #     scene.add_material(resources_dir / "materials.mat")
    #     scene.add_source(resources_dir / "sky.rad")
    #     scene.add_view(aview)
    #     pr.render(scene)

    def test_rfluxmtx(self):
        """Test the rfluxmtx function."""
        receiver = os.path.join(self.resources_dir, "skyr4.rad")
        rays = b"1.0 1 1 0 0 1"
        scene = (
            self.material,
            self.floor,
            self.ceiling,
        )
        result = pr.rfluxmtx(receiver, rays=rays, scene=scene)
        self.assertGreater(len(result), 0)

    def test_ra_tiff(self):
        """Test the ra_tiff function."""
        hdr = os.path.join(self.resources_dir, "test.hdr")
        out = "test.tif"
        pr.ra_tiff(hdr, out=str(out))
        self.assertTrue(os.path.exists(out))
        os.remove(out)

    def test_genbox(self):
        out_bytes = pr.genbox("mat", "name", 1, 2, 3)
        out_str = out_bytes.decode()
        prims = pr.parse_primitive(out_str)
        self.assertEqual(
            prims[0],
            pr.Primitive(
                "mat", "polygon", "name.1540", [], [1, 0, 0, 1, 0, 3, 0, 0, 3, 0, 0, 0]
            ),
        )

    def test_genrev(self):
        out_bytes = pr.genrev("steel", "torus", "sin(2*PI*t)", "2+cos(2*PI*t)", 2)
        out_str = out_bytes.decode()
        prims = pr.parse_primitive(out_str)
        self.assertEqual(
            prims[0],
            pr.Primitive(
                "steel", "ring", "torus.1", [], [0, 0, 1.22464679915e-16, 0, 0, 1, 3, 1]
            ),
        )
