# generate_version.cmake
# This script expects VERSION_FILE and OUTPUT_FILE to be defined

# Read the version content and remove newlines
file(READ "${VERSION_FILE}" VERSION_CONTENT)
string(STRIP "${VERSION_CONTENT}" VERSION_CONTENT)

# Get the date, user, and hostname
execute_process(
    COMMAND date
    OUTPUT_VARIABLE DATE_STR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
execute_process(
    COMMAND whoami
    OUTPUT_VARIABLE USER_STR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
execute_process(
    COMMAND hostname
    OUTPUT_VARIABLE HOST_STR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Create the version string all on one line
set(VERSION_STRING "${VERSION_CONTENT} lastmod ${DATE_STR} by ${USER_STR} on ${HOST_STR}")

# Write the Version.c file
file(WRITE "${OUTPUT_FILE}"
"/*
 * This file was created automatically during build.
 */
char VersionID[]=\"${VERSION_STRING}\";\n")
