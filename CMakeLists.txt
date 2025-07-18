cmake_minimum_required(VERSION 3.15...3.27)

project(pyradiance LANGUAGES CXX C)

# Set the C standard to C99 with GNU extensions
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON) # This enables GNU extensions (gnu99)
set(CMAKE_CXX_STANDARD 11)
if(CMAKE_VERSION VERSION_LESS 3.18)
  set(DEV_MODULE Development)
else()
  set(DEV_MODULE Development.Module)
endif()
find_package(
  Python 3.8
  COMPONENTS Interpreter ${DEV_MODULE}
  REQUIRED)

# Add this section early
include(FetchContent)

# Configure libtiff build options first
set(BUILD_SHARED_LIBS
    OFF
    CACHE BOOL "Build static libraries" FORCE)
set(CMAKE_FIND_LIBRARY_SUFFIXES ".a")

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE
      Release
      CACHE STRING "Choose the type of build." FORCE)
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release"
                                               "MinSizeRel" "RelWithDebInfo")
endif()

# Locate the threads package
set(CMAKE_THREAD_PREFER_PTHREAD TRUE)
set(THREADS_PREFER_PTHREAD_FLAG TRUE)
find_package(Threads REQUIRED)

set(PLATFORM_MATH_LIB)
if(UNIX)
  set(PLATFORM_MATH_LIB m)
  set(CMAKE_REQUIRED_LIBRARIES "${CMAKE_REQUIRED_LIBRARIES};m")
endif()

# Avoiding name clashes
add_compile_definitions(error=rad_error)

install(
  DIRECTORY
  DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/lib
  DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/bin)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE
  OUTPUT_VARIABLE nanobind_ROOT)

find_package(nanobind CONFIG REQUIRED)

# add_compile_options(-Wall -Wextra -Werror)
add_compile_options(-Wall)
if(MSVC)
  add_compile_options(
    /O2 # Maximum optimization
    /Oi # Enable intrinsic functions
    /Ot # Favor fast code
    /Oy # Omit frame pointers
    /GL # Whole program optimization
    /Qpar # Auto-parallelizer
    /fp:fast # Fast floating-point model
    # /arch:AVX2 # Use AVX2 instructions (modify based on target CPU)
    /GT # Fiber-safe optimizations
    /GF # String pooling
  )
  # Global link options
  add_link_options(/LTCG # Link-time code generation
  )
else() # GCC/Clang (Linux, macOS, MinGW)
  if(APPLE)
    add_definitions(-DBSD -DNOSTEREO -Dfreebsd)
    add_compile_options(
      -Ofast # Maximum optimization
      -funroll-loops # Unroll loops
    )
  else()
    add_definitions(-Dlinux -D_FILE_OFFSET_BITS=64 -DNOSTEREO)
    add_compile_options(
      -O3 # Maximum optimization
      -ffast-math
      -funroll-loops # Unroll loops
      -Wno-unused-const-variable)
  endif()

  nanobind_add_module(
    radiance_ext
    # Target the stable ABI for Python 3.12+, which reduces the number of binary
    # wheels that must be built. This does nothing on older Python versions
    STABLE_ABI
    # Build libnanobind statically and merge it into the extension (which itself
    # remains a shared library)
    #
    # If your project builds multiple extensions, you can replace this flag by
    # NB_SHARED to conserve space by reusing a shared libnanobind across
    # libraries
    NB_STATIC
    src/radiance/rt/RtraceSimulManager.cpp
    src/radiance/rt/RpictSimulManager.cpp
    src/radiance/rt/srcdraw.c
    src/radiance/rt/RcontribSimulManager.cpp
    src/radiance/rt/RdataShareMap.cpp
    src/radiance/rt/RdataShareFile.cpp
    src/binding/radiance_ext.cpp)
  target_include_directories(
    radiance_ext PRIVATE ${CMAKE_CURRENT_LIST_DIR}/src/radiance/common
                         ${CMAKE_CURRENT_LIST_DIR}/src/radiance/rt)
  target_link_libraries(radiance_ext PRIVATE raycalls radiance cpprad rtrad m)
  install(TARGETS radiance_ext LIBRARY DESTINATION pyradiance)
endif()

set(ZLIB_SUPPORT
    OFF
    CACHE BOOL "Enable Zlib usage" FORCE)
set(JPEG_SUPPORT
    OFF
    CACHE BOOL "Enable JPEG compression" FORCE)
set(OJPEG_SUPPORT
    OFF
    CACHE BOOL "Enable old-style JPEG compression" FORCE)
set(JBIG_SUPPORT
    OFF
    CACHE BOOL "Enable JBIG compression" FORCE)
set(WEBP_SUPPORT
    OFF
    CACHE BOOL "Enable WebP compression" FORCE)
set(ZSTD_SUPPORT
    OFF
    CACHE BOOL "Enable ZSTD compression" FORCE)
set(DEFLATE_SUPPORT
    OFF
    CACHE BOOL "Enable DEFLATE compression" FORCE)

# Declare and make libtiff available early
FetchContent_Declare(
  libtiff
  GIT_REPOSITORY https://gitlab.com/libtiff/libtiff.git
  GIT_TAG v4.7.0)

set(tiff-tools
    OFF
    CACHE BOOL "Build TIFF tools" FORCE)
set(tiff-tests
    OFF
    CACHE BOOL "Build TIFF tests" FORCE)
set(tiff-docs
    OFF
    CACHE BOOL "Build TIFF documentation" FORCE)
set(tiff-contrib
    OFF
    CACHE BOOL "Build TIFF contrib" FORCE)
set(tiff-install
    OFF
    CACHE BOOL "Install TIFF files" FORCE)
set(zlib
    OFF
    CACHE BOOL "" FORCE)
set(jpeg
    OFF
    CACHE BOOL "" FORCE)
set(pixarlog
    OFF
    CACHE BOOL "" FORCE)
set(libdeflate
    OFF
    CACHE BOOL "" FORCE)
set(lerc
    OFF
    CACHE BOOL "" FORCE)
set(lzma
    OFF
    CACHE BOOL "" FORCE)
set(webp
    OFF
    CACHE BOOL "" FORCE)
set(zstd
    OFF
    CACHE BOOL "" FORCE)

FetchContent_MakeAvailable(libtiff)

add_subdirectory(src/radiance/common)
add_subdirectory(src/radiance/rt)
add_subdirectory(src/radiance/cv)
add_subdirectory(src/radiance/gen)
add_subdirectory(src/radiance/ot)
add_subdirectory(src/radiance/px)
add_subdirectory(src/radiance/util)
add_subdirectory(src/radiance/cal)

nanobind_add_module(bsdf STABLE_ABI NB_STATIC src/binding/bsdf_ext.cpp)
target_include_directories(
  bsdf PRIVATE ${CMAKE_CURRENT_LIST_DIR}/src/radiance/common
               ${CMAKE_CURRENT_LIST_DIR}/src/radiance/rt)

target_link_libraries(bsdf PRIVATE rtrad ${PLATFORM_MATH_LIB}) # use -lm instead
                                                               # of libm.a

if(APPLE)
  target_compile_options(bsdf PRIVATE -include stdio.h)
endif()

# Install directive for scikit-build-core
install(TARGETS bsdf LIBRARY DESTINATION pyradiance)

nanobind_add_module(rad_params STABLE_ABI NB_STATIC src/binding/params.cpp)
target_include_directories(
  rad_params PRIVATE ${CMAKE_CURRENT_LIST_DIR}/src/radiance/common
                     ${CMAKE_CURRENT_LIST_DIR}/src/radiance/rt)
target_link_libraries(
  rad_params PRIVATE raycalls radiance cpprad rtrad ${PLATFORM_MATH_LIB}
)# use -lm instead of libm.a

if(APPLE)
  target_compile_options(rad_params PRIVATE -include stdio.h)
endif()

# Install directive for scikit-build-core
install(TARGETS rad_params LIBRARY DESTINATION pyradiance)
