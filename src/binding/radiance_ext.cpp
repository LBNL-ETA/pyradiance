#include <climits>
#include <cstring>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

#include "RcontribSimulManager.h"
#include "RdataShare.h"
#include "RpictSimulManager.h"
#include "RtraceSimulManager.h"
#include "color.h"
#define freefunc radiance_freefunc
#include "func.h"
#undef freefunc
#include "ray.h"
#include "resolu.h"
#include "view.h"


namespace nb = nanobind;

using OrigDirec = nb::ndarray<double, nb::shape<-1, 3>, nb::device::cpu>;
using Array3 = nb::ndarray<float, nb::numpy, nb::shape<3>, nb::c_contig>;

VIEW ourview = STDVIEW; /* view parameters */
int hres, vres;         /* current image resolution for srcdraw.c */

int psample = 4;       /* pixel sample size */
double maxdiff = .05;  /* max. difference for interpolation */
double dstrpix = 0.67; /* square pixel distribution */

double mblur = 0.; /* motion blur parameter */

double dblur = 0.; /* depth-of-field blur parameter */

// ray_restore() keeps pointers into the struct it is given (ambfile, amblist),
// so the active parameters must outlive any Python RayParams object.
static RAYPARAMS current_params;

template <typename T>
nb::ndarray<nb::numpy, T> owned_array(T *buf, std::initializer_list<size_t> shape) {
  nb::capsule owner(buf, [](void *p) noexcept { delete[] (T *)p; });
  return nb::ndarray<nb::numpy, T>(buf, shape.size(), shape.begin(), owner);
}

struct PyCallback {
  nb::object fn;
  nb::object data;
};

// Calls a Python ray callback. If it raises, the exception is left set and
// later callbacks are skipped; raise_if_error() re-raises it once control
// returns to Python. Returning -1 instead would make Radiance abort the
// process when the ray queue cannot be emptied.
int callback_wrapper(RAY *r, void *cd) {
  nb::gil_scoped_acquire acquire;
  if (PyErr_Occurred())
    return 0;
  auto *cb = static_cast<PyCallback *>(cd);
  try {
    nb::object result = cb->fn(nb::cast(*r, nb::rv_policy::copy), cb->data);
    if (result.is_none())
      return 0;
    return nb::cast<int>(result);
  } catch (nb::python_error &e) {
    e.restore();
  } catch (const std::exception &e) {
    PyErr_SetString(PyExc_RuntimeError, e.what());
  }
  return 0;
}

void raise_if_error() {
  if (PyErr_Occurred())
    throw nb::python_error();
}

// Validate an (2N, 3) origin/direction array and copy it into FVECTs
std::unique_ptr<FVECT[]> to_fvect(const OrigDirec &arr, size_t &nrays) {
  size_t nrows = arr.shape(0);
  if (nrows % 2)
    throw nb::value_error(
        "rays must have an even number of rows (origin, direction pairs)");
  if (nrows / 2 > INT_MAX)
    throw nb::value_error("too many rays");
  nrays = nrows / 2;
  std::unique_ptr<FVECT[]> out(new FVECT[nrows]);
  for (size_t i = 0; i < nrows; ++i) {
    out[i][0] = arr(i, 0);
    out[i][1] = arr(i, 1);
    out[i][2] = arr(i, 2);
  }
  return out;
}

nb::tuple scolor_tuple(const COLORV *c) {
  nb::list values;
  for (int i = 0; i < NCSAMP; i++)
    values.append(c[i]);
  return nb::tuple(values);
}

/// RtraceSimulManager that owns its Python callbacks
class PyRtraceSimulManager : public RtraceSimulManager {
public:
  std::unique_ptr<PyCallback> cooked, traced;
  ~PyRtraceSimulManager() {
    SetCookedCall(NULL);
    SetTraceCall(NULL);
    if (PyErr_Occurred())
      PyErr_WriteUnraisable(Py_None);
  }
  void SetPyCookedCall(nb::object fn, nb::object data) {
    std::unique_ptr<PyCallback> cb;
    if (!fn.is_none())
      cb.reset(new PyCallback{fn, data});
    // old callback must stay alive while SetCookedCall() flushes the queue
    SetCookedCall(cb ? callback_wrapper : NULL, cb.get());
    cooked = std::move(cb);
  }
  void SetPyTraceCall(nb::object fn, nb::object data) {
    std::unique_ptr<PyCallback> cb;
    if (!fn.is_none())
      cb.reset(new PyCallback{fn, data});
    SetTraceCall(cb ? callback_wrapper : NULL, cb.get());
    traced = std::move(cb);
  }
  void RestoreCookedCall() {
    SetCookedCall(cooked ? callback_wrapper : NULL, cooked.get());
  }
};

struct RayCollector {
  float *out;
  size_t nrays;
  int nc;
};

// Store a ray result by ray number (assigned from 1 in trace())
int collect_ray(RAY *r, void *cd) {
  auto *col = static_cast<RayCollector *>(cd);
  if (r->rno < 1 || r->rno > col->nrays)
    return 0;
  float *dst = col->out + (size_t)(r->rno - 1) * col->nc;
  for (int i = 0; i < col->nc; i++)
    dst[i] = r->rcol[i];
  return 1;
}

const char *data_share_name(RcreateDataShareF *f) {
  if (f == &mapDataShare)
    return "map";
  if (f == &fileDataShare)
    return "file";
  return "custom";
}

NB_MODULE(radiance_ext, m) {

  m.doc() = "Radiance extension";

  nb::class_<RAY>(m, "Ray")
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
      .def_prop_ro("uv",
                   [](const RAY &r) -> nb::tuple {
                     return nb::make_tuple(r.uv[0], r.uv[1]);
                   })
      .def_prop_ro("rmax", [](const RAY &r) { return r.rmax; })
      .def_prop_ro("rot", [](const RAY &r) { return r.rot; },
                   "distance to intersected object")
      .def_prop_ro("rmt", [](const RAY &r) { return r.rmt; },
                   "returned mirrored ray length")
      .def_prop_ro("rxt", [](const RAY &r) { return r.rxt; },
                   "returned unmirrored ray length")
      .def_prop_ro("rod", [](const RAY &r) { return r.rod; })
      .def_prop_ro("rweight", [](const RAY &r) { return r.rweight; })
      .def_prop_ro("rno", [](const RAY &r) { return r.rno; })
      .def_prop_ro("robj", [](const RAY &r) { return (long)r.robj; },
                   "intersected object number (-1 if none)")
      .def_prop_ro("rsrc", [](const RAY &r) { return r.rsrc; })
      .def_prop_ro("rlvl", [](const RAY &r) { return r.rlvl; },
                   "number of reflections for this ray")
      .def_prop_ro("rtype", [](const RAY &r) { return r.rtype; })
      .def_prop_ro("crtype", [](const RAY &r) { return r.crtype; },
                   "cumulative ray type")
      .def_prop_ro("mcol", [](const RAY &r) { return scolor_tuple(r.mcol); },
                   "mirrored color contribution (NCSAMP values)")
      .def_prop_ro("rcol", [](const RAY &r) { return scolor_tuple(r.rcol); },
                   "returned radiance value (NCSAMP values)");

  m.def("get_ray_params", []() {
    RAYPARAMS rp;
    ray_save(&rp);
    return rp;
  });

  m.def(
      "set_ray_params",
      [](const RAYPARAMS *rp) {
        if (rp == nullptr)
          ray_defaults(&current_params);
        else
          current_params = *rp;
        ray_restore(&current_params);
      },
      nb::arg("rp") = nb::none(),
      "Apply ray parameters, or restore defaults if None.");

  m.def("ray_done", &ray_done);

  m.def(
      "set_option",
      [](const std::vector<std::string> &opts) {
        std::vector<std::vector<char>> bufs;
        std::vector<char *> av;
        for (const std::string &s : opts) {
          bufs.emplace_back(s.begin(), s.end());
          bufs.back().push_back('\0');
        }
        for (auto &b : bufs)
          av.push_back(b.data());
        av.push_back(nullptr);
        const int ac = (int)opts.size();
        for (int i = 0; i < ac; i++) {
          int rval = getrenderopt(ac - i, av.data() + i);
          if (rval < 0)
            throw nb::value_error(
                ("bad or unknown render option: " + opts[i]).c_str());
          i += rval;
        }
      },
      nb::arg("opts"),
      "Set rendering options from command line style arguments.");

  m.def(
      "setspectrsamp",
      [](const std::vector<int> &cn, const std::vector<float> &wlpt) -> int {
        if (cn.size() != 4 || wlpt.size() != 4)
          throw nb::value_error("cn and wlpt must each have 4 values");
        int cn_array[4];
        float wlpt_array[4];

        for (int i = 0; i < 4; ++i) {
          cn_array[i] = cn[i];
          wlpt_array[i] = wlpt[i];
        }

        return setspectrsamp(cn_array, wlpt_array);
      },
      nb::arg("cn"), nb::arg("wlpt"),
      "Assign spectral sampling, returns 1 if good, -1 if bad.");

  nb::class_<PyRtraceSimulManager>(m, "RtraceSimulManager")
      .def(nb::init<>())
      .def("load_octree", &PyRtraceSimulManager::LoadOctree)
      .def(
          "set_thread_count",
          [](PyRtraceSimulManager &self, int nt) {
            int n = self.SetThreadCount(nt);
            raise_if_error();
            return n;
          },
          nb::arg("nt") = 0)
      .def("n_threads", &PyRtraceSimulManager::NThreads)
      .def(
          "enqueue_bundle",
          [](PyRtraceSimulManager &self, const OrigDirec &orig_direc,
             RNUMBER rID0) {
            if (!self.Ready())
              throw std::runtime_error("octree not loaded");
            if (rID0 && (self.rtFlags & RTdoFIFO))
              throw nb::value_error(
                  "ray number assignment unsupported with RTdoFIFO");
            size_t nrays;
            auto od = to_fvect(orig_direc, nrays);
            int ok;
            {
              nb::gil_scoped_release release;
              ok = self.EnqueueBundle(od.get(), (int)nrays, rID0);
            }
            raise_if_error();
            return ok;
          },
          nb::arg("orig_direc"), nb::arg("rID0") = 0,
          "Queue rays given as (2N, 3) origin/direction rows; returns the "
          "number queued, or -1 on failure")
      .def(
          "enqueue_ray",
          [](PyRtraceSimulManager &self, const std::vector<double> &org,
             const std::vector<double> &dir, RNUMBER rID) {
            if (org.size() != 3 || dir.size() != 3)
              throw nb::value_error("org and dir must each have 3 values");
            if (!self.Ready())
              throw std::runtime_error("octree not loaded");
            if (rID && (self.rtFlags & RTdoFIFO))
              throw nb::value_error(
                  "ray number assignment unsupported with RTdoFIFO");
            FVECT o = {org[0], org[1], org[2]};
            FVECT d = {dir[0], dir[1], dir[2]};
            int ok;
            {
              nb::gil_scoped_release release;
              ok = self.EnqueueRay(o, d, rID);
            }
            raise_if_error();
            return ok;
          },
          nb::arg("org"), nb::arg("dir"), nb::arg("rID") = 0)
      .def(
          "trace",
          [](PyRtraceSimulManager &self, const OrigDirec &rays) {
            if (!self.Ready())
              throw std::runtime_error("octree not loaded");
            size_t nrays;
            auto od = to_fvect(rays, nrays);
            const int nc = NCSAMP;
            float *buf = new float[nrays * nc]();
            auto result = owned_array(buf, {nrays, (size_t)nc});
            RayCollector col{buf, nrays, nc};
            const int saved_flags = self.rtFlags;
            self.rtFlags &= ~RTdoFIFO;
            self.SetCookedCall(collect_ray, &col);
            int ok;
            {
              nb::gil_scoped_release release;
              ok = self.EnqueueBundle(od.get(), (int)nrays, 1);
              if (ok >= 0 && self.FlushQueue() < 0)
                ok = -1;
            }
            self.RestoreCookedCall();
            self.rtFlags = saved_flags;
            raise_if_error();
            if (ok < 0)
              throw std::runtime_error("ray tracing failed");
            return result;
          },
          nb::arg("rays"),
          "Trace rays given as (2N, 3) origin/direction rows and return an "
          "(N, NCSAMP) float32 array of results. Any trace callback still "
          "runs, the cooked callback is bypassed.")
      .def("ready", &PyRtraceSimulManager::Ready)
      .def("flush_queue",
           [](PyRtraceSimulManager &self) {
             int n;
             {
               nb::gil_scoped_release release;
               n = self.FlushQueue();
             }
             raise_if_error();
             return n;
           })
      .def(
          "cleanup",
          [](PyRtraceSimulManager &self, bool everything) {
            int st = self.Cleanup(everything);
            if (everything) {
              // Cleanup() already detached the callbacks
              self.cooked.reset();
              self.traced.reset();
            }
            raise_if_error();
            return st;
          },
          nb::arg("everything") = false)
      .def_rw("rt_flags", &PyRtraceSimulManager::rtFlags)
      .def(
          "set_cooked_call",
          [](PyRtraceSimulManager &self, nb::object fn, nb::object data) {
            self.SetPyCookedCall(fn, data);
            raise_if_error();
          },
          nb::arg("callback").none(), nb::arg("client_data") = nb::none(),
          "Set callback(ray, client_data) for each finished primary ray, or "
          "None to remove it. A return value of -1 aborts the calculation.")
      .def(
          "set_trace_call",
          [](PyRtraceSimulManager &self, nb::object fn, nb::object data) {
            self.SetPyTraceCall(fn, data);
            raise_if_error();
          },
          nb::arg("callback").none(), nb::arg("client_data") = nb::none(),
          "Set callback(ray, client_data) for every ray traced, or None to "
          "remove it. With more than one thread this runs in child "
          "processes.")
      .def("cleanup_callbacks", [](PyRtraceSimulManager &self) {
        self.SetPyCookedCall(nb::none(), nb::none());
        self.SetPyTraceCall(nb::none(), nb::none());
        raise_if_error();
      });

  m.attr("RTdoFIFO") = (int)RTdoFIFO;
  m.attr("RTtraceSources") = (int)RTtraceSources;
  m.attr("RTlimDist") = (int)RTlimDist;
  m.attr("RTimmIrrad") = (int)RTimmIrrad;
  m.attr("RTmask") = (int)RTmask;

  m.attr("RCcontrib") = (int)RCcontrib;

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
               &RcontribOutput::Next),
           nb::rv_policy::reference)
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
             if (data == nullptr)
               throw std::runtime_error("cannot access shared data");
             nb::bytes result(static_cast<char *>(data), len);
             self.ReleaseMemory(data, 0);
             return result;
           },
           nb::arg("offs"), nb::arg("len"), nb::arg("fl") = (int)RDSread);

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
      .def(
          "set_data_format",
          [](RcontribSimulManager &self, nb::handle ty) {
            int c;
            if (nb::isinstance<nb::str>(ty)) {
              std::string s = nb::cast<std::string>(ty);
              if (s.size() != 1)
                throw nb::value_error("format must be 'f', 'd', or 'c'");
              c = s[0];
            } else {
              c = nb::cast<int>(ty);
            }
            if (c != 'f' && c != 'd' && c != 'c')
              throw nb::value_error("format must be 'f', 'd', or 'c'");
            if (self.GetOutput() != nullptr)
              throw std::runtime_error(
                  "set_data_format() must be called before add_modifier()");
            return self.SetDataFormat(c);
          },
          nb::arg("ty"), "Set output format ('f', 'd', or 'c')")
      .def(
          "get_format",
          [](const RcontribSimulManager &self) {
            int siz = 0;
            int ty = self.GetFormat(&siz);
            return nb::make_tuple(std::string(1, (char)ty), siz);
          },
          "Return (format character, element size in bytes)")
      .def(
          "add_modifier",
          [](RcontribSimulManager &self, const std::string &modn,
             const std::string &outspec, const std::string &prms,
             const std::string &binval, int bincnt) {
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
          [](RcontribSimulManager &self, std::optional<std::string> nm) {
            return self.GetOutput(nm ? nm->c_str() : nullptr);
          },
          nb::arg("nm") = nb::none(), nb::rv_policy::reference_internal,
          "Get the named output, or the first output if None. The result is "
          "invalidated by clear_modifiers() and cleanup().")
      .def(
          "get_output_array",
          [](RcontribSimulManager &self,
             std::optional<std::string> nm) -> nb::object {
            const RcontribOutput *out =
                self.GetOutput(nm ? nm->c_str() : nullptr);
            if (out == nullptr)
              throw nb::value_error(
                  nm ? ("no such output: " + *nm).c_str() : "no outputs");
            if (out->rData == nullptr)
              throw std::runtime_error(
                  "output not open, call prep_output() first");
            if (out->rData->GetType() == RDSTfile &&
                !(out->rData->GetMode() & RDSread))
              throw std::runtime_error(
                  "output was opened write-only; use the 'map' data share or "
                  "read the output file instead");
            int dsiz = 0;
            const int dtyp = self.GetFormat(&dsiz);
            const size_t elsize =
                dtyp == 'f' ? sizeof(float) : dtyp == 'd' ? sizeof(double) : 1;
            const size_t nbytes = (size_t)out->rowBytes * out->nRows;
            const size_t ncols = out->rowBytes / elsize;
            void *data = out->rData->GetMemory(out->begData, nbytes, RDSread);
            if (data == nullptr)
              throw std::runtime_error("cannot read output data");
            const size_t nrows = out->nRows;
            nb::object result;
            if (dtyp == 'f') {
              float *buf = new float[nrows * ncols];
              memcpy(buf, data, nbytes);
              result = nb::cast(owned_array(buf, {nrows, ncols}));
            } else if (dtyp == 'd') {
              double *buf = new double[nrows * ncols];
              memcpy(buf, data, nbytes);
              result = nb::cast(owned_array(buf, {nrows, ncols}));
            } else {
              uint8_t *buf = new uint8_t[nbytes];
              memcpy(buf, data, nbytes);
              result = nb::cast(owned_array(buf, {nrows, ncols}));
            }
            out->rData->ReleaseMemory(data, 0);
            return result;
          },
          nb::arg("nm") = nb::none(),
          "Copy the named output (or the first one) into a 2D numpy array of "
          "rows; float32 for 'f', float64 for 'd', raw bytes for 'c'.")
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
            if (!self.Ready())
              throw std::runtime_error(
                  "not ready, call prep_output() first");
            size_t nrays;
            auto od = to_fvect(rays, nrays);
            if (nrays != self.accum)
              throw nb::value_error(
                  ("expected " + std::to_string(self.accum) +
                   " rays (accum), got " + std::to_string(nrays))
                      .c_str());
            nb::gil_scoped_release release;
            return self.ComputeRecord(od.get());
          },
          nb::arg("orig_direc"))
      .def("flush_queue",
           [](RcontribSimulManager &self) {
             nb::gil_scoped_release release;
             return self.FlushQueue();
           })
      .def("reset_row", &RcontribSimulManager::ResetRow)
      .def("clear_modifiers", &RcontribSimulManager::ClearModifiers)
      .def("cleanup", &RcontribSimulManager::Cleanup,
           nb::arg("everything") = false)
      .def(
          "rcontrib",
          [](RcontribSimulManager &self, const OrigDirec &rays) {
            if (!self.Ready())
              throw std::runtime_error(
                  "not ready, call prep_output() first");
            const size_t totRows = self.GetRowMax();
            const size_t accum = self.accum;
            size_t nrays;
            auto od = to_fvect(rays, nrays);
            if (nrays != totRows * accum)
              throw nb::value_error(
                  ("expected " + std::to_string(totRows * accum) +
                   " rays (rows * accum), got " + std::to_string(nrays))
                      .c_str());
            size_t r = 0;
            {
              nb::gil_scoped_release release;
              for (; r < totRows; r++)
                if (self.ComputeRecord(od.get() + 2 * accum * r) <= 0)
                  break;
              if (r == totRows)
                self.FlushQueue();
            }
            if (r < totRows)
              throw std::runtime_error("record computation failed at row " +
                                       std::to_string(r));
          },
          nb::arg("rays"),
          "Compute all records from (2 * rows * accum, 3) origin/direction "
          "rows")
      .def_rw("out_op", &RcontribSimulManager::outOp)
      .def_prop_rw(
          "data_share",
          [](RcontribSimulManager &self) {
            return std::string(data_share_name(self.cdsF));
          },
          [](RcontribSimulManager &self, const std::string &name) {
            if (name == "map")
              self.cdsF = &mapDataShare;
            else if (name == "file")
              self.cdsF = &fileDataShare;
            else
              throw nb::value_error("data_share must be 'map' or 'file'");
          },
          "Output data share: 'map' (memory-mapped file, default) or 'file'")
      .def_rw("xres", &RcontribSimulManager::xres)
      .def_rw("yres", &RcontribSimulManager::yres)
      .def_rw("accum", &RcontribSimulManager::accum)
      .def("__enter__", [](RcontribSimulManager &self) { return &self; },
           nb::rv_policy::reference)
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
      .def("pre_view", &RpictSimulManager::PreView,
           nb::rv_policy::reference_internal,
           "Writeable previous view (for motion blur)")
      .def("get_width", &RpictSimulManager::GetWidth)
      .def("get_height", &RpictSimulManager::GetHeight)
      .def("t_width", &RpictSimulManager::TWidth)
      .def("t_height", &RpictSimulManager::THeight)
      .def_prop_rw(
          "prims",
          [](RpictSimulManager &self) -> nb::object {
            if (self.prims == NULL)
              return nb::none();
            if (self.prims == xyzprims)
              return nb::str("xyz");
            if (self.prims == stdprims)
              return nb::str("rgb");
            return nb::str("custom");
          },
          [](RpictSimulManager &self, std::optional<std::string> name) {
            if (!name)
              self.prims = NULL;
            else if (*name == "rgb")
              self.prims = stdprims;
            else if (*name == "xyz")
              self.prims = xyzprims;
            else
              throw nb::value_error("prims must be None, 'rgb', or 'xyz'");
          },
          "Output color space: None (spectral), 'rgb', or 'xyz'")
      .def_rw("frame_no", &RpictSimulManager::frameNo)
      .def(
          "new_frame",
          [](RpictSimulManager &self, const VIEW &v,
             const std::vector<int> &xydim, double ap,
             std::optional<std::vector<int>> tgrid) {
            if (xydim.size() != 2)
              throw nb::value_error("xydim must have 2 values");
            if (tgrid && tgrid->size() != 2)
              throw nb::value_error("tgrid must have 2 values");
            int dim[2] = {xydim[0], xydim[1]};
            if (!self.NewFrame(v, dim, &ap, tgrid ? tgrid->data() : nullptr))
              throw nb::value_error("invalid view or tile grid for frame");
            return nb::make_tuple(dim[0], dim[1], ap);
          },
          nb::arg("v"), nb::arg("xydim"), nb::arg("ap") = 1.0,
          nb::arg("tgrid") = nb::none(),
          "Set up a frame. Returns (xres, yres, pixel_aspect) adjusted for the "
          "view, pixel aspect ratio, and optional (nx, ny) tile grid.")
      .def(
          "render_tile",
          [](RpictSimulManager &self, std::optional<std::vector<int>> tile) {
            if (!self.Ready())
              throw std::runtime_error("octree not loaded");
            const int w = self.GetWidth(), h = self.GetHeight();
            const int tw = self.TWidth(), th = self.THeight();
            if (w <= 0 || h <= 0 || tw <= 0 || th <= 0)
              throw std::runtime_error("call new_frame() first");
            const int ntx = w / tw, nty = h / th;
            if (tile) {
              if (tile->size() != 2)
                throw nb::value_error("tile must have 2 values");
              if ((*tile)[0] < 0 || (*tile)[0] >= ntx || (*tile)[1] < 0 ||
                  (*tile)[1] >= nty)
                throw nb::value_error("tile index out of range");
            } else if (ntx > 1 || nty > 1) {
              throw nb::value_error("tile must be given when using a tile grid");
            }
            const size_t nc = self.prims ? 3 : NCSAMP;
            COLORV *cbuf = new COLORV[(size_t)tw * th * nc]();
            auto color = owned_array(cbuf, {(size_t)th, (size_t)tw, nc});
            float *zbuf = new float[(size_t)tw * th]();
            auto depth = owned_array(zbuf, {(size_t)th, (size_t)tw});
            bool ok;
            {
              nb::gil_scoped_release release;
              ok = self.RenderTile(cbuf, 0, zbuf,
                                   tile ? tile->data() : nullptr);
            }
            if (!ok)
              throw std::runtime_error("tile rendering failed");
            return nb::make_tuple(color, depth);
          },
          nb::arg("tile") = nb::none(),
          "Render the whole frame, or the given (tx, ty) tile, returning "
          "(color, depth) arrays. Rows start at the bottom of the image, as "
          "in Radiance.")
      .def(
          "render_frame",
          [](RpictSimulManager &self, const std::string &pfname,
             RenderDataType dt, std::optional<std::string> dfname) {
            RenderDataType res;
            {
              nb::gil_scoped_release release;
              res = self.RenderFrame(pfname.c_str(), dt,
                                     dfname ? dfname->c_str() : nullptr);
            }
            if (res == RDTnone)
              throw std::runtime_error("frame rendering failed");
            return res;
          },
          nb::arg("pfname"), nb::arg("dt") = RDTrgbe,
          nb::arg("dfname") = nb::none(),
          "Render frame to a new picture file (and optional depth file)")
      .def(
          "resume_frame",
          [](RpictSimulManager &self, const std::string &pfname,
             std::optional<std::string> dfname) {
            RenderDataType res;
            {
              nb::gil_scoped_release release;
              res = self.ResumeFrame(pfname.c_str(),
                                     dfname ? dfname->c_str() : nullptr);
            }
            if (res == RDTnone)
              throw std::runtime_error("frame rendering failed");
            return res;
          },
          nb::arg("pfname"), nb::arg("dfname") = nb::none(),
          "Resume a partially finished picture file")
      .def("set_thread_count", &RpictSimulManager::SetThreadCount,
           nb::arg("nt") = 0)
      .def("set_reference_depth",
           nb::overload_cast<const char *>(
               &RpictSimulManager::SetReferenceDepth),
           nb::arg("dstr"))
      .def("set_reference_depth",
           nb::overload_cast<double, const char *>(
               &RpictSimulManager::SetReferenceDepth),
           nb::arg("dref"), nb::arg("unit") = nullptr)
      .def(
          "get_reference_depth",
          [](const RpictSimulManager &self) {
            char du[64] = {0};
            double d = self.GetReferenceDepth(du);
            return nb::make_tuple(d, std::string(du));
          },
          "Return (reference depth, depth string with units)")
      .def("n_threads", &RpictSimulManager::NThreads);

  m.def("initfunc", &initfunc);
  m.def("loadfunc", [](const char *func){ return loadfunc(const_cast<char *>(func)); });
  m.def("eval",
        [](const char *expr) { return eval(const_cast<char *>(expr)); });
  m.def("set_eparams", &set_eparams);
  m.def("calcontext",
        [](const char *cxt) { return calcontext(const_cast<char *>(cxt)); });

  m.attr("RCCONTEXT") = nb::str(RCCONTEXT);
  m.def(
      "xyz_rgb",
      [](const Array3 xyz) {
        float *rgb = new float[3]();
        float xyz2[3] = {xyz(0), xyz(1), xyz(2)};
        cie_rgb(rgb, xyz2);
        return owned_array(rgb, {3});
      },
      "Convert CIE color to standard RGB");
}
