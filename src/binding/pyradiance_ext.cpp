#include "RtraceSimulManager.h"
#include "otspecial.h"
#include "otypes.h"
#include "platform.h"
#include "ray.h"
#include "resolu.h"
#include "source.h"
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <vector>

namespace nb = nanobind;

using namespace nb::literals;

struct CallbackData {
  nb::object callback;
  nb::object data;
};

struct PyRtraceSimulManager : public RtraceSimulManager {

private:
  CallbackData cooked_cb_data;
  CallbackData trace_cb_data;
  PyRtraceSimulManager(nb::object cb = nb::none(), nb::object cd = nb::none(),
                       const char *octn = nullptr)
      : RtraceSimulManager(nullptr, nullptr, octn) {
    if (!cb.is_none())
      SetCookedCall(cb, cd);
  }

public:
  static int PythonCallback(RAY *r, void *cd) {
    CallbackData *cb_data = static_cast<CallbackData *>(cd);
    if (cb_data->callback.is_none())
      return -1;
    nb::object py_ray = nb::cast(r, nb::rv_policy::reference);
    try {
      nb::object result;
      if (!cb_data->data.is_none()) {
        result = cb_data->callback(py_ray, cb_data->data);
      } else {
        result = cb_data->callback(py_ray);
      }
      return nb::cast<int>(result);
    } catch (nb::python_error &e) {
      // Handle exception if needed
      e.restore();
      return -1;
    }
  }
  void SetCookedCall(nb::object cb, nb::object cd = nb::none()) {
    // Store the Python callable and data
    cooked_cb_data.callback = cb;
    cooked_cb_data.data = cd;
    // Set the C++ callback function to our static method
    RtraceSimulManager::SetCookedCall(&PyRtraceSimulManager::PythonCallback,
                                      &cooked_cb_data);
  }

  void SetTraceCall(nb::object cb, nb::object cd = nb::none()) {
    trace_cb_data.callback = cb;
    trace_cb_data.data = cd;
    RtraceSimulManager::SetTraceCall(&PyRtraceSimulManager::PythonCallback,
                                     &trace_cb_data);
  }
};

NB_MODULE(radiance_ext, m) {

  m.doc() = "Radiance extension";

  nb::class_<RAY>(m, "RAY")
      .def(nb::init<>())
      .def_ro("rorg", &RAY::rorg)
      /*.def_property(*/
      /*    "rorg",*/
      /*    [](RAY &self) {*/
      /*      return std::array<RREAL, 3>{self.rorg[0], self.rorg[1],*/
      /*                                  self.rorg[2]};*/
      /*    },*/
      /*    [](RAY &self, const std::array<RREAL, 3> &value) {*/
      /*      self.rorg[0] = value[0];*/
      /*      self.rorg[1] = value[1];*/
      /*      self.rorg[2] = value[2];*/
      /*    })*/
      .def_ro("rdir", &RAY::rdir)
      .def_ro("rmax", &RAY::rmax)
      .def_ro("rot", &RAY::rot)
      .def_ro("rop", &RAY::rop)
      .def_ro("ron", &RAY::ron)
      .def_ro("rod", &RAY::rod)
      .def_ro("uv", &RAY::uv)
      .def_ro("pert", &RAY::pert)
      .def_ro("rmt", &RAY::rmt)
      .def_ro("rxt", &RAY::rxt)
      .def_ro("parent", &RAY::parent)
      .def_ro("rno", &RAY::rno)
      .def_ro("robj", &RAY::robj)
      .def_ro("rsrc", &RAY::rsrc)
      .def_ro("rweight", &RAY::rweight)
      .def_ro("gecc", &RAY::gecc)
      .def_ro("rcoef", &RAY::rcoef)
      .def_ro("pcol", &RAY::pcol)
      .def_ro("mcol", &RAY::mcol)
      .def_ro("rcol", &RAY::rcol)
      .def_ro("cext", &RAY::cext)
      .def_ro("albedo", &RAY::albedo)
      .def_ro("rflips", &RAY::rflips)
      .def_ro("rlvl", &RAY::rlvl)
      .def_ro("rtype", &RAY::rtype)
      .def_ro("crtype", &RAY::crtype);

  nb::class_<RadSimulManager>(m, "RadSimulManager")
      .def(nb::init<const char *>())
      .def("load_octree", &RadSimulManager::LoadOctree)
      .def("new_header", &RadSimulManager::NewHeader)
      .def("add_header",
           nb::overload_cast<const char *>(&RadSimulManager::AddHeader),
           "Add a line to header (adds newline if none)")
      .def("add_header",
           [](RadSimulManager &self, const std::vector<const char *> &args) {
             return self.AddHeader(args.size(),
                                   const_cast<char **>(args.data()));
           })
      .def("get_head_len", &RadSimulManager::GetHeadLen)
      .def("get_head_str", (const char *(RadSimulManager::*)() const) &
                               RadSimulManager::GetHeadStr)
      .def("get_head_str",
           (const char *(RadSimulManager::*)(const char *, bool) const) &
               RadSimulManager::GetHeadStr)
      .def("nthreads", &RadSimulManager::NThreads)
      .def("set_thread_count", &RadSimulManager::SetThreadCount,
           nb::arg("nt") = 0)
      .def("threads_available", &RadSimulManager::ThreadsAvailable)
      .def("ready", &RadSimulManager::Ready)
      .def("process_ray", &RadSimulManager::ProcessRay)
      .def("wait_result", &RadSimulManager::WaitResult)
      .def("cleanup", &RadSimulManager::Cleanup, nb::arg("everything") = false);

  nb::class_<PyRtraceSimulManager, RtraceSimulManager>(m, "RtraceSimulManager")

      .def(nb::init<>())
      .def(nb::init<RayReportCall *, void *, const char *>())
      .def("set_thread_count", &RtraceSimulManager::SetThreadCount,
           nb::arg("nt") = 0)
      .def(
          "enqueue_bundle",
          [](RtraceSimulManager &self,
             nb::ndarray<double, nb::shape<-1, 3>> orig_direc,
             RNUMBER rID0 = 0) {
            // Ensure array has correct dimensions
            if (orig_direc.ndim() != 2 || orig_direc.shape(1) != 3) {
              throw std::runtime_error("Input array must be of shape (n, 3)");
            }
            int n = orig_direc.shape(0);
            // Access data pointer
            const double(*orig_direc_ptr)[3] =
                reinterpret_cast<const double(*)[3]>(orig_direc.data());
            return self.EnqueueBundle(orig_direc_ptr, n, rID0);
          },
          nb::arg("orig_direc"), nb::arg("rID0") = 0)
      .def("enqueue_ray", &RtraceSimulManager::EnqueueRay, nb::arg("org"),
           nb::arg("dir"), nb::arg("rID") = 0)
      .def("set_cooked_call", &PyRtraceSimulManager::SetCookedCall,
           nb::arg("callback"))
      .def("set_trace_call", &PyRtraceSimulManager::SetTraceCall,
           nb::arg("callback"))
      .def("ready", &RtraceSimulManager::Ready)
      .def("flush_queue", &RtraceSimulManager::FlushQueue)
      .def("cleanup", &RtraceSimulManager::Cleanup,
           nb::arg("everything") = false);

  nb::enum_<decltype(RTdoFIFO)>(m, "RTFlags")
      .value("RTdoFIFO", RTdoFIFO)
      .value("RTtraceSources", RTtraceSources)
      .value("RTlimDist", RTlimDist)
      .value("RTimmIrrad", RTimmIrrad)
      .value("RTmask", RTmask);
}
