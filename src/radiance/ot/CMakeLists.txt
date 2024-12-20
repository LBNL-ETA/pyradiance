add_executable(getbbox
  bbox.c
  getbbox.c
  init2otypes.c
  readobj2.c
)
target_include_directories(getbbox PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(getbbox PRIVATE rtrad m)

add_executable(obj2mesh
  cvmesh.c
  o_face.c
  obj2mesh.c
  wfconv.c
  writemesh.c
)
target_include_directories(obj2mesh PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(obj2mesh PRIVATE rtrad m)

add_executable(oconv
  bbox.c
  initotypes.c
  o_cone.c
  o_face.c
  o_instance.c
  oconv.c
  sphere.c
  writeoct.c
)
target_include_directories(oconv PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(oconv PRIVATE rtrad m)

install(TARGETS getbbox obj2mesh oconv
  DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/bin
)
