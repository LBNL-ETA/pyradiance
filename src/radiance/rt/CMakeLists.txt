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
    m_wgmdf.c
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
target_link_libraries(rtrace raycalls radiance rtrad ${PLATFORM_MATH_LIB})

add_executable(rpict rpmain.c rpict.c srcdraw.c duphead.c persist.c)
target_include_directories(rpict PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rpict radiance rtrad ${PLATFORM_MATH_LIB})

add_executable(lookamb lookamb.c ambio.c)
target_include_directories(lookamb
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(lookamb rtrad ${PLATFORM_MATH_LIB})

add_executable(rcontrib rcmain.c rcontrib.c rc2.c rc3.c)
target_include_directories(rcontrib
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rcontrib radiance rtrad ${PLATFORM_MATH_LIB})
if(WIN32)
  target_link_libraries(rcontrib ws2_32)
endif()

add_executable(mkpmap mkpmap.c)
target_include_directories(mkpmap PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(mkpmap radiance rtrad ${PLATFORM_MATH_LIB})

add_executable(pmapdump pmapdump.c pmaptype.c pmapparm.c)
target_include_directories(pmapdump
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pmapdump raycalls radiance rtrad ${PLATFORM_MATH_LIB})

install(TARGETS rtrace rpict lookamb rcontrib mkpmap pmapdump
        DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/bin)
