cmake_minimum_required(VERSION 3.15...3.26)

project(pyradiance LANGUAGES CXX C)

# Try to import all Python components potentially needed by nanobind
find_package(Python 3.9
  REQUIRED COMPONENTS Interpreter Development.Module
  OPTIONAL_COMPONENTS Development.SABIModule)

# Avoiding name clashes
message(SKBUILD_PLATLIB_DIR="${SKBUILD_PLATLIB_DIR}")
add_compile_definitions(error=rad_error)

set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -static")
set(CMAKE_BUILD_TYPE Debug)

install(DIRECTORY
    DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/lib
    DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/bin
)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

execute_process(
COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE nanobind_ROOT)

find_package(nanobind CONFIG REQUIRED)

# add_compile_options(-Wall -Wextra -Werror)
add_compile_options(-Wall )
if(MSVC)
	add_compile_options(
	    /O2             # Maximum optimization
	    /Oi            # Enable intrinsic functions
	    /Ot            # Favor fast code
	    /Oy            # Omit frame pointers
	    /GL            # Whole program optimization
	    /Qpar          # Auto-parallelizer
	    /fp:fast       # Fast floating-point model
	    /arch:AVX2     # Use AVX2 instructions (modify based on target CPU)
	    /GT            # Fiber-safe optimizations
	    /GF            # String pooling
	)
	# Global link options
	add_link_options(
	    /LTCG          # Link-time code generation
	)

else() # GCC/Clang (Linux, macOS, MinGW)
	add_compile_options(
	    -O3                    # Maximum optimization
	    -flto                  # Link-time optimization
	    -march=native          # Optimize for local machine architecture
	    -ffast-math            # Fast math operations
	    -funroll-loops         # Unroll loops
	    -fomit-frame-pointer   # Omit frame pointer
	    -ffunction-sections    # Place each function in its own section
	    -fdata-sections        # Place each data item in its own section
	)

	if(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
	    add_compile_options(
		-fdevirtualize-at-ltrans  # Better devirtualization with LTO
		-fipa-pta                 # More aggressive function analysis
	    )
	endif()

	add_link_options(
	    -flto
	    -Wl,--gc-sections     # Remove unused code sections
	)

	if(APPLE)
	    add_compile_options(
		-momit-leaf-frame-pointer
	    )
	endif()
endif()


add_subdirectory(src/radiance/common)
add_subdirectory(src/radiance/rt)
add_subdirectory(src/radiance/cv)
add_subdirectory(src/radiance/gen)
add_subdirectory(src/radiance/ot)
add_subdirectory(src/radiance/px)
add_subdirectory(src/radiance/util)
add_subdirectory(src/radiance/cal)

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
  src/binding/radiance_ext.cpp
)

nanobind_add_module(
	bsdf

	STABLE_ABI

	NB_STATIC

	src/binding/bsdf_ext.cpp
)

target_include_directories(radiance_ext PRIVATE ${CMAKE_CURRENT_LIST_DIR}/src/radiance/common ${CMAKE_CURRENT_LIST_DIR}/src/radiance/rt)
target_include_directories(bsdf PRIVATE ${CMAKE_CURRENT_LIST_DIR}/src/radiance/common ${CMAKE_CURRENT_LIST_DIR}/src/radiance/rt)

target_link_libraries(radiance_ext PRIVATE raycalls radiance cpprad rtrad m)
target_link_libraries(bsdf PRIVATE rtrad m)
# Install directive for scikit-build-core
install(TARGETS radiance_ext LIBRARY DESTINATION pyradiance)
install(TARGETS bsdf LIBRARY DESTINATION pyradiance)
