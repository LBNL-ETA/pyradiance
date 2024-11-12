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

// extern char *tralist[]; /* list of modifers to trace (or no) */
// extern int traincl;     /* include == 1, exclude == 0 */
// 
// int hresolu; /* horizontal resolution */
// int vresolu; /* vertical resolution */
// // Add necessary extern declarations
// extern char *octname;
// extern int nobjects;
// extern int castonly;
// extern int nsceneobjs;
// extern const char *formstr(int f);

// #ifndef MAXMODLIST
// #define MAXMODLIST 1024 /* maximum modifiers we'll track */
// #endif
// 
// #ifndef MAXTSET
// #define MAXTSET 8191 /* maximum number in trace set */
// #endif
// OBJECT traset[MAXTSET + 1] = {0}; /* trace include/exclude set */
// 
// typedef void putf_t(RREAL *v, int n);
// static putf_t puta, putd, putf, putrgbe;
// typedef void oputf_t(RAY *r);
// static oputf_t oputo, oputd, oputv, oputV, oputl, oputL, oputc, oputp, oputr,
    // oputR, oputx, oputX, oputn, oputN, oputs, oputw, oputW, oputm, oputM,
    // oputtilde;
// 
// static void tabin(RAY *r);
// static oputf_t *ray_out[32], *every_out[32];
// static putf_t *putreal;

// char VersionID[] =
    // "RADIANCE 6.0a lastmod Thu Aug 29 02:47:38 PM PDT 2024 by taoningw on lbnl";

// char *tralist[MAXMODLIST]; /* list of modifers to trace (or no) */
// int traincl = -1;
// int inform; /* input format */
// int outform = 'a';
// double (*sens_curve)(const SCOLOR scol) =
    // NULL;                      /* spectral conversion for 1-channel */
// double out_scalefactor = 1;    /* output calibration scale factor */
// RGBPRIMP out_prims = stdprims; /* output color primitives (NULL if spectral) */

// static void tabin(/* tab in appropriate amount */
/*                  RAY *r) {*/
/*  const RAY *rp;*/
/**/
/*  for (rp = r->parent; rp != NULL; rp = rp->parent)*/
/*    putchar('\t');*/
/*}*/
/* print ray values */
/*int ourtrace(RAY *r, void *cd) {*/
/*  oputf_t **tp;*/
/**/
/*  if (every_out[0] == NULL)*/
/*    return 0;*/
/*  if (r->ro == NULL) {*/
/*    if (traincl == 1)*/
/*      return 0;*/
/*  } else if (traincl != -1 && traincl != inset(traset, r->ro->omod))*/
/*    return 0;*/
/*  tabin(r);*/
/*  for (tp = every_out; *tp != NULL; tp++)*/
/*    (**tp)(r);*/
/*  if (outform == 'a')*/
/*    putchar('\n');*/
/*  return 1;*/
/*}*/
/**/
/* print requested ray values */
/*int printvals(RAY *r, void *cd) {*/
/*  oputf_t **tp;*/
/**/
/*  if (ray_out[0] == NULL)*/
/*    return 0;*/
/*  for (tp = ray_out; *tp != NULL; tp++)*/
/*    (**tp)(r);*/
/*  if (outform == 'a')*/
/*    putchar('\n');*/
/*  return 1;*/
/*}*/


NB_MODULE(radiance, m) {
  // inform = outform = 'a';
  // hresolu = 0;
  // vresolu = 0;
  // castonly = 0;
  // traincl = -1; // Important for ray tracing
  // out_scalefactor = 1;
  // out_prims = stdprims;
  // sens_curve = NULL;
  // tralist[0] = NULL;

  m.doc() = "This is a example";
  // using RayReportCall = int (*)(RAY *, void *);
  // m.def("ourtrace", ourtrace, "print ray values");
  // m.def("printvals", printvals, "print requested ray values");
  nb::class_<RadSimulManager>(m, "RadSimulManager")
      .def(nb::init<const char *>())
      .def("LoadOctree",
           [](RadSimulManager &self, const char *octn) {
             try {
               if (!octn) {
                 throw std::runtime_error("Octree filename is null");
               }
               if (access(octn, R_OK) != 0) {
                 throw std::runtime_error("Cannot access octree file");
               }
               fprintf(stderr, "Starting LoadOctree with: %s\n", octn);
               bool result = self.LoadOctree(octn);
               if (!result) {
                 throw std::runtime_error("Failed to load octree");
               }
               return result;
             } catch (const std::exception &e) {
               fprintf(stderr, "Exception in LoadOctree: %s\n", e.what());
               throw;
             } catch (...) {
               fprintf(stderr, "Unknown exception in LoadOctree\n");
               throw;
             }
           })
      .def("NewHeader", &RadSimulManager::NewHeader)
      .def("AddHeader",
           nb::overload_cast<const char *>(&RadSimulManager::AddHeader),
           "Add a line to header (adds newline if none)")
      .def("AddHeader",
           [](RadSimulManager &self, const std::vector<const char *> &args) {
             return self.AddHeader(args.size(),
                                   const_cast<char **>(args.data()));
           })
      .def("GetHeader", &RadSimulManager::GetHeader)
      .def("NThreads", &RadSimulManager::NThreads)
      .def("SetThreadCount", &RadSimulManager::SetThreadCount)
      .def("ThreadsAvailable", &RadSimulManager::ThreadsAvailable)
      .def("Ready", &RadSimulManager::Ready)
      .def("ProcessRay", &RadSimulManager::ProcessRay)
      .def("WaitResult", &RadSimulManager::WaitResult)
      .def("Cleanup", &RadSimulManager::Cleanup);

  nb::class_<RtraceSimulManager, RadSimulManager>(m, "RtraceSimulManager")

      .def(nb::init<>())
      .def(nb::init<RayReportCall *, void *, const char *>())
      .def("SetThreadCount", &RtraceSimulManager::SetThreadCount)
      .def("EnqueueBundle",
           [](RtraceSimulManager &self,
              nb::ndarray<double, nb::shape<-1, 3>> orig_direc, int n,
              RNUMBER rID0) {
             const double(*orig_direc_ptr)[3] =
                 reinterpret_cast<const double(*)[3]>(orig_direc.data());
             return self.EnqueueBundle(orig_direc_ptr, n, rID0);
           })
      .def("EnqueueRay", &RtraceSimulManager::EnqueueRay)
      .def("SetCookedCall", &RtraceSimulManager::SetCookedCall)
      .def("SetTraceCall", &RtraceSimulManager::SetTraceCall)
      .def("Ready", &RtraceSimulManager::Ready)
      .def("FlushQueue", &RtraceSimulManager::FlushQueue)
      .def("Cleanup", &RtraceSimulManager::Cleanup);
}
