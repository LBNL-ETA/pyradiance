add_executable(cnt cnt.c)
target_include_directories(cnt PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(cnt PRIVATE rtrad ${PLATFORM_MATH_LIB})

add_executable(ev ev.c)
target_include_directories(ev PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(ev PRIVATE rtrad ${PLATFORM_MATH_LIB})

add_executable(histo histo.c)
target_include_directories(histo PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(histo PRIVATE ${PLATFORM_MATH_LIB})

add_executable(icalc calc.c)
target_include_directories(icalc PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(icalc PRIVATE rtrad ${PLATFORM_MATH_LIB})

add_executable(neaten neat.c)

add_executable(rcalc rcalc.c)
target_include_directories(rcalc PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rcalc PRIVATE rtrad ${PLATFORM_MATH_LIB})

add_executable(rlam lam.c)
target_include_directories(rlam PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rlam PRIVATE rtrad ${PLATFORM_MATH_LIB})

add_executable(rsplit rsplit.c)
target_include_directories(rsplit PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(rsplit PRIVATE rtrad ${PLATFORM_MATH_LIB})

add_executable(tabfunc tabfunc.c)
target_include_directories(tabfunc PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(tabfunc PRIVATE rtrad ${PLATFORM_MATH_LIB})

add_executable(total total.c)
target_include_directories(total PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../common)
target_link_libraries(total PRIVATE rtrad ${PLATFORM_MATH_LIB})

install(TARGETS
  cnt
  ev
  histo
  icalc
  neaten
  rcalc
  rlam
  rsplit
  tabfunc
  total
  DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/bin
)

file(GLOB_RECURSE cal_files "cal/*.*")
file(COPY ${cal_files}
  DESTINATION ${SKBUILD_PLATLIB_DIR}/pyradiance/lib
)
