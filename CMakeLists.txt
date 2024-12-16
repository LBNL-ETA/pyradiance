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
find_package(Python 3.9
  REQUIRED COMPONENTS Interpreter Development.Module
  OPTIONAL_COMPONENTS Development.SABIModule)

# Get the Python installation directory
# execute_process(
#     COMMAND "${Python_EXECUTABLE}" -c "import site; print(site.getsitepackages()[0])"
#     OUTPUT_VARIABLE PYTHON_INSTALL_DIR
#     OUTPUT_STRIP_TRAILING_WHITESPACE
# )

# Avoiding name clashes
message(SKBUILD_PLATLIB_DIR="${SKBUILD_PLATLIB_DIR}")
add_compile_definitions(error=rad_error)

set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -static")
set(CMAKE_BUILD_TYPE Debug)

# message(PYTHON_INSTALL_DIR="${PYTHON_INSTALL_DIR}")
install(DIRECTORY
    # DESTINATION ${PYTHON_INSTALL_DIR}/pyradiance/lib
    DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/lib
)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
# Import nanobind through CMake's find_package mechanism
find_package(nanobind CONFIG REQUIRED)

include_directories(${CMAKE_CURRENT_LIST_DIR}/src/radiance/common)
include_directories(${CMAKE_CURRENT_LIST_DIR}/src/radiance/rt)

add_subdirectory(src/radiance/common)
add_subdirectory(src/radiance/rt)
add_subdirectory(src/radiance/gen)
add_subdirectory(src/radiance/util)

# We are now ready to compile the actual extension module
nanobind_add_module(
  # Name of the extension
  radiance_ext

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

  src/radiance/rt/RtraceSimulManager.cpp
  src/radiance/rt/RcontribSimulManager.cpp
  src/radiance/rt/RdataShareMap.cpp
  src/radiance/rt/RdataShareFile.cpp
  # src/radiance/rt/rxcmain.cpp
  src/binding/pyradiance_ext.cpp
)

add_compile_options(-Wall -Wextra -Werror)
target_link_libraries(radiance_ext PRIVATE raycalls radiance cpprad rtrad m)
# Install directive for scikit-build-core
install(TARGETS radiance_ext LIBRARY DESTINATION pyradiance)
