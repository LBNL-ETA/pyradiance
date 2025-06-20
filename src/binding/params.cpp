#include <tuple>
#include <vector>
#include <cstring>

#include "rtmath.h"
#include "paths.h"
#include "view.h"
#include "ray.h"

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/vector.h>


namespace nb = nanobind;

extern char *progname;

std::string viewstr(VIEW &v) {
    char buffer[512];  
    snprintf(buffer, sizeof(buffer),
        " -vt%c -vp %.6g %.6g %.6g -vd %.6g %.6g %.6g -vu %.6g %.6g %.6g"
        " -vh %.6g -vv %.6g -vo %.6g -va %.6g -vs %.6g -vl %.6g",
        v.type,
        v.vp[0], v.vp[1], v.vp[2],
        v.vdir[0]*v.vdist, v.vdir[1]*v.vdist, v.vdir[2]*v.vdist,
        v.vup[0], v.vup[1], v.vup[2],
        v.horiz, v.vert,
        v.vfore, v.vaft,
        v.hoff, v.voff
    );
    return std::string(buffer);
}

NB_MODULE(rad_params, m) {
	progname = "rad_params";
    m.doc() = "Radiance common";

    nb::class_<VIEW>(m, "View")
        .def(nb::init<>())
        .def_prop_rw(
          "type", [](VIEW &v) { return (char)v.type; },
          [](VIEW &v, const char t) { v.type = (int)t; }, "View types: 'v': perspective, 'l': parallel, 'c': cylindrical panorma, 'h': hemispherical fisheye, 'a': angular fisheye, 's': planispherical fisheye")
        .def_prop_rw(
          "vp",
          [](VIEW &v) { return nb::make_tuple(v.vp[0], v.vp[1], v.vp[2]); },
          [](VIEW &v, nb::tuple pos) {
            v.vp[0] = nb::cast<double>(pos[0]);
            v.vp[1] = nb::cast<double>(pos[1]);
            v.vp[2] = nb::cast<double>(pos[2]);
          }, "View position: x, y, z")
        .def_prop_rw(
          "vdir",
          [](VIEW &v) {
            return nb::make_tuple(v.vdir[0], v.vdir[1], v.vdir[2]);
          },
          [](VIEW &v, nb::tuple dir) {
            v.vdir[0] = nb::cast<double>(dir[0]);
            v.vdir[1] = nb::cast<double>(dir[1]);
            v.vdir[2] = nb::cast<double>(dir[2]);
          }, "View direction: x, y, z")
        .def_prop_rw(
          "vu",
          [](VIEW &v) { return nb::make_tuple(v.vup[0], v.vup[1], v.vup[2]); },
          [](VIEW &v, nb::tuple up) {
            v.vup[0] = nb::cast<double>(up[0]);
            v.vup[1] = nb::cast<double>(up[1]);
            v.vup[2] = nb::cast<double>(up[2]);
          }, "View up direction: x, y, z")
        .def_rw("vdist", &VIEW::vdist)
        .def_rw("horiz", &VIEW::horiz, "View horizontal size")
        .def_rw("vert", &VIEW::vert, "View vertical size")
        .def_rw("hoff", &VIEW::hoff, "View horizontal offset")
        .def_rw("voff", &VIEW::voff, "View vertical offset")
        .def_rw("vfore", &VIEW::vfore, "View fore clipping plane")
        .def_rw("vaft", &VIEW::vaft, "View aft clipping plane")
        .def_prop_rw(
          "hvec",
          [](VIEW &v) {
            return nb::make_tuple(v.hvec[0], v.hvec[1], v.hvec[2]);
          },
          [](VIEW &v, nb::tuple vec) {
            v.hvec[0] = nb::cast<double>(vec[0]);
            v.hvec[1] = nb::cast<double>(vec[1]);
            v.hvec[2] = nb::cast<double>(vec[2]);
          })
        .def_prop_rw(
          "vvec",
          [](VIEW &v) {
            return nb::make_tuple(v.vvec[0], v.vvec[1], v.vvec[2]);
          },
          [](VIEW &v, nb::tuple vec) {
            v.vvec[0] = nb::cast<double>(vec[0]);
            v.vvec[1] = nb::cast<double>(vec[1]);
            v.vvec[2] = nb::cast<double>(vec[2]);
          })
        .def_rw("hn2", &VIEW::hn2)  /* DOT(hvec,hvec) */
        .def_rw("vn2", &VIEW::vn2) /* DOT(vvec,vvec) */
        .def("__repr__", &viewstr)
        .def("__str__", &viewstr);

    m.def("create_default_view", []() {
        VIEW v = {0};  // Zero-initialize the struct
        v.type = 'v';
        v.vp[0] = 0.; v.vp[1] = 0.; v.vp[2] = 0.;
        v.vdir[0] = 0.; v.vdir[1] = 1.; v.vdir[2] = 0.;
        v.vup[0] = 0.; v.vup[1] = 0.; v.vup[2] = 1.;
        v.vdist = 1.;
        v.horiz = 45.;
        v.vert = 45.;
        v.hoff = 0.;
        v.voff = 0.;
        v.vfore = 0.;
        v.vaft = 0.; 
        v.hvec[0] = 1.; v.hvec[1] = 0.; v.hvec[2] = 0.;
        v.vvec[0] = 0.; v.vvec[1] = 0.; v.vvec[2] = 0.;
        v.hn2 = 0.;
        v.vn2 = 0.;
        return v;
    });

    nb::class_<RESOLU>(m, "Resolu")
        .def(nb::init<>())
        .def_rw("rt", &RESOLU::rt)
        .def_rw("xr", &RESOLU::xr)
        .def_rw("yr", &RESOLU::yr);

    m.def("parse_view", [](const char *s) {
        VIEW vp;
        sscanview(&vp, const_cast<char *>(s));
        return vp;
    }, "Parse a view string into a View object");

    m.def("viewfile", [](const char *fname) {
        VIEW vp = {0};
        int result = viewfile(const_cast<char *>(fname), &vp, NULL);
		if (result <= 0) {  // viewfile failed
        throw std::runtime_error("Failed to read view file: " + std::string(fname ? fname : "stdin"));
		}
        return vp;
    }, "Read a view file into a View object");

    m.def("get_view_args", [](VIEW &v) {
        nb::list result;

        std::string vt = std::string("-vt") + (char)v.type;
        result.append(vt);

        result.append("-vp");
        result.append(std::to_string(v.vp[0]));
        result.append(std::to_string(v.vp[1]));
        result.append(std::to_string(v.vp[2]));

        result.append("-vd");
        result.append(std::to_string(v.vdir[0]*v.vdist));
        result.append(std::to_string(v.vdir[1]*v.vdist));
        result.append(std::to_string(v.vdir[2]*v.vdist));

        result.append("-vu");
        result.append(std::to_string(v.vup[0]));
        result.append(std::to_string(v.vup[1]));
        result.append(std::to_string(v.vup[2]));

        result.append("-vh");
        result.append(std::to_string(v.horiz));
        result.append("-vv");
        result.append(std::to_string(v.vert));
        result.append("-vs");
        result.append(std::to_string(v.hoff));
        result.append("-vl");
        result.append(std::to_string(v.voff));
        result.append("-vo");
        result.append(std::to_string(v.vfore));
        result.append("-va");
        result.append(std::to_string(v.vaft));

        return result;
    }, "Returns a list of string for the view");


    nb::class_<RAYPARAMS>(m, "RayParams")
        .def_prop_rw(
            "i", [](RAYPARAMS &param) { return (bool)param.do_irrad; },
            [](RAYPARAMS &param, const bool val) { param.do_irrad = (int)val; },
            "do irradiance")
        .def_prop_rw(
            "u", [](RAYPARAMS &param) { return (bool)param.rand_samp; },
            [](RAYPARAMS &param, const bool val) { param.rand_samp = (int)val; },
            "random sampling")
        .def_prop_rw(
            "dj", [](RAYPARAMS &param) { return param.dstrsrc; },
            [](RAYPARAMS &param, const double val) { param.dstrsrc = val; },
            "direct jitter")
        .def_prop_rw(
            "dt", [](RAYPARAMS &param) { return param.shadthresh; },
            [](RAYPARAMS &param, const double val) { param.shadthresh = val; },
            "direct threshold")
        .def_prop_rw(
            "dc", [](RAYPARAMS &param) { return param.shadcert; },
            [](RAYPARAMS &param, const double val) { param.shadcert = val; },
            "direct certainty")
        .def_prop_rw(
            "dr", [](RAYPARAMS &param) { return param.directrelay; },
            [](RAYPARAMS &param, const int val) { param.directrelay = val; },
            "direct relay")
        .def_prop_rw(
            "dp", [](RAYPARAMS &param) { return param.vspretest; },
            [](RAYPARAMS &param, const int val) { param.vspretest = val; },
            "virtual source pretesting")
        .def_prop_rw(
            "dv", [](RAYPARAMS &param) { return param.directvis; },
            [](RAYPARAMS &param, const int val) { param.directvis = val; },
            "direct visibility")
        .def_prop_rw(
            "ds", [](RAYPARAMS &param) { return param.srcsizerat; },
            [](RAYPARAMS &param, const double val) { param.srcsizerat = val; },
            "source size aspect ratio")
        .def_prop_rw(
            "me",
            [](RAYPARAMS &param) {
              return nb::make_tuple(param.cextinction[0], param.cextinction[1],
                                    param.cextinction[2]);
            },
            [](RAYPARAMS &param, const float v1, const float v2, const float v3) {
              param.cextinction[0] = v1;
              param.cextinction[1] = v2;
              param.cextinction[2] = v3;
            },
            "medium(mist) extinction coefficients")
        .def_prop_rw(
            "ma",
            [](RAYPARAMS &param) {
              return nb::make_tuple(param.salbedo[0], param.salbedo[1],
                                    param.salbedo[2]);
            },
            [](RAYPARAMS &param, const float v1, const float v2, const float v3) {
              param.salbedo[0] = v1;
              param.salbedo[1] = v2;
              param.salbedo[2] = v3;
            },
            "medium (mist) scattering albedo")
        .def_prop_rw(
            "mg", [](RAYPARAMS &param) { return param.seccg; },
            [](RAYPARAMS &param, const double val) { param.seccg = val; },
            "medium (mist) eccentricity factor")
        .def_prop_rw(
            "ms", [](RAYPARAMS &param) { return param.ssampdist; },
            [](RAYPARAMS &param, const double val) { param.ssampdist = val; },
            "medium (mist) sampling distance")
        .def_prop_rw(
            "st", [](RAYPARAMS &param) { return param.specthresh; },
            [](RAYPARAMS &param, const double val) { param.specthresh = val; },
            "specular threshold")
        .def_prop_rw(
            "ss", [](RAYPARAMS &param) { return param.specjitter; },
            [](RAYPARAMS &param, const double val) { param.specjitter = val; },
            "specular jitter")
        .def_prop_rw(
            "bv", [](RAYPARAMS &param) { return (bool)(param.backvis); },
            [](RAYPARAMS &param, const bool val) { param.backvis = (int)val; },
            "source back side visibility")
        .def_prop_rw(
            "lr", [](RAYPARAMS &param) { return param.maxdepth; },
            [](RAYPARAMS &param, const int val) { param.maxdepth = val; },
            "max depth")
        .def_prop_rw(
            "lw", [](RAYPARAMS &param) { return param.minweight; },
            [](RAYPARAMS &param, const double val) { param.minweight = val; },
            "minimum ray weight")
        .def_prop_rw(
            "af", [](RAYPARAMS &param) { return param.ambfile; },
            [](RAYPARAMS &param, const std::string val) {
              strncpy(param.ambfile, val.c_str(), 511);
            param.ambfile[511] = '\0';
            },
            "ambient file")
        .def_prop_rw(
            "av",
            [](RAYPARAMS &param) {
              return nb::make_tuple(param.ambval[0], param.ambval[1],
                                    param.ambval[2]);
            },
            [](RAYPARAMS &param, std::vector<float> vals) {
              param.ambval[0] = vals[0];
              param.ambval[1] = vals[1];
              param.ambval[2] = vals[2];
            },
            "ambient values")
        .def_prop_rw(
            "aw", [](RAYPARAMS &param) { return param.ambvwt; },
            [](RAYPARAMS &param, const int val) { param.ambvwt = val; },
            "ambient weight")
        .def_prop_rw(
            "aa", [](RAYPARAMS &param) { return param.ambacc; },
            [](RAYPARAMS &param, const double val) { param.ambacc = val; },
            "ambient accuracy")
        .def_prop_rw(
            "ar", [](RAYPARAMS &param) { return param.ambres; },
            [](RAYPARAMS &param, const int val) { param.ambres = val; },
            "ambient resolution")
        .def_prop_rw(
            "ad", [](RAYPARAMS &param) { return param.ambdiv; },
            [](RAYPARAMS &param, const int val) { param.ambdiv = val; },
            "ambient division")
        .def_prop_rw(
            "as_", [](RAYPARAMS &param) { return param.ambssamp; },
            [](RAYPARAMS &param, const int val) { param.ambssamp = val; },
            "ambient super sampling")
        .def_prop_rw(
            "ab", [](RAYPARAMS &param) { return param.ambounce; },
            [](RAYPARAMS &param, const int val) { param.ambounce = val; },
            "ambient bounce")
        .def_prop_rw(
            "ambincl", [](RAYPARAMS &param) { return param.ambincl; },
            [](RAYPARAMS &param, const bool val) { param.ambincl = val; },
            "ambient inclusion/exclusion")
        .def_prop_rw(
            "amblist",
            [](RAYPARAMS &param) {
                nb::list result;
                for (int i = 0; i < AMBLLEN + 1; i++) {
                  if (amblist[i] == nullptr) {
                    break;
                  }
                  result.append(amblist[i]);
                }
                return result;
            },
            [](RAYPARAMS &param, std::vector<const char *> vals) {
                char **amblp = amblist;
                for (int i = 0; i < vals.size(); i++) {
                  *amblp++ = savqstr(vals[i]);
                }
                *amblp = NULL;
            }
        );

    m.def("get_default_ray_params", []() {
        RAYPARAMS rp;
        ray_defaults(&rp);
        return rp;
    });

    m.def("get_ray_params_args", [](RAYPARAMS &r){
        nb::list args;

        if (r.rand_samp) {
            args.append("-u+");
        }
        if (r.backvis)
            args.append("-bv");
        args.append("-dt");
        args.append(std::to_string(r.shadthresh));
        args.append("-dc");
        args.append(std::to_string(r.shadcert));
        args.append("-dj");
        args.append(std::to_string(r.dstrsrc));
        args.append("-dr");
        args.append(std::to_string(r.directrelay));
        args.append("-dp");
        args.append(std::to_string(r.vspretest));
        if (r.directvis)
            args.append("-dv");
        args.append("-ds");
        args.append(std::to_string(r.srcsizerat));

        args.append("-st");
        args.append(std::to_string(r.specthresh));
        args.append("-ss");
        args.append(std::to_string(r.specjitter));

        args.append("-lr");
        args.append(std::to_string(r.maxdepth));
        args.append("-lw");
        args.append(std::to_string(r.minweight));

        if (r.do_irrad)
            args.append("-i+");
        args.append("-av");
        args.append(std::to_string(r.ambval[0]));
        args.append(std::to_string(r.ambval[1]));
        args.append(std::to_string(r.ambval[2]));
        args.append("-aw");
        args.append(std::to_string(r.ambvwt));
        args.append("-aa");
        args.append(std::to_string(r.ambacc));
        args.append("-ar");
        args.append(std::to_string(r.ambres));
        args.append("-ad");
        args.append(std::to_string(r.ambdiv));
        args.append("-as");
        args.append(std::to_string(r.ambssamp));
        args.append("-ab");
        args.append(std::to_string(r.ambounce));
        if (r.ambincl == 1 || r.ambincl == 0) {
            if (r.ambincl == 1) {
                args.append("-ai");
            } else if (r.ambincl == 0) {
                args.append("-ae");
            }
            for (int i = 0; i < AMBLLEN + 1; i++) {
              if (amblist[i] == nullptr) {
                break;
              }
              args.append(amblist[i]);
            }
        }
        if (r.ambfile[0] != '\0') {
            args.append("-af");
            args.append(r.ambfile);
        }

        args.append("-me");
        args.append(std::to_string(r.cextinction[0]));
        args.append(std::to_string(r.cextinction[1]));
        args.append(std::to_string(r.cextinction[2]));
        args.append("-ma");
        args.append(std::to_string(r.salbedo[0]));
        args.append(std::to_string(r.salbedo[1]));
        args.append(std::to_string(r.salbedo[2]));
        args.append("-mg");
        args.append(std::to_string(r.seccg));
        args.append("-ms");
        args.append(std::to_string(r.ssampdist));

        return args;
    }, "Returns a list of strings given a RayParams object");
}
