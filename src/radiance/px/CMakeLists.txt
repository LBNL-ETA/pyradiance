add_executable(pfilt pf2.c pf3.c pfilt.c)
target_include_directories(pfilt PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pfilt rtrad ${PLATFORM_MATH_LIB})

add_executable(pcond pcond.c pcond2.c pcond3.c pcond4.c warp3d.c)
target_include_directories(pcond PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pcond rtrad ${PLATFORM_MATH_LIB})

add_executable(pcwarp pcwarp.c warp3d.c)
target_include_directories(pcwarp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pcwarp rtrad ${PLATFORM_MATH_LIB})

add_executable(ttyimage ttyimage.c)
target_include_directories(ttyimage PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ttyimage rtrad ${PLATFORM_MATH_LIB})

add_executable(pvalue pvalue.c)
target_include_directories(pvalue PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pvalue rtrad ${PLATFORM_MATH_LIB})

add_executable(pcompos pcompos.c)
target_include_directories(pcompos PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pcompos rtrad ${PLATFORM_MATH_LIB})

add_executable(psign psign.c)
target_include_directories(psign PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(psign rtrad ${PLATFORM_MATH_LIB})

add_executable(ra_gif ra_gif.c clrtab.c neuclrtab.c)
target_include_directories(ra_gif PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_gif rtrad ${PLATFORM_MATH_LIB})

add_executable(ra_ps ra_ps.c)
target_include_directories(ra_ps PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_ps rtrad ${PLATFORM_MATH_LIB})

add_executable(ra_ppm ra_ppm.c)
target_include_directories(ra_ppm PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_ppm rtrad ${PLATFORM_MATH_LIB})

add_executable(ra_bmp ra_bmp.c)
target_include_directories(ra_bmp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_bmp rtrad ${PLATFORM_MATH_LIB})

add_executable(ra_t8 ra_t8.c clrtab.c neuclrtab.c)
target_include_directories(ra_t8 PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_t8 rtrad ${PLATFORM_MATH_LIB})

add_executable(ra_t16 ra_t16.c)
target_include_directories(ra_t16 PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_t16 rtrad ${PLATFORM_MATH_LIB})

add_executable(ra_rgbe ra_rgbe.c)
target_include_directories(ra_rgbe PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_rgbe rtrad ${PLATFORM_MATH_LIB})

add_executable(ra_pict ra_pict.c)
target_include_directories(ra_pict PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_pict rtrad ${PLATFORM_MATH_LIB})

add_executable(ra_hexbit ra_hexbit.c)
target_include_directories(ra_hexbit PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_hexbit rtrad ${PLATFORM_MATH_LIB})

add_executable(pflip pflip.c)
target_include_directories(pflip PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pflip rtrad ${PLATFORM_MATH_LIB})

add_executable(protate protate.c)
target_include_directories(protate PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(protate rtrad ${PLATFORM_MATH_LIB})

add_executable(pextrem pextrem.c)
target_include_directories(pextrem PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pextrem rtrad ${PLATFORM_MATH_LIB})

add_executable(pcomb pcomb.c)
target_include_directories(pcomb PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pcomb rtrad ${PLATFORM_MATH_LIB})

add_executable(pinterp pinterp.c)
target_include_directories(pinterp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pinterp rtrad ${PLATFORM_MATH_LIB})

add_executable(ra_xyze ra_xyze.c)
target_include_directories(ra_xyze PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_xyze rtrad ${PLATFORM_MATH_LIB})

add_executable(macbethcal macbethcal.c pmapgen.c mx3.c warp3d.c)
target_include_directories(macbethcal PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(macbethcal rtrad ${PLATFORM_MATH_LIB})

add_executable(pmblur2 pmblur2.c)
target_include_directories(pmblur2 PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pmblur2 rtrad ${PLATFORM_MATH_LIB})

add_executable(psketch psketch.c)
target_include_directories(psketch PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(psketch rtrad ${PLATFORM_MATH_LIB})

add_executable(ra_tiff ra_tiff.c)
target_include_directories(ra_tiff PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common ${libtiff_SOURCE_DIR}/libtiff)
target_link_libraries(ra_tiff 
    PRIVATE 
    rtrad
    tiff
    ${PLATFORM_MATH_LIB}
)

add_executable(normtiff normtiff.c)
target_include_directories(normtiff PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common ${libtiff_SOURCE_DIR}/libtiff)
target_link_libraries(normtiff rtrad tiff ${PLATFORM_MATH_LIB})


# Force static linking on non-Windows platforms
# if(NOT WIN32)
#     set_target_properties(ra_tiff PROPERTIES LINK_FLAGS "-static")
#     set_target_properties(normtiff PROPERTIES LINK_FLAGS "-static")
# endif()

install(TARGETS
  macbethcal
  pcomb
  pcompos
  pcond
  pcwarp
  pextrem
  pfilt
  pflip
  pinterp
  pmblur2
  protate
  psign
  psketch
  pvalue
  ra_bmp
  ra_gif
  ra_hexbit
  ra_pict
  ra_ppm
  ra_tiff
  normtiff
  ra_ps
  ra_rgbe
  ra_t16
  ra_t8
  ra_xyze
  ttyimage
  DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/bin
)
