

add_executable(genbeads genbeads.c hermite3.c)
target_link_libraries(genbeads PRIVATE ${MATH_LIBRARY})

add_executable(genbox genbox.c)
target_include_directories(genbox PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(genbox wfobj rtrad ${MATH_LIBRARY})

add_executable(genmarble genmarble.c ../common/random.h)
target_include_directories(genmarble PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(genmarble PRIVATE ${MATH_LIBRARY})

add_executable(gensky gensky.c sun.c)
target_include_directories(gensky PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(gensky PRIVATE rtrad ${MATH_LIBRARY})

add_executable(genssky genssky.c sun.c atmos.c)
target_include_directories(genssky PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common ${CMAKE_CURRENT_SOURCE_DIR}/../rt)
target_link_libraries(genssky rtrad ${MATH_LIBRARY} Threads::Threads)

add_executable(gensdaymtx gensdaymtx.c sun.c atmos.c)
target_include_directories(gensdaymtx PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common ${CMAKE_CURRENT_SOURCE_DIR}/../rt)
target_link_libraries(gensdaymtx rtrad ${MATH_LIBRARY} Threads::Threads)

add_executable(gendaylit gendaylit.c sun.c)
target_include_directories(gendaylit PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(gendaylit PRIVATE rtrad ${MATH_LIBRARY})

add_executable(gendaymtx gendaymtx.c sun.c)
target_include_directories(gendaymtx PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(gendaymtx PRIVATE rtrad ${MATH_LIBRARY})

add_executable(genblinds genblinds.c)
target_include_directories(genblinds PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(genblinds PRIVATE rtrad ${MATH_LIBRARY})

add_executable(genprism genprism.c)
target_include_directories(genprism PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(genprism PRIVATE rtrad ${MATH_LIBRARY})

add_executable(xform xform.c)
target_include_directories(xform PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(xform PRIVATE rtrad ${MATH_LIBRARY})

add_executable(replmarks replmarks.c)
target_include_directories(replmarks PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(replmarks PRIVATE rtrad ${MATH_LIBRARY})

add_executable(mkillum mkillum.c mkillum2.c mkillum3.c)
target_include_directories(mkillum PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common ${CMAKE_CURRENT_SOURCE_DIR}/../rt)
target_link_libraries(mkillum PRIVATE raycalls radiance rtrad ${MATH_LIBRARY})

add_executable(mksource mksource.c)
target_include_directories(mksource PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common ${CMAKE_CURRENT_SOURCE_DIR}/../rt)
target_link_libraries(mksource PRIVATE raycalls radiance rtrad ${MATH_LIBRARY})

add_executable(genrev genrev.c)
target_include_directories(genrev PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(genrev PRIVATE rtrad ${MATH_LIBRARY})

add_executable(gencatenary gencat.c)
target_include_directories(gencatenary PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(gencatenary PRIVATE rtrad ${MATH_LIBRARY})

add_executable(genworm genworm.c)
target_include_directories(genworm PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(genworm PRIVATE rtrad ${MATH_LIBRARY})

add_executable(gensurf gensurf.c)
target_include_directories(gensurf PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(gensurf PRIVATE rtrad ${MATH_LIBRARY})

add_executable(genclock genclock.c)
target_include_directories(genclock PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(genclock PRIVATE ${MATH_LIBRARY})

add_executable(genbranch genbranch.c)
target_include_directories(genbranch PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(genbranch PRIVATE ${MATH_LIBRARY})

install(TARGETS
  genblinds
  genbox
  genclock
  gendaylit
  gendaymtx
  gensdaymtx
  genprism
  genrev
  gensky
  genssky
  gensurf
  genworm
  mkillum
  mksource
  replmarks
  xform
  DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/bin
)

install(FILES
  glaze1.cal
  glaze2.cal
  illum.cal
  perezlum.cal
  perezlum_c.cal
  rev.cal
  skybright.cal
  surf.cal
  mie_ca.dat
  DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/lib
)
