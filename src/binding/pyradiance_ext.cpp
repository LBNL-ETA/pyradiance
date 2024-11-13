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

NB_MODULE(radiance_ext, m) {

  m.doc() = "This is Radiance";
  nb::class_<RadSimulManager>(m, "RadSimulManager")
      .def(nb::init<const char *>())
      .def("load_octree", &RadSimulManager::LoadOctree)
      /*.def("load_octree",*/
      /*     [](RadSimulManager &self, const char *octn) {*/
      /*       bool result = self.LoadOctree(octn);*/
      /*     })*/
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

  nb::class_<RtraceSimulManager, RadSimulManager>(m, "RtraceSimulManager")

      .def(nb::init<>())
      .def(nb::init<RayReportCall *, void *, const char *>())
      .def("set_thread_count", &RtraceSimulManager::SetThreadCount,
           nb::arg("nt") = 0)
      .def(
          "enqueue_bundle",
          [](RtraceSimulManager &self,
             nb::ndarray<double, nb::shape<-1, 3>> orig_direc, int n,
             RNUMBER rID0 = 0) {
            const double(*orig_direc_ptr)[3] =
                reinterpret_cast<const double(*)[3]>(orig_direc.data());
            return self.EnqueueBundle(orig_direc_ptr, n, rID0);
          },
          nb::arg("orig_direc"), nb::arg("n"), nb::arg("rID0") = 0)
      .def("enqueue_ray", &RtraceSimulManager::EnqueueRay, nb::arg("org"),
           nb::arg("dir"), nb::arg("rID") = 0)
      /*.def("SetCookedCall", &RtraceSimulManager::SetCookedCall)*/
      /*.def("SetTraceCall", &RtraceSimulManager::SetTraceCall)*/
      .def("set_cooked_call", &RtraceSimulManager::SetCookedCall, nb::arg("cb"),
           nb::arg("cd") = nullptr)
      .def("set_trace_call", &RtraceSimulManager::SetTraceCall, nb::arg("cb"),
           nb::arg("cd") = nullptr)
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
