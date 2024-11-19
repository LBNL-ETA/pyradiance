#include "RtraceSimulManager.h"
#include "RcontribSimulManager.h"
#include "otspecial.h"
#include "otypes.h"
#include "platform.h"
#include "ray.h"
#include "resolu.h"
#include "source.h"
#include <functional>
#include <memory>
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <unordered_map>
#include <utility>
#include <vector>

namespace nb = nanobind;

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
          [](RtraceSimulManager &self,
             const nb::ndarray<double, nb::shape<-1, 3>> &orig_direc,
             RNUMBER rID0 = 0) {
            std::vector<std::array<double, 3>> data;
            /*auto arr = nb::cast<nb::ndarray<double>>(orig_direc);*/
            if (orig_direc.ndim() != 2 || orig_direc.shape(1) != 3) {
              throw std::runtime_error("NumPy array must be of shape (n, 3)");
            }
            int n = orig_direc.shape(0) / 2;
            const double(*orig_direc_ptr)[3] =
                reinterpret_cast<const double(*)[3]>(orig_direc.data());
            return self.EnqueueBundle(orig_direc_ptr, n, rID0);
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

  nb::class_<RcontribOutput>(m, "RcontribOutput")
      .def(nb::init<const char *>(), nb::arg("fnm") = nullptr)
      .def("GetName", &RcontribOutput::GetName)
      .def("SetRowsDone", &RcontribOutput::SetRowsDone)
      .def("GetRow", &RcontribOutput::GetRow)
      .def("InsertionP", &RcontribOutput::InsertionP)
      .def("DoneRow", &RcontribOutput::DoneRow)
      .def("Next",
           static_cast<const RcontribOutput *(RcontribOutput::*)() const>(
               &RcontribOutput::Next))
      .def("Next", static_cast<RcontribOutput *(RcontribOutput::*)()>(
                       &RcontribOutput::Next))
      .def_ro("rData", &RcontribOutput::rData)
      .def_ro("rowBytes", &RcontribOutput::rowBytes)
      .def_ro("omod", &RcontribOutput::omod)
      .def_ro("obin", &RcontribOutput::obin)
      .def_ro("begData", &RcontribOutput::begData)
      .def_ro("curRow", &RcontribOutput::curRow)
      .def_ro("nRows", &RcontribOutput::nRows);
}
