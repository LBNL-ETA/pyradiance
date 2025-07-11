add_executable(ies2rad ies2rad.c)
target_include_directories(ies2rad
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ies2rad rtrad ${PLATFORM_MATH_LIB})

add_executable(arch2rad arch2rad.c trans.c)
target_include_directories(arch2rad
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(arch2rad rtrad ${PLATFORM_MATH_LIB})

add_executable(nff2rad nff2rad.c)
target_include_directories(nff2rad
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)

add_executable(lampcolor lampcolor.c)
target_include_directories(lampcolor
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(lampcolor rtrad ${PLATFORM_MATH_LIB})

add_executable(tmesh2rad tmesh2rad.c)
target_include_directories(tmesh2rad
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(tmesh2rad rtrad ${PLATFORM_MATH_LIB})

add_executable(obj2rad obj2rad.c trans.c)
target_include_directories(obj2rad
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(obj2rad rtrad ${PLATFORM_MATH_LIB})

add_executable(robjutil robjutil.c)
target_include_directories(robjutil
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(robjutil wfobj rtrad ${PLATFORM_MATH_LIB})

add_executable(mgf2rad mgf2rad.c)
target_include_directories(mgf2rad
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(mgf2rad mgf rtrad ${PLATFORM_MATH_LIB})

add_executable(rad2mgf rad2mgf.c)
target_include_directories(rad2mgf
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rad2mgf rtrad ${PLATFORM_MATH_LIB})

add_executable(mgfilt mgfilt.c)
target_include_directories(mgfilt PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(mgfilt mgf rtrad ${PLATFORM_MATH_LIB})

add_executable(mgf2inv mgf2inv.c)
target_include_directories(mgf2inv
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(mgf2inv mgf rtrad ${PLATFORM_MATH_LIB})

add_executable(3ds2mgf 3ds2mgf.c rayopt3ds.c vect3ds.c)
target_include_directories(3ds2mgf
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(3ds2mgf rtrad ${PLATFORM_MATH_LIB})

add_executable(pabopto2bsdf pabopto2bsdf.c bsdfrep.c bsdfrbf.c bsdfmesh.c
                            bsdftrans.cpp)
target_include_directories(pabopto2bsdf
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pabopto2bsdf rtrad ${PLATFORM_MATH_LIB})

# add_executable(pabopto2rad pabopto2bsdf.c bsdfrep.c bsdfrbf.c bsdfmesh.c
# bsdftrans.cpp) target_include_directories(pabopto2rad PRIVATE
# ${CMAKE_CURRENT_SOURCE_DIR}/../common) target_link_libraries(pabopto2rad rtrad
# ${PLATFORM_MATH_LIB}) set_target_properties(pabopto2rad PROPERTIES
# COMPILE_DEFINITIONS TEST_MAIN)

add_executable(bsdf2rad bsdf2rad.c bsdfrep.c bsdfinterp.c)
target_include_directories(bsdf2rad
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(bsdf2rad rtrad ${PLATFORM_MATH_LIB})

add_executable(bsdfquery bsdfquery.c bsdfrep.c bsdfinterp.c)
target_include_directories(bsdfquery
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(bsdfquery rtrad ${PLATFORM_MATH_LIB})

add_executable(bsdf2ttree bsdf2ttree.c bsdfrep.c bsdfinterp.c)
target_include_directories(bsdf2ttree
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(bsdf2ttree rtrad ${PLATFORM_MATH_LIB})

add_executable(bsdf2klems bsdf2klems.c bsdfrep.c bsdfinterp.c)
target_include_directories(bsdf2klems
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(bsdf2klems rtrad ${PLATFORM_MATH_LIB})

add_executable(pkgBSDF pkgBSDF.c trans.c)
target_include_directories(pkgBSDF
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pkgBSDF rtrad ${PLATFORM_MATH_LIB})

add_executable(checkBSDF checkBSDF.c)
target_include_directories(checkBSDF
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(checkBSDF rtrad ${PLATFORM_MATH_LIB})

add_executable(epw2wea epw2wea.c)

install(
  TARGETS 3ds2mgf
          bsdf2klems
          bsdf2rad
          bsdf2ttree
          checkBSDF
          epw2wea
          ies2rad
          lampcolor
          mgf2inv
          mgf2rad
          mgfilt
          nff2rad
          obj2rad
          pkgBSDF
          rad2mgf
          robjutil
          tmesh2rad
          pabopto2bsdf
          # pabopto2rad
  DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/bin)

file(COPY bsdf2rad.cal lamp.tab source.cal tilt.cal window.cal
     DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/lib)
