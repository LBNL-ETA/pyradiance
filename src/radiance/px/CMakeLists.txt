add_executable(pfilt pf2.c pf3.c pfilt.c)
target_include_directories(pfilt PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pfilt rtrad m)

add_executable(pcond pcond.c pcond2.c pcond3.c pcond4.c warp3d.c)
target_include_directories(pcond PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pcond rtrad m)

add_executable(pcwarp pcwarp.c warp3d.c)
target_include_directories(pcwarp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pcwarp rtrad m)

add_executable(ttyimage ttyimage.c)
target_include_directories(ttyimage PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ttyimage rtrad m)

add_executable(pvalue pvalue.c)
target_include_directories(pvalue PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pvalue rtrad m)

add_executable(pcompos pcompos.c)
target_include_directories(pcompos PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pcompos rtrad m)

add_executable(psign psign.c)
target_include_directories(psign PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(psign rtrad m)

add_executable(ra_gif ra_gif.c clrtab.c neuclrtab.c)
target_include_directories(ra_gif PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_gif rtrad m)

add_executable(ra_ps ra_ps.c)
target_include_directories(ra_ps PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_ps rtrad m)

add_executable(ra_ppm ra_ppm.c)
target_include_directories(ra_ppm PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_ppm rtrad m)

add_executable(ra_bmp ra_bmp.c)
target_include_directories(ra_bmp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_bmp rtrad m)

add_executable(ra_t8 ra_t8.c clrtab.c neuclrtab.c)
target_include_directories(ra_t8 PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_t8 rtrad m)

add_executable(ra_t16 ra_t16.c)
target_include_directories(ra_t16 PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_t16 rtrad m)

add_executable(ra_rgbe ra_rgbe.c)
target_include_directories(ra_rgbe PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_rgbe rtrad m)

add_executable(ra_pict ra_pict.c)
target_include_directories(ra_pict PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_pict rtrad m)

add_executable(ra_hexbit ra_hexbit.c)
target_include_directories(ra_hexbit PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_hexbit rtrad m)

add_executable(pflip pflip.c)
target_include_directories(pflip PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pflip rtrad m)

add_executable(protate protate.c)
target_include_directories(protate PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(protate rtrad m)

add_executable(pextrem pextrem.c)
target_include_directories(pextrem PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pextrem rtrad m)

add_executable(pcomb pcomb.c)
target_include_directories(pcomb PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pcomb rtrad m)

add_executable(pinterp pinterp.c)
target_include_directories(pinterp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pinterp rtrad m)

add_executable(ra_xyze ra_xyze.c)
target_include_directories(ra_xyze PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ra_xyze rtrad m)

add_executable(macbethcal macbethcal.c pmapgen.c mx3.c warp3d.c)
target_include_directories(macbethcal PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(macbethcal rtrad m)

add_executable(pmblur2 pmblur2.c)
target_include_directories(pmblur2 PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(pmblur2 rtrad m)

add_executable(psketch psketch.c)
target_include_directories(psketch PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(psketch rtrad m)

include(FetchContent)

# Set global static linking preferences
set(BUILD_SHARED_LIBS OFF CACHE BOOL "Build static libraries" FORCE)
set(CMAKE_FIND_LIBRARY_SUFFIXES ".a")
set(BUILD_SHARED_LIBS OFF)

set(ZLIB_SUPPORT OFF CACHE BOOL "Enable Zlib usage" FORCE)
set(JPEG_SUPPORT OFF CACHE BOOL "Enable JPEG compression" FORCE)
set(OJPEG_SUPPORT OFF CACHE BOOL "Enable old-style JPEG compression" FORCE)
set(JBIG_SUPPORT OFF CACHE BOOL "Enable JBIG compression" FORCE)
set(WEBP_SUPPORT OFF CACHE BOOL "Enable WebP compression" FORCE)
set(ZSTD_SUPPORT OFF CACHE BOOL "Enable ZSTD compression" FORCE)
set(DEFLATE_SUPPORT OFF CACHE BOOL "Enable DEFLATE compression" FORCE)

# Declare libtiff
FetchContent_Declare(
    libtiff
    GIT_REPOSITORY https://gitlab.com/libtiff/libtiff.git
    GIT_TAG v4.7.0  # Specify the version you want
)

# Configure libtiff build options
set(BUILD_SHARED_LIBS OFF CACHE BOOL "Build static libraries" FORCE)
set(tiff-tools OFF CACHE BOOL "Build TIFF tools" FORCE)
set(tiff-tests OFF CACHE BOOL "Build TIFF tests" FORCE)
set(tiff-docs OFF CACHE BOOL "Build TIFF documentation" FORCE)
set(tiff-contrib OFF CACHE BOOL "Build TIFF contrib" FORCE)
set(tiff-install OFF CACHE BOOL "Install TIFF files" FORCE)

# Fetch and make libtiff available
FetchContent_MakeAvailable(libtiff)


add_executable(ra_tiff ra_tiff.c)
target_include_directories(ra_tiff PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common ${libtiff_SOURCE_DIR}/libtiff)
target_link_libraries(ra_tiff 
    PRIVATE 
    rtrad
    -static    # Force static linking
    tiff
    m
)

add_executable(normtiff normtiff.c)
target_include_directories(normtiff PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common ${libtiff_SOURCE_DIR}/libtiff)
target_link_libraries(normtiff rtrad tiff m)


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
