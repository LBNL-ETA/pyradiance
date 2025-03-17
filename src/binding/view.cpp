#include <tuple>
#include "rtmath.h"
#include "paths.h"
#include "view.h"
#include <nanobind/nanobind.h>
#include <nanobind/stl/tuple.h>

namespace nb = nanobind;

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

}
