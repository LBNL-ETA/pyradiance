#include <functional>
#include <memory>
#include <unordered_map>
#include <utility>
#include <vector>

#include "RcontribSimulManager.h"
#include "RdataShare.h"
#include "RtraceSimulManager.h"
#include "func.h"
#include "otspecial.h"
#include "otypes.h"
#include "platform.h"
#include "ray.h"
#include "resolu.h"
#include "source.h"

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

namespace nb = nanobind;

using OrigDirec = nb::ndarray<double, nb::shape<-1, 3>>;

// Store callbacks globally (not ideal but works for now)
static std::unordered_map<void *, std::shared_ptr<nb::callable>>
    stored_callbacks;

// Function that will be called from C++
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

// Global storage for the Python callback
static std::shared_ptr<nb::callable> stored_cdsf_callback;

// Global wrapper function that will be used as the function pointer
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

// Add the function declaration here
void rxcontrib(const int rstart = 0);

void ndarray_to_fvect(const OrigDirec arr, FVECT *output) {
  // Get data pointer and copy
  const double *data = static_cast<const double *>(arr.data());
  for (size_t i = 0; i < arr.shape(0); ++i) {
    output[i][0] = data[i * 3];
    output[i][1] = data[i * 3 + 1];
    output[i][2] = data[i * 3 + 2];
  }
}

NB_MODULE(radiance_ext, m) {

  m.doc() = "Radiance extension";
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

  nb::class_<RtraceSimulManager>(m, "RtraceSimulManager")

      .def(nb::init<>())
      .def("load_octree", &RtraceSimulManager::LoadOctree)
      .def("set_thread_count", &RtraceSimulManager::SetThreadCount,
           nb::arg("nt") = 0)
      .def(
          "enqueue_bundle",
          [](RtraceSimulManager &self, const nb::sequence &orig_direc,
             RNUMBER rID0 = 0) {
            std::vector<std::array<double, 3>> data;
            auto seq = nb::cast<nb::sequence>(orig_direc);
            size_t n = len(seq) / 2;
            data.reserve(n * 2);
            for (size_t i = 0; i < n * 2; ++i) {
              auto row = nb::cast<nb::sequence>(seq[i]);
              std::array<double, 3> point;
              for (size_t j = 0; j < 3; ++j) {
                point[j] = nb::cast<double>(row[j]);
              }
              data.push_back(point);
            }

            return self.EnqueueBundle(
                reinterpret_cast<const double(*)[3]>(data.data()), n, rID0);
          },
          nb::arg("orig_direc"), nb::arg("rID0") = 0)
      .def(
          "enqueue_bundle_array",
          [](RtraceSimulManager &self, const OrigDirec &orig_direc,
             RNUMBER rID0 = 0) {
            FVECT *output;
            ndarray_to_fvect(orig_direc, output);
            int n = orig_direc.shape(0) / 2;
            return self.EnqueueBundle(output, n, rID0);
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
      .def("cleanup_callbacks", [](RtraceSimulManager &self) {
        stored_callbacks.clear();
        self.SetCookedCall(nullptr, nullptr);
        self.SetTraceCall(nullptr, nullptr);
      });

  nb::enum_<decltype(RTdoFIFO)>(m, "RTFlags")
      .value("RTdoFIFO", RTdoFIFO)
      .value("RTtraceSources", RTtraceSources)
      .value("RTlimDist", RTlimDist)
      .value("RTimmIrrad", RTimmIrrad)
      .value("RTmask", RTmask);

  // For the callback handling
  m.def("make_ray_report_callback", [](nb::callable callback) {
    return [callback](RAY *r, void *cd) -> int {
      nb::gil_scoped_acquire acquire;
      try {
        nb::object result = callback(nb::cast(r), nb::cast(cd));
        return nb::cast<int>(result);
      } catch (const std::exception &e) {
        return -1;
      }
    };
  });

  m.attr("rt_do_fifo") = (int)RTdoFIFO;
  m.attr("rt_trace_sources") = (int)RTtraceSources;
  m.attr("rt_lim_dist") = (int)RTlimDist;
  m.attr("rt_imm_irrad") = (int)RTimmIrrad;
  m.attr("rt_mask") = (int)RTmask;

  nb::enum_<RCOutputOp>(m, "RcOutputOp")
      .value("rco_new", RCOnew)
      .value("rco_force", RCOforce)
      .value("rco_recover", RCOrecover);

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
      /*.def("get_memory", &RdataShare::GetMemory)*/
      .def("get_memory",
           [](RdataShare &self, size_t offs, size_t len, int fl) {
             void *data = self.GetMemory(offs, len, fl);
             /*return nb::bytes(static_cast<char *>(data), len);*/
             return nb::ndarray<nb::numpy, int>(static_cast<int *>(data),
                                                {len / sizeof(int)} // shape
             );
           })
      .def("release_memory", &RdataShare::ReleaseMemory);

  // Bind default data share function
  m.def("default_data_share", &defDataShare,
        "Default implementation of data share creation", nb::arg("name"),
        nb::arg("op"), nb::arg("siz"));

  nb::class_<RcontribSimulManager>(m, "RcontribSimulManager")
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
          [](RcontribSimulManager &self, OrigDirec &rays) {
            FVECT *output;
            ndarray_to_fvect(rays, output);
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

            while (r < totRows) { // loop until done
              int ri = r * 2;
              int ri1 = ri + 1;
              for (int i = 0; i < n2go; i++) {
                int ni = i * 2;
                int ni1 = ni + 1;
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

  m.def("initfunc", &initfunc);
  m.def("loadfunc", &loadfunc);
  m.def("eval",
        [](const char *expr) { return eval(const_cast<char *>(expr)); });
  m.def("set_eparams", &set_eparams);
  m.def("calcontext",
        [](const char *cxt) { return calcontext(const_cast<char *>(cxt)); });

  m.def("rxcontrib", &rxcontrib);
  m.attr("RCCONTEXT") = nb::str(RCCONTEXT);
}
