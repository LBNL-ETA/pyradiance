#include <tuple>
#include "rtmath.h"
#include "paths.h"
#include "view.h"
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/vector.h>
#include <vector>
#include <cstring>


namespace nb = nanobind;
// First define a factory function that creates an initialized VIEW
char *progname = "unknown";
NB_MODULE(rad_view, m) {
    m.doc() = "Radiance common";

    nb::class_<VIEW>(m, "View")
        .def(nb::init<>())
        .def_prop_rw(
          "type", [](VIEW &v) { return (char)v.type; },
          [](VIEW &v, const char t) { v.type = (int)t; })
        .def_prop_rw(
          "vp",
          [](VIEW &v) { return nb::make_tuple(v.vp[0], v.vp[1], v.vp[2]); },
          [](VIEW &v, nb::tuple pos) {
            v.vp[0] = nb::cast<double>(pos[0]);
            v.vp[1] = nb::cast<double>(pos[1]);
            v.vp[2] = nb::cast<double>(pos[2]);
          })
        .def_prop_rw(
          "vdir",
          [](VIEW &v) {
            return nb::make_tuple(v.vdir[0], v.vdir[1], v.vdir[2]);
          },
          [](VIEW &v, nb::tuple dir) {
            v.vdir[0] = nb::cast<double>(dir[0]);
            v.vdir[1] = nb::cast<double>(dir[1]);
            v.vdir[2] = nb::cast<double>(dir[2]);
          })
        .def_prop_rw(
          "vu",
          [](VIEW &v) { return nb::make_tuple(v.vup[0], v.vup[1], v.vup[2]); },
          [](VIEW &v, nb::tuple up) {
            v.vup[0] = nb::cast<double>(up[0]);
            v.vup[1] = nb::cast<double>(up[1]);
            v.vup[2] = nb::cast<double>(up[2]);
          })
        .def_rw("vdist", &VIEW::vdist)
        .def_rw("horiz", &VIEW::horiz)
        .def_rw("vert", &VIEW::vert)
        .def_rw("hoff", &VIEW::hoff)
        .def_rw("voff", &VIEW::voff)
        .def_rw("vfore", &VIEW::vfore)
        .def_rw("vaft", &VIEW::vaft)
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
        .def_rw("vn2", &VIEW::vn2); /* DOT(vvec,vvec) */

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
    });

    m.def("viewfile", [](const char *fname, VIEW *vp, RESOLU *rp) {
        return viewfile(const_cast<char *>(fname), vp, rp);
    });

    m.def("get_view_args", [](VIEW &v) {
        std::vector<std::string> result;

        std::string vt = std::string("-vt") + (char)v.type;
        result.push_back(vt);

        result.push_back("-vp");
        result.push_back(std::to_string(v.vp[0]));
        result.push_back(std::to_string(v.vp[1]));
        result.push_back(std::to_string(v.vp[2]));

        result.push_back("-vd");
        result.push_back(std::to_string(v.vdir[0]*v.vdist));
        result.push_back(std::to_string(v.vdir[1]*v.vdist));
        result.push_back(std::to_string(v.vdir[2]*v.vdist));

        result.push_back("-vu");
        result.push_back(std::to_string(v.vup[0]));
        result.push_back(std::to_string(v.vup[1]));
        result.push_back(std::to_string(v.vup[2]));

        result.push_back("-vh");
        result.push_back(std::to_string(v.horiz));
        result.push_back("-vv");
        result.push_back(std::to_string(v.vert));
        result.push_back("-vs");
        result.push_back(std::to_string(v.hoff));
        result.push_back("-vl");
        result.push_back(std::to_string(v.voff));
        result.push_back("-vo");
        result.push_back(std::to_string(v.vfore));
        result.push_back("-va");
        result.push_back(std::to_string(v.vaft));

        return result;
        });
}
