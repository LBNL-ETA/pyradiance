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

# Create libraries
add_library(radiance STATIC ${ROBJS})
set_target_properties(radiance PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)

add_library(raycalls STATIC ${RLOBJS})
set_target_properties(raycalls PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)
