# Define source file groups
set(RTOBJ
    cone.c face.c 
    # free_os.c 
    instance.c readobj.c readoct.c otypes.c
    objset.c octree.c readfargs.c modobject.c getlibpath.c
    # addobjnotify.c 
    zeroes.c mesh.c readmesh.c tmesh.c sceneio.c
)

set(PICOBJ
    color.c header.c image.c lamps.c resolu.c rexpr.c spec_rgb.c
    colrops.c font.c tonemap.c tmapcolrs.c tmapluv.c tmaptiff.c
    tmap16bit.c bmpfile.c falsecolor.c depthcodec.c normcodec.c
    idmap.c fltdepth.c jitteraperture.c
)

set(UTLOBJ
    ezxml.c ccolor.c ccyrgb.c bsdf.c bsdf_m.c bsdf_t.c loadbsdf.c
    disk2square.c hilbert.c interp2d.c triangulate.c data.c
)

set(STDOBJ
    fgetline.c fropen.c linregr.c xf.c mat4.c invmat4.c fvect.c urand.c
    urind.c calexpr.c caldefn.c calfunc.c calprnt.c biggerlib.c multisamp.c
    unix_process.c process.c gethomedir.c getpath.c error.c savestr.c
    savqstr.c badarg.c fgetword.c words.c expandarg.c wordfile.c fgetval.c
    clip.c plocate.c eputs.c wputs.c quit.c lookup.c bmalloc.c
    # loadvars.c 
    tcos.c fputword.c 
    # chanvalue.c 
    dircode.c paths.c byteswap.c
    cvtcmd.c dmessage.c
)

set(SYSOBJ
    ealloc.c fdate.c portio.c myhostname.c erf.c strcmp.c strlcpy.c
)

set(CPPOBJ
    abitmap.cpp abitmapio.cpp
)

set(MGFOBJ
    mgf_parser.c mgf_object.c mgf_xf.c mgf_context.c
)

set(WFOBJ
    objutil.c objtriangulate.c readwfobj.c convertobj.c writewfobj.c
)

set(REETZOBJ
    g3affine.c g3flist.c g3sphere.c g3vector.c gbasic.c muc_randvar.c
)

# Create libraries
add_library(rtrad STATIC
    ${RTOBJ}
    ${PICOBJ}
    ${UTLOBJ}
    ${STDOBJ}
    ${SYSOBJ}
)

set_target_properties(rtrad PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)

add_library(cpprad STATIC ${CPPOBJ})
add_library(mgf STATIC ${MGFOBJ})
add_library(wfobj STATIC ${WFOBJ})
add_library(reetz STATIC ${REETZOBJ})

set_target_properties(cpprad PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)

# Special compile definitions
target_compile_definitions(rtrad PRIVATE
    DEFPATH=":${CMAKE_INSTALL_PREFIX}/lib/ray"
)
