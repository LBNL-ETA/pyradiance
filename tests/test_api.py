import os
import unittest
from datetime import datetime
from pathlib import Path
import shutil

import pyradiance as pr


class TestPyradianceAPI(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(__file__), "Resources")
    floor = os.path.join(resources_dir, "floor 1.rad")
    ceiling = os.path.join(resources_dir, "ceiling.rad")
    material = os.path.join(resources_dir, "materials.mat")
    source = os.path.join(resources_dir, "sky.rad")
    smd_file = os.path.join(resources_dir, "spectral.csv")

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

    @unittest.skipIf(os.name=='nt', "test not supported on Windows")
    def test_parse_view(self):
        inp_str = "-vta -vv 180 -vh 180 -vp 0 0 0 -vd 0 -1 0"
        res = pr.parse_view(inp_str)
        self.assertEqual(res.vp, (0, 0, 0))
        self.assertEqual(res.vdir, (0, -1, 0))
        self.assertEqual(res.type, "a")
        self.assertEqual(res.horiz, 180)

    @unittest.skipIf(os.name=='nt', "test not supported on Windows")
    def test_ray_param(self):
        pr.ray_done(1)
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
        pr.set_ray_params()

    @unittest.skipIf(os.name=='nt', "test not supported on Windows")
    def test_parse_opt(self):
        pr.ray_done(1)
        inp_str = "-ab 8 -ad 1024 -u- -aa .1 -lw 1e-8 -av 1 2 3"
        pr.set_option(inp_str.split())
        rparams = pr.get_ray_params()
        self.assertEqual(rparams.ab, 8)
        self.assertEqual(rparams.ad, 1024)
        self.assertEqual(rparams.u, False)
        self.assertEqual(rparams.aa, 0.1)
        self.assertEqual(rparams.lw, 1e-8)
        self.assertEqual(rparams.av, (1, 2, 3))
        pr.set_ray_params()

    def test_load_material_smd(self):
        path = Path(self.smd_file)
        prim = pr.load_material_smd(path)
        for v, t in zip(prim[0].fargs, [0.5206966996192932, 0.3083151578903198, 0.02297455072402954, 0.00482973841239237, 0.0]):
            self.assertAlmostEqual(v, t, places=4)
        prim2 = pr.load_material_smd(path, spectral=True, roughness=0.2)
        for v, t in zip(prim2[1].fargs, [1., 1., 1., 0.00482973841239237, 0.2]):
            self.assertAlmostEqual(v, t, places=4)

    def test_create_default_view(self):
        myview = pr.create_default_view()
        self.assertEqual(myview.type , 'v')

    def test_view_mod(self):
        myview = pr.create_default_view()
        myview.type = 'a'
        self.assertEqual(myview.type , 'a')
        myview.vp = 1,1,1
        self.assertEqual(myview.vp , (1,1,1))

    def test_view_args(self):
        myview = pr.create_default_view()
        myview.type = 'a'
        myview.vp = 1,1,1
        args = pr.get_view_args(myview)
        self.assertEqual(args, ['-vta', '-vp', '1.000000', '1.000000', '1.000000', '-vd', '0.000000', '1.000000', '0.000000', '-vu', '0.000000', '0.000000', '1.000000', '-vh', '45.000000', '-vv', '45.000000', '-vs', '0.000000', '-vl', '0.000000', '-vo', '0.000000', '-va', '0.000000'])

    def test_parse_view(self):
        view = "-vta -vp 1 2 3 -vd 4 5 6 -vv 180 -vh 170"
        myview = pr.parse_view(view)
        self.assertEqual(myview.type, 'a')
        self.assertEqual(myview.vp, (1,2,3))
        self.assertEqual(myview.vdir, (4,5,6))
        self.assertEqual(myview.horiz, 170)
        self.assertEqual(myview.vert, 180)

    def test_get_default_ray_params(self):
        params = pr.get_default_ray_params()
        params.ab = 3
        self.assertEqual(params.ab, 3)

    def test_get_ray_params_args(self):
        params = pr.get_default_ray_params()
        params.ab = 3
        params.ambincl = True
        params.amblist = ["test"]
        args = pr.get_ray_params_args(params)
        self.assertEqual(args, ['-u+', '-bv', '-dt', '0.030000', '-dc', '0.750000', '-dj', '0.000000', '-dr', '2', '-dp', '512', '-dv', '-ds', '0.200000', '-st', '0.150000', '-ss', '1.000000', '-lr', '-10', '-lw', '0.000100', '-av', '0.000000', '0.000000', '0.000000', '-aw', '0', '-aa', '0.100000', '-ar', '256', '-ad', '1024', '-as', '512', '-ab', '3', '-ai', 'test', '-me', '0.000000', '0.000000', '0.000000', '-ma', '0.000000', '0.000000', '0.000000', '-mg', '0.000000', '-ms', '0.000000'])



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

    def test_gensky(self):
        res = pr.gensky(
            datetime(2022, 2, 1, 12), 37, 122, 120,
        )
        ptypes = {p.ptype for p in pr.parse_primitive(res.decode())}
        self.assertEqual(ptypes, {"light", "brightfunc", "source"})


    def test_genssky(self):
        pass
        # res = pr.genssky(
        #     datetime(2022, 2, 1, 12), 37, 122, 120, nthreads=4
        # )
        # ptypes = {p.ptype for p in pr.parse_primitive(res.decode())}
        # self.assertEqual(ptypes, {"light", "source", "spectrum", "specpict"})
        # os.remove("out_sky.hsr")
        # shutil.rmtree("atmos_data")

    def test_gendaymtx(self):
        pass

    def test_gensdaymtx(self):
        pass

    def test_render(self):
        """Test the render function."""
        aview = pr.View()
        aview.type = 'a'
        aview.vp = (1, 2, 1)
        aview.vdir = (0, -1 ,0)
        aview.vu = (0, 0, 1)
        aview.horiz = 180
        aview.vert = 180
        scene = pr.Scene("test_scene")
        scene.add_surface(self.floor)
        scene.add_surface(self.ceiling)
        scene.add_material(self.material)
        scene.add_source(self.source)
        scene.add_view(aview)
        img = pr.render(scene, quality='low', ambbounce=1, nproc=4, ambcache=True, resolution=(800,800))
        os.remove(scene.octree)
        os.remove(scene._moctree)
        os.remove(f"{scene.sid}.amb")

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

    def test_genblinds(self):
        result = pr.genblinds(
            mat="white",
            name="blinds",
            depth=0.05,
            width=1,
            height=1,
            nslats=10,
            angle=45,
            rcurv = 0,)

    def test_genbsdf(self):
        sol_mat = pr.ShadingMaterial(0.5, 0, 0)
        vis_mat = pr.ShadingMaterial(0.6, 0, 0)
        ir_mat = pr.ShadingMaterial(0.9, 0, 0)
        geom = pr.BlindsGeometry(
            depth=0.05,
            width=1,
            height=1,
            nslats=20,
            angle=45,
            rcurv=1,
        )
        sol_blinds = pr.generate_blinds(sol_mat, geom)
        vis_blinds = pr.generate_blinds(vis_mat, geom)
        ir_blinds = pr.generate_blinds(ir_mat, geom)
        sol_results = pr.generate_bsdf(sol_blinds, nsamp=10, params=["-ab", "1"])
        vis_results = pr.generate_bsdf(vis_blinds, nsamp=10, params=["-ab", "1"])
        ir_results = pr.generate_bsdf(ir_blinds, basis='u', nsamp=10, params=["-ab", "1"])
        xml = pr.generate_xml(sol_results, vis_results, ir_results)

    def test_rcontrib(self):
        pass

    def test_pcomb(self):
        pass

    def test_pcond(self):
        pass


if __name__ == "__main__":
    unittest.main()
