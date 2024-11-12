cmake_minimum_required(VERSION 3.15...3.26)

project(pyradiance LANGUAGES CXX C)

if (NOT SKBUILD)
  message(WARNING "\
  This CMake file is meant to be executed using 'scikit-build'. Running
  it directly will almost certainly not produce the desired result. If
  you are a user trying to install this package, please use the command
  below, which will install all necessary build dependencies, compile
  the package in an isolated environment, and then install it.
  =====================================================================
   $ pip install .
  =====================================================================
  If you are a software developer, and this is your own package, then
  it is usually much more efficient to install the build dependencies
  in your environment once and use the following command that avoids
  a costly creation of a new virtual environment at every compilation:
  =====================================================================
   $ pip install nanobind scikit-build-core[pyproject]
   $ pip install --no-build-isolation -ve .
  =====================================================================
  You may optionally add -Ceditable.rebuild=true to auto-rebuild when
  the package is imported. Otherwise, you need to re-run the above
  after editing C++ files.")
endif()

# Try to import all Python components potentially needed by nanobind
find_package(Python 3.8
  REQUIRED COMPONENTS Interpreter Development.Module
  OPTIONAL_COMPONENTS Development.SABIModule)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
# Import nanobind through CMake's find_package mechanism
find_package(nanobind CONFIG REQUIRED)

include_directories(${CMAKE_CURRENT_LIST_DIR}/src/Radiance/src/common)
include_directories(${CMAKE_CURRENT_LIST_DIR}/src/Radiance/src/rt)

# We are now ready to compile the actual extension module
nanobind_add_module(
  # Name of the extension
  radiance

  # Target the stable ABI for Python 3.12+, which reduces
  # the number of binary wheels that must be built. This
  # does nothing on older Python versions
  STABLE_ABI

  # Build libnanobind statically and merge it into the
  # extension (which itself remains a shared library)
  #
  # If your project builds multiple extensions, you can
  # replace this flag by NB_SHARED to conserve space by
  # reusing a shared libnanobind across libraries
  NB_STATIC

  # Source code goes here
  src/pyradiance_ext.cpp

  src/Radiance/src/rt/RtraceSimulManager.cpp

  src/Radiance/src/common/badarg.c
  src/Radiance/src/common/bmalloc.c
  src/Radiance/src/common/fgetline.c
  src/Radiance/src/common/bsdf.c
  src/Radiance/src/common/bsdf_m.c
  src/Radiance/src/common/bsdf_t.c
  src/Radiance/src/common/sceneio.c
  src/Radiance/src/common/caldefn.c
  src/Radiance/src/common/calexpr.c
  src/Radiance/src/common/calfunc.c
  src/Radiance/src/common/ccyrgb.c
  src/Radiance/src/common/color.c
  src/Radiance/src/common/ccolor.c
  src/Radiance/src/common/data.c
  src/Radiance/src/common/disk2square.c
  src/Radiance/src/common/dircode.c
  src/Radiance/src/common/ealloc.c
  src/Radiance/src/common/eputs.c
  src/Radiance/src/common/error.c
  src/Radiance/src/common/ezxml.c
  src/Radiance/src/common/readfargs.c
  src/Radiance/src/common/face.c
  src/Radiance/src/common/cone.c
  src/Radiance/src/common/font.c
  src/Radiance/src/common/readmesh.c
  src/Radiance/src/common/fdate.c
  src/Radiance/src/common/fgetval.c
  src/Radiance/src/common/getlibpath.c
  src/Radiance/src/common/tmesh.c
  src/Radiance/src/common/fgetword.c
  src/Radiance/src/common/zeroes.c
  src/Radiance/src/common/fputword.c
  src/Radiance/src/common/fvect.c
  src/Radiance/src/common/getpath.c
  src/Radiance/src/common/gethomedir.c
  src/Radiance/src/common/header.c
  src/Radiance/src/common/hilbert.c
  src/Radiance/src/common/instance.c
  src/Radiance/src/common/image.c
  src/Radiance/src/common/loadbsdf.c
  src/Radiance/src/common/lookup.c
  src/Radiance/src/common/mat4.c
  src/Radiance/src/common/mesh.c
  src/Radiance/src/common/modobject.c
  src/Radiance/src/common/multisamp.c
  src/Radiance/src/common/objset.c
  src/Radiance/src/common/octree.c
  src/Radiance/src/common/otypes.c
  src/Radiance/src/common/process.c
  src/Radiance/src/common/portio.c
  src/Radiance/src/common/readobj.c
  src/Radiance/src/common/resolu.c
  src/Radiance/src/common/savestr.c
  src/Radiance/src/common/savqstr.c
  src/Radiance/src/common/spec_rgb.c
  src/Radiance/src/common/tcos.c
  src/Radiance/src/common/urand.c
  src/Radiance/src/common/readoct.c
  src/Radiance/src/common/quit.c
  src/Radiance/src/common/words.c
  src/Radiance/src/common/wputs.c
  src/Radiance/src/common/xf.c

  src/Radiance/src/rt/ambcomp.c
  src/Radiance/src/rt/source.c
  src/Radiance/src/rt/freeobjmem.c
  src/Radiance/src/rt/srcobstr.c
  src/Radiance/src/rt/srcsamp.c
  src/Radiance/src/rt/preload.c
  src/Radiance/src/rt/ambient.c
  src/Radiance/src/rt/ambio.c
  src/Radiance/src/rt/func.c
  src/Radiance/src/rt/initotypes.c
  src/Radiance/src/rt/dielectric.c
  src/Radiance/src/rt/m_clip.c
  src/Radiance/src/rt/mx_data.c
  src/Radiance/src/rt/normal.c
  src/Radiance/src/rt/glass.c
  src/Radiance/src/rt/p_data.c
  src/Radiance/src/rt/p_func.c
  src/Radiance/src/rt/srcsupp.c
  src/Radiance/src/rt/raytrace.c
  src/Radiance/src/rt/rayfifo.c
  # src/Radiance/src/rt/rtrace.c
  src/Radiance/src/rt/fprism.c
  src/Radiance/src/rt/ashikhmin.c
  src/Radiance/src/rt/noise3.c
  src/Radiance/src/rt/aniso.c
  src/Radiance/src/rt/m_alias.c
  src/Radiance/src/rt/m_brdf.c
  src/Radiance/src/rt/m_bsdf.c
  src/Radiance/src/rt/m_direct.c
  src/Radiance/src/rt/m_mirror.c
  src/Radiance/src/rt/m_mist.c
  src/Radiance/src/rt/mx_func.c
  src/Radiance/src/rt/o_cone.c
  src/Radiance/src/rt/o_face.c
  src/Radiance/src/rt/o_instance.c
  src/Radiance/src/rt/o_mesh.c
  src/Radiance/src/rt/text.c
  src/Radiance/src/rt/sphere.c
  src/Radiance/src/rt/t_data.c
  src/Radiance/src/rt/t_func.c
  src/Radiance/src/rt/virtuals.c
  src/Radiance/src/rt/raycalls.c
  src/Radiance/src/rt/raypcalls.c

  src/Radiance/src/rt/pmapamb.c
  src/Radiance/src/rt/pmapbias.c
  src/Radiance/src/rt/pmapparm.c
  src/Radiance/src/rt/pmapio.c
  src/Radiance/src/rt/pmapdata.c
  src/Radiance/src/rt/pmaptype.c
  src/Radiance/src/rt/pmaprand.c
  src/Radiance/src/rt/pmapray.c
  src/Radiance/src/rt/pmapsrc.c
  src/Radiance/src/rt/pmutil.c
)

# Install directive for scikit-build-core
install(TARGETS radiance LIBRARY DESTINATION pyradiance)
