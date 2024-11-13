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

function(generate_version_file OUTPUT_FILE VERSION_FILE)
    add_custom_command(
        OUTPUT ${OUTPUT_FILE}
        COMMAND ${CMAKE_COMMAND} 
            -D VERSION_FILE=${VERSION_FILE}
            -D OUTPUT_FILE=${OUTPUT_FILE}
            -P ${CMAKE_CURRENT_SOURCE_DIR}/generate_version.cmake
        DEPENDS ${VERSION_FILE} ${CMAKE_CURRENT_SOURCE_DIR}/generate_version.cmake
        COMMENT "Generating Version.c"
        VERBATIM
    )
endfunction()

# Example usage:
set(VERSION_FILE "${CMAKE_CURRENT_SOURCE_DIR}/src/radiance/rt/VERSION")
set(VERSION_C "${CMAKE_CURRENT_SOURCE_DIR}/src/radiance/rt/Version.c")


# Generate Version.c
generate_version_file(${VERSION_C} ${VERSION_FILE})

# Create a target that depends on Version.c
add_library(version_info OBJECT ${VERSION_C})

# Add Version.c to your main target
# Example: add_executable(your_app main.c $<TARGET_OBJECTS:version_info>)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
# Import nanobind through CMake's find_package mechanism
find_package(nanobind CONFIG REQUIRED)

include_directories(${CMAKE_CURRENT_LIST_DIR}/src/radiance/common)
include_directories(${CMAKE_CURRENT_LIST_DIR}/src/radiance/rt)

add_library(common STATIC
  src/radiance/common/abitmap.cpp
  src/radiance/common/badarg.c
  src/radiance/common/bmalloc.c
  src/radiance/common/fgetline.c
  src/radiance/common/bsdf.c
  src/radiance/common/bsdf_m.c
  src/radiance/common/bsdf_t.c
  src/radiance/common/sceneio.c
  src/radiance/common/caldefn.c
  src/radiance/common/calexpr.c
  src/radiance/common/calfunc.c
  src/radiance/common/ccyrgb.c
  src/radiance/common/color.c
  src/radiance/common/ccolor.c
  src/radiance/common/data.c
  src/radiance/common/disk2square.c
  src/radiance/common/dircode.c
  src/radiance/common/ealloc.c
  src/radiance/common/eputs.c
  src/radiance/common/error.c
  src/radiance/common/ezxml.c
  src/radiance/common/readfargs.c
  src/radiance/common/face.c
  src/radiance/common/cone.c
  src/radiance/common/font.c
  src/radiance/common/readmesh.c
  src/radiance/common/fdate.c
  src/radiance/common/fgetval.c
  src/radiance/common/getlibpath.c
  src/radiance/common/tmesh.c
  src/radiance/common/fgetword.c
  src/radiance/common/zeroes.c
  src/radiance/common/fputword.c
  src/radiance/common/fvect.c
  src/radiance/common/getpath.c
  src/radiance/common/gethomedir.c
  src/radiance/common/header.c
  src/radiance/common/hilbert.c
  src/radiance/common/instance.c
  src/radiance/common/image.c
  src/radiance/common/loadbsdf.c
  src/radiance/common/lookup.c
  src/radiance/common/mat4.c
  src/radiance/common/mesh.c
  src/radiance/common/modobject.c
  src/radiance/common/multisamp.c
  src/radiance/common/objset.c
  src/radiance/common/octree.c
  src/radiance/common/otypes.c
  src/radiance/common/process.c
  src/radiance/common/portio.c
  src/radiance/common/readobj.c
  src/radiance/common/resolu.c
  src/radiance/common/savestr.c
  src/radiance/common/savqstr.c
  src/radiance/common/spec_rgb.c
  src/radiance/common/tcos.c
  src/radiance/common/urand.c
  src/radiance/common/readoct.c
  src/radiance/common/quit.c
  src/radiance/common/words.c
  src/radiance/common/wputs.c
  src/radiance/common/xf.c
)
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
  src/binding/pyradiance_ext.cpp

  src/radiance/rt/RtraceSimulManager.cpp

  ${VERSION_C}
  # src/radiance/common/abitmap.cpp
  # src/radiance/common/badarg.c
  # src/radiance/common/bmalloc.c
  # src/radiance/common/fgetline.c
  # src/radiance/common/bsdf.c
  # src/radiance/common/bsdf_m.c
  # src/radiance/common/bsdf_t.c
  # src/radiance/common/sceneio.c
  # src/radiance/common/caldefn.c
  # src/radiance/common/calexpr.c
  # src/radiance/common/calfunc.c
  # src/radiance/common/ccyrgb.c
  # src/radiance/common/color.c
  # src/radiance/common/ccolor.c
  # src/radiance/common/data.c
  # src/radiance/common/disk2square.c
  # src/radiance/common/dircode.c
  # src/radiance/common/ealloc.c
  # src/radiance/common/eputs.c
  # src/radiance/common/error.c
  # src/radiance/common/ezxml.c
  # src/radiance/common/readfargs.c
  # src/radiance/common/face.c
  # src/radiance/common/cone.c
  # src/radiance/common/font.c
  # src/radiance/common/readmesh.c
  # src/radiance/common/fdate.c
  # src/radiance/common/fgetval.c
  # src/radiance/common/getlibpath.c
  # src/radiance/common/tmesh.c
  # src/radiance/common/fgetword.c
  # src/radiance/common/zeroes.c
  # src/radiance/common/fputword.c
  # src/radiance/common/fvect.c
  # src/radiance/common/getpath.c
  # src/radiance/common/gethomedir.c
  # src/radiance/common/header.c
  # src/radiance/common/hilbert.c
  # src/radiance/common/instance.c
  # src/radiance/common/image.c
  # src/radiance/common/loadbsdf.c
  # src/radiance/common/lookup.c
  # src/radiance/common/mat4.c
  # src/radiance/common/mesh.c
  # src/radiance/common/modobject.c
  # src/radiance/common/multisamp.c
  # src/radiance/common/objset.c
  # src/radiance/common/octree.c
  # src/radiance/common/otypes.c
  # src/radiance/common/process.c
  # src/radiance/common/portio.c
  # src/radiance/common/readobj.c
  # src/radiance/common/resolu.c
  # src/radiance/common/savestr.c
  # src/radiance/common/savqstr.c
  # src/radiance/common/spec_rgb.c
  # src/radiance/common/tcos.c
  # src/radiance/common/urand.c
  # src/radiance/common/readoct.c
  # src/radiance/common/quit.c
  # src/radiance/common/words.c
  # src/radiance/common/wputs.c
  # src/radiance/common/xf.c

  src/radiance/rt/ambcomp.c
  src/radiance/rt/source.c
  src/radiance/rt/freeobjmem.c
  src/radiance/rt/srcobstr.c
  src/radiance/rt/srcsamp.c
  src/radiance/rt/preload.c
  src/radiance/rt/ambient.c
  src/radiance/rt/ambio.c
  src/radiance/rt/func.c
  src/radiance/rt/initotypes.c
  src/radiance/rt/dielectric.c
  src/radiance/rt/m_clip.c
  src/radiance/rt/mx_data.c
  src/radiance/rt/normal.c
  src/radiance/rt/glass.c
  src/radiance/rt/p_data.c
  src/radiance/rt/p_func.c
  src/radiance/rt/srcsupp.c
  src/radiance/rt/raytrace.c
  src/radiance/rt/rayfifo.c
  # src/radiance/rt/rtrace.c
  src/radiance/rt/fprism.c
  src/radiance/rt/ashikhmin.c
  src/radiance/rt/noise3.c
  src/radiance/rt/aniso.c
  src/radiance/rt/m_alias.c
  src/radiance/rt/m_brdf.c
  src/radiance/rt/m_bsdf.c
  src/radiance/rt/m_direct.c
  src/radiance/rt/m_mirror.c
  src/radiance/rt/m_mist.c
  src/radiance/rt/mx_func.c
  src/radiance/rt/o_cone.c
  src/radiance/rt/o_face.c
  src/radiance/rt/o_instance.c
  src/radiance/rt/o_mesh.c
  src/radiance/rt/text.c
  src/radiance/rt/sphere.c
  src/radiance/rt/t_data.c
  src/radiance/rt/t_func.c
  src/radiance/rt/virtuals.c
  src/radiance/rt/raycalls.c
  src/radiance/rt/raypcalls.c

  src/radiance/rt/pmapamb.c
  src/radiance/rt/pmapbias.c
  src/radiance/rt/pmapparm.c
  src/radiance/rt/pmapio.c
  src/radiance/rt/pmapdata.c
  src/radiance/rt/pmaptype.c
  src/radiance/rt/pmaprand.c
  src/radiance/rt/pmapray.c
  src/radiance/rt/pmapsrc.c
  src/radiance/rt/pmutil.c
)

target_link_libraries(radiance PRIVATE common)
# Install directive for scikit-build-core
install(TARGETS radiance LIBRARY DESTINATION pyradiance)
