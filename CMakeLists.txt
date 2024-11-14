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

add_compile_definitions(error=rad_error)

set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -static")
set(CMAKE_BUILD_TYPE Debug)
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


add_subdirectory(src/radiance/common)
add_subdirectory(src/radiance/rt)

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

  # Source code goes here
  src/binding/pyradiance_ext.cpp

  src/radiance/rt/RtraceSimulManager.cpp

  # ${VERSION_C}
)

target_link_libraries(radiance_ext PRIVATE 
raycalls 
radiance 
cpprad
rtrad
m)
# Install directive for scikit-build-core
install(TARGETS radiance_ext LIBRARY DESTINATION pyradiance)
# if(UNIX)
#     target_link_options(radiance_ext PRIVATE -Wl,--allow-multiple-definition)
# endif()
