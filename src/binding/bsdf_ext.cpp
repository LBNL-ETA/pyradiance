#include "bsdf.h"
#include "ray.h"
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>

namespace nb = nanobind;

using Mat3 = nb::ndarray<double, nb::shape<3, 3>>;
using Vec3 = nb::ndarray<double, nb::shape<3>>;
using Vec6 = nb::ndarray<double, nb::shape<6>>;

void vec_from_deg(double theta, double phi, FVECT vec) {
  const double DEG = M_PI / 180.;
  theta *= DEG;
  phi *= DEG;
  vec[0] = vec[1] = sin(theta);
  vec[0] *= cos(phi);
  vec[1] *= sin(phi);
  vec[2] = cos(theta);
}
void get_cie_xyz(const SDValue *val, double cie_xyz[3]) {
  cie_xyz[0] = val->spec.cx / val->spec.cy * val->cieY;
  cie_xyz[1] = val->cieY;
  cie_xyz[2] = (1. - val->spec.cx - val->spec.cy) / val->spec.cy * val->cieY;
}

NB_MODULE(bsdf, m) {
  m.doc() = "Radiance BSDF module extension";

  m.attr("SAMPLE_ALL") = (int)SDsampAll;
  m.attr("SAMPLE_S") = (int)SDsampS;
  m.attr("SAMPLE_T") = (int)SDsampT;
  m.attr("SAMPLE_R") = (int)SDsampR;
  m.attr("SAMPLE_SP") = (int)SDsampSp;
  m.attr("SAMPLE_DF") = (int)SDsampDf;
  m.attr("SAMPLE_SPR") = (int)SDsampSpR;
  m.attr("SAMPLE_SPT") = (int)SDsampSpT;
  m.attr("SAMPLE_SPS") = (int)SDsampSpS;

  m.attr("QUERY_VAL") = (int)SDqueryVal;
  m.attr("QUERY_MIN") = (int)SDqueryMin;
  m.attr("QUERY_MAX") = (int)SDqueryMax;

  nb::class_<C_COLOR>(m, "C_COLOR")
      .def_ro("clock", &C_COLOR::clock)
      .def_ro("client_data", &C_COLOR::client_data)
      .def_ro("flags", &C_COLOR::flags)
      .def_prop_ro(
          "ssamp",
          [](C_COLOR &c) { return nb::make_tuple(&c.ssamp[0], C_CNSS); })
      .def_ro("ssum", &C_COLOR::ssum)
      .def_ro("cx", &C_COLOR::cx)
      .def_ro("cy", &C_COLOR::cy)
      .def_ro("eff", &C_COLOR::eff);

  nb::enum_<SDError>(m, "SDError")
      .value("SDEnone", SDEnone)
      .value("SDEmemory", SDEmemory)
      .value("SDEfile", SDEfile)
      .value("SDEformat", SDEformat)
      .value("SDEargument", SDEargument)
      .value("SDEdata", SDEdata)
      .value("SDEsupport", SDEsupport)
      .value("SDEinternal", SDEinternal)
      .value("SDEunknown", SDEunknown);

  nb::class_<SDComponent>(m, "SDComponent")
      .def_prop_ro("cspec",
                   [](SDComponent &sd) {
                     nb::list result;
                     for (int i = 0; i < SDmaxCh; i++) {
                       result.append(sd.cspec[i]);
                     }
                     return result;
                   })
      .def_ro("func", &SDComponent::func)
      .def_ro("dist", &SDComponent::dist)
      .def_ro("cdList", &SDComponent::cdList);

  // Then bind SDSpectralDF
  nb::class_<SDSpectralDF>(m, "SDSpectralDF")
      .def_ro("minProjSA", &SDSpectralDF::minProjSA)
      .def_ro("maxHemi", &SDSpectralDF::maxHemi)
      .def_ro("ncomp", &SDSpectralDF::ncomp)
      .def_prop_ro("comp", [](SDSpectralDF &sd) {
        nb::list result;
        for (int i = 0; i < sd.ncomp; i++) {
          result.append(sd.comp[i]);
        }
        return result;
      });

  nb::class_<SDValue>(m, "SDValue")
      .def_ro("cie_y", &SDValue::cieY)
      .def_ro("spec", &SDValue::spec);

  nb::class_<SDData>(m, "SDData")
      .def_prop_ro(
          "name",
          [](SDData &sd) -> std::string { return std::string(sd.name); })
      .def_prop_ro(
          "matn",
          [](SDData &sd) -> std::string { return std::string(sd.matn); })
      .def_prop_ro(
          "makr",
          [](SDData &sd) -> std::string { return std::string(sd.makr); })
      .def_prop_ro("mgf",
                   [](SDData &sd) -> std::string {
                     return sd.mgf ? std::string(sd.mgf) : "";
                   })
      .def_prop_ro("dim",
                   [](SDData &sd) {
                     return nb::make_tuple(sd.dim[0], sd.dim[1], sd.dim[2]);
                   })
      .def_ro("rLambFront", &SDData::rLambFront)
      .def_ro("rLambBack", &SDData::rLambBack)
      .def_ro("tLambFront", &SDData::tLambFront)
      .def_ro("tLambBack", &SDData::tLambBack)
      .def_ro("rf", &SDData::rf)
      .def_ro("rb", &SDData::rb)
      .def_ro("tf", &SDData::tf)
      .def_ro("tb", &SDData::tb);

  m.def("load_file", &SDcacheFile);
  m.def("free", &SDfreeCache);
  m.def(
      "inv_xform",
      [](const Mat3 v_mtx) {
        RREAL iMtx[3][3] = {{0}};
        RREAL vMtx[3][3] = {{v_mtx(0, 0), v_mtx(0, 1), v_mtx(0, 2)},
                            {v_mtx(1, 0), v_mtx(1, 1), v_mtx(1, 2)},
                            {v_mtx(2, 0), v_mtx(2, 1), v_mtx(2, 2)}};
        SDinvXform(iMtx, vMtx);
        return Mat3(iMtx);
      },
      nb::rv_policy::reference_internal);

  m.def(
      "comp_xform",
      [](const Vec3 s_nrm, const Vec3 u_vec) {
        RREAL vMtx[3][3] = {{0}};
        const FVECT sNrm = {s_nrm(0), s_nrm(1), s_nrm(2)};
        const FVECT uVec = {u_vec(0), u_vec(1), u_vec(2)};
        SDcompXform(vMtx, sNrm, uVec);
        return Vec3(vMtx);
      },
      nb::rv_policy::reference_internal);

  m.def(
      "map_dir",
      [](const Vec3 inp_vec, Mat3 v_mtx) {
        FVECT resVec = {0};
        RREAL vMtx[3][3] = {
            {v_mtx(0, 0), v_mtx(0, 1), v_mtx(0, 2)},
            {v_mtx(1, 0), v_mtx(1, 1), v_mtx(1, 2)},
            {v_mtx(2, 0), v_mtx(2, 1), v_mtx(2, 2)},
        };
        const FVECT inpVec = {inp_vec(0), inp_vec(1), inp_vec(2)};
        SDmapDir(resVec, vMtx, inpVec);
        return Vec3(resVec);
      },
      nb::rv_policy::reference_internal);

  m.def("size", [](const SDData *sd, const double theta, const double phi,
                   const int qflags) {
    double proj_sa[2] = {0};
    FVECT v1 = {0};
    vec_from_deg(theta, phi, v1);
    SDsizeBSDF(proj_sa, v1, NULL, qflags, sd);
    return nb::make_tuple(proj_sa);
  });

  m.def("size2", [](const SDData *sd, const double theta, const double phi,
                    const double t2, const double p2, const int qflags) {
    double proj_sa[2] = {0};
    FVECT v1 = {0};
    FVECT v2 = {0};
    vec_from_deg(theta, phi, v1);
    vec_from_deg(t2, p2, v2);
    SDsizeBSDF(proj_sa, v1, v2, qflags, sd);
    return nb::make_tuple(proj_sa);
  });

  m.def("direct_hemi",
        [](const SDData *sd, const double theta, const double phi,
           const int sflags) -> double {
          FVECT vin = {0};
          vec_from_deg(theta, phi, vin);
          return SDdirectHemi(vin, sflags, sd);
        });

  m.def("sample", [](const SDData *sd, const double theta, const double phi,
                     const int nsamp, const int sflags) {
    FVECT vin = {0};
    FVECT vout = {0};
    SDValue val;
    vec_from_deg(theta, phi, vin);
    float *result = new float[nsamp * 6];

    for (int i = 0; i<nsamp; i++) {
      int ii = i * 6;
      VCOPY(vout, vin);
      SDsampBSDF(&val, vout,
                 (i + rand() * (1. / (RAND_MAX + .5))) / (double)nsamp, sflags,
                 sd);
      result[ii] = vout[0];
      result[ii + 1] = vout[1];
      result[ii + 2] = vout[2];
      double cie_xyz[3] = {0};
      get_cie_xyz(&val, cie_xyz);
      result[ii + 3] = cie_xyz[0];
      result[ii + 4] = cie_xyz[1];
      result[ii + 5] = cie_xyz[2];
    }
    // Delete 'result' when the 'owner' capsule expires
    nb::capsule owner(result, [](void *p) noexcept { delete[] (float *)p; });
    return nb::ndarray<nb::numpy, float, nb::ndim<2>>(result, {(size_t)nsamp, 6}, owner);
  });

  m.def("query",
        [](const SDData *sd, const double theta_in, const double phi_in,
           const double theta_out, const double phi_out) {
          SDValue val;
          double cie_xyz[3] = {0};
          FVECT vin = {0};
          FVECT vout = {0};
          vec_from_deg(theta_in, phi_in, vin);
          vec_from_deg(theta_out, phi_out, vout);
          SDevalBSDF(&val, vin, vout, sd);
          get_cie_xyz(&val, cie_xyz);
          return nb::ndarray<nb::numpy, float, nb::ndim<1>>(cie_xyz, {3});
        });
}
