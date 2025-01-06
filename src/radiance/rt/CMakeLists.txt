function(generate_version_file OUTPUT_FILE VERSION_FILE)

  configure_file(${VERSION_FILE} ${CMAKE_CURRENT_BINARY_DIR}/RADVERSION
                 COPYONLY)

  add_custom_command(
    OUTPUT ${OUTPUT_FILE}
    COMMAND
      ${CMAKE_COMMAND} -D VERSION_FILE=${CMAKE_CURRENT_BINARY_DIR}/RADVERSION -D
      OUTPUT_FILE=${OUTPUT_FILE} -P
      ${CMAKE_CURRENT_SOURCE_DIR}/generate_version.cmake
    DEPENDS ${VERSION_FILE} ${CMAKE_CURRENT_SOURCE_DIR}/generate_version.cmake
    COMMENT "Generating Version.c"
    VERBATIM)
endfunction()

# generate version.c
set(VERSION_FILE "${CMAKE_CURRENT_SOURCE_DIR}/VERSION")
set(VERSION_C "${CMAKE_CURRENT_SOURCE_DIR}/Version.c")
generate_version_file(${VERSION_C} ${VERSION_FILE})

set(RAYOBJS
    ambcomp.c
    ambient.c
    ambio.c
    freeobjmem.c
    initotypes.c
    preload.c
    raytrace.c
    renderopts.c)

set(SURFOBJS
    source.c
    sphere.c
    srcobstr.c
    srcsupp.c
    srcsamp.c
    virtuals.c
    o_face.c
    o_cone.c
    o_instance.c
    o_mesh.c)

set(MATOBJS
    aniso.c
    normal.c
    dielectric.c
    m_clip.c
    glass.c
    m_brdf.c
    m_mirror.c
    m_direct.c
    m_mist.c
    fprism.c
    m_alias.c
    m_bsdf.c
    ashikhmin.c)

set(MODOBJS
    p_func.c
    t_func.c
    p_data.c
    t_data.c
    text.c
    mx_func.c
    mx_data.c)

set(SUPPOBJS func.c noise3.c)

set(PMOBJS
    pmap.c
    pmapsrc.c
    pmapmat.c
    pmaprand.c
    pmapio.c
    pmapdata.c
    pmapbias.c
    pmapparm.c
    pmapcontrib.c
    pmapamb.c
    pmapray.c
    pmapopt.c
    pmapdiag.c
    pmaptype.c
    oocmorton.c
    oococt.c
    oocsort.c
    oocbuild.c
    oocnn.c
    ooccache.c
    pmutil.c
    pmcontrib2.c)

# Combine all objects for radiance library
set(ROBJS
    ${RAYOBJS}
    ${SURFOBJS}
    ${MATOBJS}
    ${MODOBJS}
    ${SUPPOBJS}
    ${PMOBJS}
    Version.c)

# Define source files for raycalls library
set(RLOBJS raycalls.c rayfifo.c)

if(WIN32)
  list(APPEND RLOBJS raypwin.c)
else()
  list(APPEND RLOBJS raypcalls.c)
endif()

install(FILES rayinit.cal DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/lib)

# Create libraries
add_library(radiance STATIC ${ROBJS})
set_target_properties(radiance PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(radiance
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)

add_library(raycalls STATIC ${RLOBJS})
set_target_properties(raycalls PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(raycalls
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)

add_executable(rtrace rtmain.c rtrace.c duphead.c persist.c)
target_include_directories(rtrace PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rtrace raycalls radiance rtrad ${MATH_LIBRARY})

add_executable(rpict rpmain.c rpict.c srcdraw.c duphead.c persist.c)
target_include_directories(rpict PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rpict radiance rtrad ${MATH_LIBRARY})

add_executable(lookamb lookamb.c ambio.c)
target_include_directories(lookamb
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(lookamb rtrad ${MATH_LIBRARY})

add_executable(rcontrib rcmain.c rcontrib.c rc2.c rc3.c)
target_include_directories(rcontrib
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rcontrib radiance rtrad ${MATH_LIBRARY})
if (WIN32)
	target_link_libraries(rcontrib ws2_32)
endif()


add_executable(mkpmap mkpmap.c)
target_include_directories(mkpmap PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(mkpmap radiance rtrad ${MATH_LIBRARY})

add_executable(pmapdump pmapdump.c pmaptype.c pmapparm.c)
target_include_directories(pmapdump
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pmapdump raycalls radiance rtrad ${MATH_LIBRARY})

install(TARGETS rtrace rpict lookamb rcontrib mkpmap pmapdump
        DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/bin)
