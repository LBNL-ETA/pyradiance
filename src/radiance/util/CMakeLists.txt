add_executable(evalglare evalglare.c pictool.c)
target_include_directories(evalglare PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(evalglare PRIVATE rtrad reetz m)

add_executable(dctimestep dctimestep.c cmbsdf.c cmatrix.c)
target_include_directories(dctimestep PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(dctimestep PRIVATE rtrad m)

add_executable(getinfo getinfo.c)
target_include_directories(getinfo PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(getinfo PRIVATE rtrad m)

add_executable(rad rad.c)
target_include_directories(rad PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rad PRIVATE radiance rtrad m)

add_executable(vwrays vwrays.c)
target_include_directories(vwrays PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(vwrays PRIVATE rtrad m)

add_executable(rttree_reduce rttree_reduce.c)
target_include_directories(rttree_reduce PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rttree_reduce rtrad)

add_executable(rmtxop rmtxop.c rmatrix.c cmbsdf.c cmatrix.c)
target_include_directories(rmtxop PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rmtxop PRIVATE rtrad m)

add_executable(rcomb rcomb.c rmatrix.c cmbsdf.c cmatrix.c)
target_include_directories(rcomb PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rcomb PRIVATE radiance rtrad m)

add_executable(wrapBSDF wrapBSDF.c)
target_include_directories(wrapBSDF PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(wrapBSDF rtrad m)

add_executable(rfluxmtx rfluxmtx.c)
target_include_directories(rfluxmtx PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rfluxmtx PRIVATE rtrad m)

install(FILES
  ambpos.cal
  disk2square.cal
  hsv_rgb.cal
  klems_full.cal
  klems_half.cal
  klems_quarter.cal
  minimalBSDFt.xml
  rambpos.cal
  reinhartb.cal
  tregsamp.dat
  WINDOW6BSDFt.xml
  DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/lib
)

install(TARGETS
  evalglare
  dctimestep
  getinfo
  rad
  rcomb
  rfluxmtx
  rmtxop
  rttree_reduce
  vwrays
  wrapBSDF
  DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/bin
)
