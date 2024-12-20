#include <cstring>
#include <functional>
#include <memory>
#include <unordered_map>
#include <utility>
#include <vector>

#include "RcontribSimulManager.h"
#include "RdataShare.h"
#include "RpictSimulManager.h"
#include "RtraceSimulManager.h"
#include "color.h"
#include "func.h"
#include "otspecial.h"
#include "otypes.h"
#include "platform.h"
#include "ray.h"
#include "resolu.h"
#include "source.h"
#include "view.h"

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

namespace nb = nanobind;

using OrigDirec = nb::ndarray<double, nb::shape<-1, 3>>;
using Array3 = nb::ndarray<float, nb::numpy, nb::shape<3>, nb::c_contig>;

VIEW ourview = STDVIEW; /* view parameters */
int hres, vres;         /* current image resolution for srcdraw.c */

int psample = 4;       /* pixel sample size */
double maxdiff = .05;  /* max. difference for interpolation */
double dstrpix = 0.67; /* square pixel distribution */

double mblur = 0.; /* motion blur parameter */

double dblur = 0.; /* depth-of-field blur parameter */

static std::unordered_map<void *, std::shared_ptr<nb::callable>>
    stored_callbacks;

int callback_wrapper(RAY *r, void *cd) {
  auto it = stored_callbacks.find(cd);
  if (it == stored_callbacks.end())
    return -1;

  nb::gil_scoped_acquire acquire;
  try {
    nb::object result = (*(it->second))(nb::cast(r), nb::cast(cd));
    return nb::cast<int>(result);
  } catch (const std::exception &e) {
    return -1;
  }
}

static std::shared_ptr<nb::callable> stored_cdsf_callback;

RdataShare *python_cdsf_wrapper(const char *name, RCOutputOp op, size_t siz) {
  if (!stored_cdsf_callback) {
    return defDataShare(name, op, siz); // fallback to default
  }

  nb::gil_scoped_acquire acquire;
  try {
    nb::object result =
        (*stored_cdsf_callback)(nb::cast(name), nb::cast(op), nb::cast(siz));
    return nb::cast<RdataShare *>(result);
  } catch (const std::exception &e) {
    error(SYSTEM, e.what());
    return nullptr;
  }
}

void ndarray_to_fvect(const OrigDirec &arr, FVECT *output) {
  for (size_t i = 0; i < arr.shape(0); ++i) {
    output[i][0] = arr(i, 0);
    output[i][1] = arr(i, 1);
    output[i][2] = arr(i, 2);
  }
}

extern char *progname;

// Function to append an item to amblist
void append_amblist(const nb::str &value) {
  for (int i = 0; i < 256; ++i) {
    if (amblist[i] == nullptr) {
      amblist[i] = strdup(value.c_str());
      return;
    }
  }
  throw nb::value_error("Amblist is full");
}

// Template for get and set operations
template <typename T>
void define_get_set(nb::module_ &m, const char *name, T &var) {
  std::string get_name = "get_" + std::string(name);
  std::string set_name = "set_" + std::string(name);
  m.def(get_name.c_str(), [&var]() { return var; });
  m.def(set_name.c_str(), [&var](T v) { var = v; });
}

NB_MODULE(radiance_ext, m) {

  m.doc() = "Radiance extension";

  define_get_set<int>(m, "u", rand_samp);

  define_get_set<int>(m, "bv", backvis);

  define_get_set<double>(m, "dt", shadthresh);
  define_get_set<double>(m, "dc", shadcert);
  define_get_set<double>(m, "dj", dstrsrc);
  define_get_set<int>(m, "dr", directrelay);
  define_get_set<int>(m, "dp", vspretest);
  define_get_set<int>(m, "dv", directvis);
  define_get_set<double>(m, "ds", srcsizerat);

  define_get_set<double>(m, "st", specthresh);
  define_get_set<double>(m, "ss", specjitter);

  define_get_set<int>(m, "lr", maxdepth);
  define_get_set<double>(m, "lw", minweight);

  define_get_set<int>(m, "aw", ambvwt);
  define_get_set<double>(m, "aa", ambacc);
  define_get_set<int>(m, "ar", ambres);
  define_get_set<int>(m, "ad", ambdiv);
  define_get_set<int>(m, "as", ambssamp);
  define_get_set<int>(m, "ab", ambounce);
  define_get_set<int>(m, "ai", ambincl);

  m.def("get_av",
        []() { return nb::make_tuple(ambval[0], ambval[1], ambval[2]); });
  m.def("set_av", [](double v1, double v2, double v3) {
    ambval[0] = v1;
    ambval[1] = v2, ambval[2] = v3;
  });

  m.def("get_amblist", []() {
    nb::list result;
    for (int i = 0; i < AMBLLEN + 1; i++) {
      if (amblist[i] != nullptr) {
        result.append(amblist[i]);
      } else {
        break;
      }
    }
    return result;
  });

  m.def("append_amblist", &append_amblist);
  m.def("extend_amblist", [](const nb::list &values) {
    for (const auto &value : values) {
      append_amblist(nb::cast<nb::str>(value));
    }
  });

  m.def("remove_last_amblist", []() {
    int last_index = -1;
    for (int i = AMBLLEN; i >= 0; --i) {
      if (amblist[i] != nullptr) {
        last_index = i;
        break;
      }
    }
    if (last_index == -1) {
      throw nb::value_error("Amblist is empty");
    }
    free(amblist[last_index]);
    amblist[last_index] = nullptr;
  });

  m.def("clear_amblist", []() {
    for (int i = 0; i < AMBLLEN + 1; ++i) {
      if (amblist[i] != nullptr) {
        free(amblist[i]);
        amblist[i] = nullptr;
      }
    }
  });

  nb::class_<RAY>(m, "RAY")
      .def(nb::init<>())
      .def_prop_ro("rorg",
                   [](const RAY &r) -> nb::tuple {
                     return nb::make_tuple(r.rorg[0], r.rorg[1], r.rorg[2]);
                   })
      .def_prop_ro("rdir",
                   [](const RAY &r) -> nb::tuple {
                     return nb::make_tuple(r.rdir[0], r.rdir[1], r.rdir[2]);
                   })
      .def_prop_ro("rop",
                   [](const RAY &r) -> nb::tuple {
                     return nb::make_tuple(r.rop[0], r.rop[1], r.rop[2]);
                   })
      .def_prop_ro("ron",
                   [](const RAY &r) -> nb::tuple {
                     return nb::make_tuple(r.ron[0], r.ron[1], r.ron[2]);
                   })
      .def_prop_ro("pert",
                   [](const RAY &r) -> nb::tuple {
                     return nb::make_tuple(r.pert[0], r.pert[1], r.pert[2]);
                   })
      .def_prop_ro("rmax", [](const RAY &r) { return r.rmax; })
      .def_prop_ro("rod", [](const RAY &r) { return r.rod; })
      .def_prop_ro("rweight", [](const RAY &r) { return r.rweight; })
      .def_prop_ro("rno", [](const RAY &r) { return r.rno; })
      .def_prop_ro("rtype", [](const RAY &r) { return r.rtype; })
      .def_prop_ro("mcol",
                   [](const RAY &r) -> nb::tuple {
                     return nb::make_tuple(r.mcol[0], r.mcol[1], r.mcol[2]);
                   })
      .def_prop_ro("rcol", [](const RAY &r) -> nb::tuple {
        return nb::make_tuple(r.rcol[0], r.rcol[1], r.rcol[2]);
      });

  nb::class_<VIEW>(m, "VIEW")
      .def_prop_rw(
          "type", [](VIEW &v) { return (char)v.type; },
          [](VIEW &v, const char t) { v.type = (int)t; })
      .def_prop_rw(
          "vp",
          [](VIEW &v) { return nb::make_tuple(v.vp[0], v.vp[1], v.vp[2]); },
          [](VIEW &v, double x, double y, double z) {
            v.vp[0] = x;
            v.vp[1] = y;
            v.vp[2] = z;
          })
      .def_prop_rw(
          "vdir",
          [](VIEW &v) {
            return nb::make_tuple(v.vdir[0], v.vdir[1], v.vdir[2]);
          },
          [](VIEW &v, double x, double y, double z) {
            v.vdir[0] = x;
            v.vdir[1] = y;
            v.vdir[2] = z;
          })
      .def_prop_rw(
          "vu",
          [](VIEW &v) { return nb::make_tuple(v.vup[0], v.vup[1], v.vup[2]); },
          [](VIEW &v, double x, double y, double z) {
            v.vup[0] = x;
            v.vup[1] = y;
            v.vup[2] = z;
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
          [](VIEW &v, double x, double y, double z) {
            v.hvec[0] = x;
            v.hvec[1] = y;
            v.hvec[2] = z;
          })
      .def_prop_rw(
          "vvec",
          [](VIEW &v) {
            return nb::make_tuple(v.vvec[0], v.vvec[1], v.vvec[2]);
          },
          [](VIEW &v, double x, double y, double z) {
            v.vvec[0] = x;
            v.vvec[1] = y;
            v.vvec[2] = z;
          })
      .def_rw("hn2", &VIEW::hn2)  /* DOT(hvec,hvec) */
      .def_rw("vn2", &VIEW::vn2); /* DOT(vvec,vvec) */

  nb::class_<RESOLU>(m, "RESOLU")
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

  m.def("set_render_option", [](std::vector<std::string> opts) {
    int ac = opts.size();
    char **av = new char *[ac];
    int rval = 0;

    for (size_t i = 0; i < ac; i++) {
      av[i] = new char[opts[i].length() + 1];
      strcpy(av[i], opts[i].c_str());
    }
    for (size_t i = 0; i < ac; i++) {
      rval = getrenderopt(ac - i, av + i);
      if (rval >= 0) {
        i += rval;
        continue;
      }
    }
    return;
  });

  m.def(
      "setspectrsamp",
      [](const std::vector<int> &cn, const std::vector<float> &wlpt) -> int {
        int cn_array[4] = {0};
        float wlpt_array[4] = {0};

        for (int i = 0; i < 4; ++i) {
          cn_array[i] = cn[i];
          wlpt_array[i] = wlpt[i];
        }

        return setspectrsamp(cn_array, wlpt_array);
      },
      nb::arg("cn"), nb::arg("wlpt"),
      "Assign spectral sampling, returns 1 if good, -1 if bad.");

  nb::class_<RtraceSimulManager>(m, "RtraceSimulManager")
      .def(nb::init<>())
      .def("load_octree", &RtraceSimulManager::LoadOctree)
      .def("set_thread_count", &RtraceSimulManager::SetThreadCount,
           nb::arg("nt") = 0)
      .def(
          "enqueue_bundle_list",
          [](RtraceSimulManager &self, const nb::list &orig_direc,
             RNUMBER rID0 = 0) {
            size_t list_count = len(orig_direc);
            size_t nrays = list_count / 2;
            FVECT *output = (FVECT *)emalloc(sizeof(FVECT) * list_count);
            for (size_t i = 0; i < list_count; ++i) {
              output[i][0] = nb::cast<double>(nb::list(orig_direc[i])[0]);
              output[i][1] = nb::cast<double>(nb::list(orig_direc[i])[1]);
              output[i][2] = nb::cast<double>(nb::list(orig_direc[i])[2]);
            }
            int ok = self.EnqueueBundle(output, nrays, rID0);
            free(output);
            return ok;
          },
          nb::arg("orig_direc"), nb::arg("rID0") = 0)
      .def(
          "enqueue_bundle",
          [](RtraceSimulManager &self, const OrigDirec &orig_direc,
             RNUMBER rID0 = 0) {
            FVECT *output =
                (FVECT *)emalloc(sizeof(FVECT) * orig_direc.shape(0));
            ndarray_to_fvect(orig_direc, output);
            int n = orig_direc.shape(0) / 2;
            int ok = self.EnqueueBundle(output, n, rID0);
            free(output);
            return ok;
          },
          nb::arg("orig_direc"), nb::arg("rID0") = 0)
      .def("ready", &RtraceSimulManager::Ready)
      .def("flush_queue", &RtraceSimulManager::FlushQueue)
      .def("cleanup", &RtraceSimulManager::Cleanup,
           nb::arg("everything") = false)
      .def_rw("rt_flags", &RtraceSimulManager::rtFlags)
      .def("set_cooked_call",
           [](RtraceSimulManager &self, nb::callable callback) {
             auto cb_ptr = std::make_shared<nb::callable>(std::move(callback));
             void *key = cb_ptr.get();
             stored_callbacks[key] = cb_ptr;

             self.SetCookedCall(callback_wrapper, key);
           })
      .def("set_trace_call",
           [](RtraceSimulManager &self, nb::callable callback) {
             auto cb_ptr = std::make_shared<nb::callable>(std::move(callback));
             void *key = cb_ptr.get();
             stored_callbacks[key] = cb_ptr;

             self.SetTraceCall(callback_wrapper, key);
           })
      .def_rw("rt_flags", &RtraceSimulManager::rtFlags)
      .def("cleanup_callbacks", [](RtraceSimulManager &self) {
        stored_callbacks.clear();
        self.SetCookedCall(nullptr, nullptr);
        self.SetTraceCall(nullptr, nullptr);
      });

  m.attr("RTdoFIFO") = (int)RTdoFIFO;
  m.attr("RTtraceSources") = (int)RTtraceSources;
  m.attr("RTlimDist") = (int)RTlimDist;
  m.attr("RTimmIrrad") = (int)RTimmIrrad;
  m.attr("RTmask") = (int)RTmask;

  m.attr("RCcontrib") = (int)RTmask + 1;

  nb::enum_<RCOutputOp>(m, "RcOutputOp")
      .value("NEW", RCOnew)
      .value("FORCE", RCOforce)
      .value("RECOVER", RCOrecover);

  nb::class_<RcontribOutput>(m, "RcontribOutput")
      .def(nb::init<const char *>(), nb::arg("fnm") = nullptr)
      .def("get_name", &RcontribOutput::GetName)
      .def("set_rows_done", &RcontribOutput::SetRowsDone)
      .def("get_row", &RcontribOutput::GetRow)
      .def("insertion_p", &RcontribOutput::InsertionP)
      .def("done_row", &RcontribOutput::DoneRow)
      .def("next",
           static_cast<const RcontribOutput *(RcontribOutput::*)() const>(
               &RcontribOutput::Next))
      .def("next", static_cast<RcontribOutput *(RcontribOutput::*)()>(
                       &RcontribOutput::Next))
      .def_ro("r_data", &RcontribOutput::rData)
      .def_ro("row_bytes", &RcontribOutput::rowBytes)
      .def_ro("omod", &RcontribOutput::omod)
      .def_ro("obin", &RcontribOutput::obin)
      .def_ro("beg_data", &RcontribOutput::begData)
      .def_ro("cur_row", &RcontribOutput::curRow)
      .def_ro("n_rows", &RcontribOutput::nRows);

  m.attr("RDSexcl") = (int)RDSexcl;
  m.attr("RDSextend") = (int)RDSextend;
  m.attr("RDSread") = (int)RDSread;
  m.attr("RDSwrite") = (int)RDSwrite;

  nb::enum_<RDSType>(m, "RDSType")
      .value("RDSTanonMap", RDSTanonMap)
      .value("RDSTfileMap", RDSTfileMap)
      .value("RDSTfile", RDSTfile)
      .value("RDSTcust1", RDSTcust1)
      .value("RDSTcust2", RDSTcust2)
      .value("RDSTcust3", RDSTcust3)
      .value("RDSTcust4", RDSTcust4);

  nb::class_<RdataShare>(m, "RdataShare")
      .def("get_name", &RdataShare::GetName)
      .def("get_mode", &RdataShare::GetMode)
      .def("get_size", &RdataShare::GetSize)
      .def("get_type", &RdataShare::GetType)
      .def("resize", &RdataShare::Resize)
      .def("get_memory",
           [](RdataShare &self, size_t offs, size_t len, int fl) {
             void *data = self.GetMemory(offs, len, fl);
             return nb::bytes(static_cast<char *>(data), len);
           })
      .def("release_memory", &RdataShare::ReleaseMemory);

  // Bind default data share function
  m.def("default_data_share", &defDataShare,
        "Default implementation of data share creation", nb::arg("name"),
        nb::arg("op"), nb::arg("siz"));

  nb::class_<RcontribSimulManager>(m, "RcontribSimulManager")
      .def(nb::init<>())
      .def(nb::init<const char *>(), nb::arg("octn") = nullptr)
      .def("has_flag", &RcontribSimulManager::HasFlag)
      .def("set_flag", &RcontribSimulManager::SetFlag, nb::arg("fl"),
           nb::arg("val") = true)
      .def("load_octree", &RcontribSimulManager::LoadOctree)
      .def("new_header", &RcontribSimulManager::NewHeader,
           nb::arg("inspec") = nullptr)
      .def("add_header",
           nb::overload_cast<const char *>(&RcontribSimulManager::AddHeader))
      .def("get_head_len", &RcontribSimulManager::GetHeadLen)
      .def("get_head_str",
           nb::overload_cast<>(&RcontribSimulManager::GetHeadStr, nb::const_))
      .def("get_head_str",
           nb::overload_cast<const char *, bool>(
               &RcontribSimulManager::GetHeadStr, nb::const_),
           nb::arg("key"), nb::arg("inOK") = false)
      .def("set_data_format", &RcontribSimulManager::SetDataFormat)
      .def("get_format", &RcontribSimulManager::GetFormat,
           nb::arg("siz") = nullptr)
      .def(
          "add_modifier",
          [](RcontribSimulManager &self, const std::string &modn,
             const std::string &outspec, const std::string &prms = "",
             const std::string &binval = "", int bincnt = 1) {
            return self.AddModifier(modn.c_str(), outspec.c_str(),
                                    prms.empty() ? nullptr : prms.c_str(),
                                    binval.empty() ? nullptr : binval.c_str(),
                                    bincnt);
          },
          nb::arg("modn"), nb::arg("outspec"), nb::arg("prms") = "",
          nb::arg("binval") = "", nb::arg("bincnt") = 1,
          "Add a modifier to the simulation manager")
      .def("add_mod_file", &RcontribSimulManager::AddModFile, nb::arg("modfn"),
           nb::arg("outspec"), nb::arg("prms") = nullptr,
           nb::arg("binval") = nullptr, nb::arg("bincnt") = 1)
      .def(
          "get_output",
          [](RcontribSimulManager &self,
             nb::object nm = nb::none()) -> const RcontribOutput * {
            if (nm.is_none()) {
              return self.GetOutput(nullptr);
            }
            static std::string name = nb::cast<std::string>(nm);
            return self.GetOutput(name.c_str());
          },
          nb::arg("nm") = nb::none(), nb::rv_policy::reference_internal)
      .def(
          "get_output_array",
          [](RcontribSimulManager &self, nb::object nm = nb::none()) {
            const RcontribOutput *out;
            if (nm.is_none()) {
              out = self.GetOutput(nullptr);
            } else {
              static std::string name = nb::cast<std::string>(nm);
              out = self.GetOutput(name.c_str());
            }

            void *data = out->rData->GetMemory(
                out->begData, out->rowBytes * out->nRows, RDSread);
            return nb::ndarray<nb::numpy, float, nb::ndim<2>>(
                data, {out->nRows, out->rowBytes / sizeof(float)});
          },
          nb::arg("nm") = nb::none(), nb::rv_policy::reference_internal)
      .def("prep_output", &RcontribSimulManager::PrepOutput)
      .def("ready", &RcontribSimulManager::Ready)
      .def("set_thread_count", &RcontribSimulManager::SetThreadCount,
           nb::arg("nt") = 0)
      .def("n_threads", &RcontribSimulManager::NThreads)
      .def("get_row_max", &RcontribSimulManager::GetRowMax)
      .def("get_row_count", &RcontribSimulManager::GetRowCount)
      .def("get_row_finished", &RcontribSimulManager::GetRowFinished)
      .def(
          "compute_record",
          [](RcontribSimulManager &self, const OrigDirec &rays) {
            FVECT *output = (FVECT *)emalloc(sizeof(FVECT) * rays.shape(0));
            ndarray_to_fvect(rays, output);
            for (int i = 0; i < rays.shape(0); i++) {
              printf("%f %f %f\n", output[i][0], output[i][1], output[i][2]);
            }
            return self.ComputeRecord(output);
          },
          nb::arg("orig_direc"))
      .def("flush_queue", &RcontribSimulManager::FlushQueue)
      .def("reset_row", &RcontribSimulManager::ResetRow)
      .def("clear_modifiers", &RcontribSimulManager::ClearModifiers)
      .def("cleanup", &RcontribSimulManager::Cleanup,
           nb::arg("everything") = false)
      .def(
          "rcontrib",
          [](RcontribSimulManager &self, const OrigDirec &rays) {
            const int totRows = self.GetRowMax();
            const int n2go = self.accum;
            FVECT *odarr = (FVECT *)emalloc(sizeof(FVECT) * 2 * self.accum);
            int r = 0;
            int ri, ri1 = 0;
            int ni, ni1 = 0;

            while (r < totRows) {
              ri = r * 2;
              ri1 = ri + 1;
              for (int i = 0; i < n2go; i++) {
                ni = i * 2;
                ni1 = ni + 1;
                odarr[ni][0] = rays(ri, 0);
                odarr[ni][1] = rays(ri, 1);
                odarr[ni][2] = rays(ri, 2);
                odarr[ni1][0] = rays(ri1, 0);
                odarr[ni1][1] = rays(ri1, 1);
                odarr[ni1][2] = rays(ri1, 2);
              }
              if (self.ComputeRecord(odarr) <= 0)
                return; // error reported, hopefully...
              r++;
              if (r == totRows)
                self.FlushQueue();
            }
            efree(odarr);
            return;
          },
          nb::arg("rays"))
      .def_rw("out_op", &RcontribSimulManager::outOp)
      .def_prop_rw(
          "cds_f",
          [](RcontribSimulManager &self) -> nb::object {
            return nb::cpp_function([func = self.cdsF](const char *name,
                                                       RCOutputOp op,
                                                       size_t size) {
              return func(name, op, size);
            });
          },
          [](RcontribSimulManager &self, RcreateDataShareF *func) {
            self.cdsF = func;
          })
      .def_rw("xres", &RcontribSimulManager::xres)
      .def_rw("yres", &RcontribSimulManager::yres)
      .def_rw("accum", &RcontribSimulManager::accum)
      .def("__enter__", [](RcontribSimulManager &self) { return &self; })
      .def(
          "__exit__",
          [](RcontribSimulManager &self, nb::object type, nb::object value,
             nb::object tb) -> bool {
            self.Cleanup(true);
            return false; // don't suppress exceptions
          },
          nb::arg("type") = nb::none(), nb::arg("value") = nb::none(),
          nb::arg("traceback") = nb::none());

  nb::enum_<RenderDataType>(m, "RenderDataType")
      .value("RDTnone", RDTnone)
      .value("RDTscolor", RDTscolor)
      .value("RDTrgb", RDTrgb)
      .value("RDTxyz", RDTxyz)
      .value("RDTscolr", RDTscolr)
      .value("RDTrgbe", RDTrgbe)
      .value("RDTxyze", RDTxyze)
      .value("RDTcolorM", RDTcolorM)
      .value("RDTdfloat", RDTdfloat)
      .value("RDTdshort", RDTdshort)
      .value("RDTdepthM", RDTdepthM);

  nb::class_<PixelAccess>(m, "PixelAccess")
      .def(nb::init<>())
      .def(nb::init<COLORV *, int, float *>(), nb::arg("rp"),
           nb::arg("ystride"), nb::arg("zp") = nullptr)
      .def(nb::init<COLRV *, int, float *>(), nb::arg("bp"), nb::arg("ystride"),
           nb::arg("zp") = nullptr)
      .def(nb::init<COLRV *, int, short *>(), nb::arg("bp"), nb::arg("ystride"),
           nb::arg("dp"))
      .def(nb::init<COLORV *, int, short *>(), nb::arg("rp"),
           nb::arg("ystride"), nb::arg("dp"))
      .def("init",
           nb::overload_cast<COLORV *, int, float *>(&PixelAccess::Init))
      .def("init", nb::overload_cast<COLRV *, int, float *>(&PixelAccess::Init))
      .def("init", nb::overload_cast<COLRV *, int, short *>(&PixelAccess::Init))
      .def("init",
           nb::overload_cast<COLORV *, int, short *>(&PixelAccess::Init))
      /*.def("set_color_space",*/
      /*     [](PixelAccess &self, RenderDataType cs, nb::object pr) {*/
      /*       if (pr.is_none()) {*/
      /*         return self.SetColorSpace(cs, NULL);*/
      /*       }*/
      /*       RGBPRIMP pr2 = nb::cast<RGBPRIMP>(pr);*/
      /*       return self.SetColorSpace(cs, pr2);*/
      /*     })*/
      .def("color_space", &PixelAccess::ColorSpace)
      /*.def(*/
      /*    "primaries",*/
      /*    [](PixelAccess &self) {*/
      /*      RGBPRIMP result = self.Primaries();*/
      /*      return nb::ndarray<nb::numpy, float, nb::shape<2>>(result);*/
      /*    },*/
      /*    nb::rv_policy::reference_internal)*/
      .def("nc", &PixelAccess::NC)
      .def("depth_type", &PixelAccess::DepthType)
      .def("get_row_stride", &PixelAccess::GetRowStride)
      .def("set_pixel",
           nb::overload_cast<int, int, const RAY *>(&PixelAccess::SetPixel))
      .def("set_pixel", nb::overload_cast<int, int, const COLORV *, float>(
                            &PixelAccess::SetPixel))
      .def("get_pixel", &PixelAccess::GetPixel)
      .def("copy_pixel", &PixelAccess::CopyPixel);

  nb::class_<RpictSimulManager>(m, "RpictSimulManager")
      .def(nb::init<>())
      .def(nb::init<const char *>(), nb::arg("octn") = nullptr)
      .def("load_octree", &RpictSimulManager::LoadOctree)
      .def("new_header", &RpictSimulManager::NewHeader,
           nb::arg("inspec") = nullptr)
      .def("add_header",
           nb::overload_cast<const char *>(&RpictSimulManager::AddHeader))
      .def("get_head_len", &RpictSimulManager::GetHeadLen)
      .def("get_head_str",
           nb::overload_cast<>(&RpictSimulManager::GetHeadStr, nb::const_))
      .def("get_head_str",
           nb::overload_cast<const char *, bool>(&RpictSimulManager::GetHeadStr,
                                                 nb::const_),
           nb::arg("key"), nb::arg("inOK") = false)
      .def("ready", &RpictSimulManager::Ready)
      .def("pre_view", &RpictSimulManager::PreView)
      .def("get_width", &RpictSimulManager::GetWidth)
      .def("get_height", &RpictSimulManager::GetHeight)
      .def("t_width", &RpictSimulManager::TWidth)
      .def("t_height", &RpictSimulManager::THeight)
      .def("render_tile",
           nb::overload_cast<COLORV *, int, float *, const int *>(
               &RpictSimulManager::RenderTile))
      .def("render_tile", nb::overload_cast<COLRV *, int, float *, const int *>(
                              &RpictSimulManager::RenderTile))
      .def("render_tile", nb::overload_cast<COLRV *, int, short *, const int *>(
                              &RpictSimulManager::RenderTile))
      .def("render_tile",
           nb::overload_cast<COLORV *, int, short *, const int *>(
               &RpictSimulManager::RenderTile))
      .def("render_frame", &RpictSimulManager::RenderFrame)
      .def("resume_frame", &RpictSimulManager::RenderFrame)
      .def("set_thread_count", &RpictSimulManager::SetThreadCount,
           nb::arg("nt") = 0)
      .def("set_reference_depth",
           nb::overload_cast<const char *>(
               &RpictSimulManager::SetReferenceDepth),
           nb::arg("dstr") = 0)
      .def("set_reference_depth",
           nb::overload_cast<double, const char *>(
               &RpictSimulManager::SetReferenceDepth),
           nb::arg("dref"), nb::arg("unit") = nullptr)
      .def("get_reference_depth",
           [](RpictSimulManager &self, const char *du) {
             return self.GetReferenceDepth(const_cast<char *>(du));
           })
      .def("new_frame",
           [](RpictSimulManager &self, const VIEW &v, int xydim[2], double *ap,
              const int *tgrid) { return self.NewFrame(v, xydim, ap, tgrid); })
      .def("n_threads", &RpictSimulManager::NThreads);

  m.def("initfunc", &initfunc);
  m.def("loadfunc", &loadfunc);
  m.def("eval",
        [](const char *expr) { return eval(const_cast<char *>(expr)); });
  m.def("set_eparams", &set_eparams);
  m.def("calcontext",
        [](const char *cxt) { return calcontext(const_cast<char *>(cxt)); });

  m.attr("RCCONTEXT") = nb::str(RCCONTEXT);
  m.def(
      "cie_rgb",
      [](const Array3 xyz) {
        float rgb[3] = {0, 0, 0};
        float xyz2[3] = {xyz(0), xyz(1), xyz(2)};
        cie_rgb(rgb, xyz2);
        return Array3(rgb);
      },
      "Convert CIE color to standard RGB");
}
