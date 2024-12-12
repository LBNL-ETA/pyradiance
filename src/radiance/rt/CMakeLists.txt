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
    renderopts.c
)

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
    o_mesh.c
)

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
    ashikhmin.c
)

set(MODOBJS
    p_func.c
    t_func.c
    p_data.c
    t_data.c
    text.c
    mx_func.c
    mx_data.c
)

set(SUPPOBJS
    func.c
    noise3.c
)

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
    pmcontrib2.c
)

# Combine all objects for radiance library
set(ROBJS
    ${RAYOBJS}
    ${SURFOBJS}
    ${MATOBJS}
    ${MODOBJS}
    ${SUPPOBJS}
    ${PMOBJS}
    Version.c
)

# Define source files for raycalls library
set(RLOBJS
    raycalls.c
    raypcalls.c
    rayfifo.c
)

file(COPY rayinit.cal
  DESTINATION ${PYTHON_INSTALL_DIR}/pyradiance/lib
)


# Create libraries
add_library(radiance STATIC ${ROBJS})
set_target_properties(radiance PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)

add_library(raycalls STATIC ${RLOBJS})
set_target_properties(raycalls PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)
