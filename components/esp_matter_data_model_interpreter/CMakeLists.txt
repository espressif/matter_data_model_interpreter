idf_component_register(
    SRCS "src/esp_matter_data_model_interpreter.cpp"
         "src/data_model_manager.cpp"
         "src/nvs_data_model_storage.cpp"
         "src/generated/esp_matter_data_model_api_messages.pb-c.c"
         "src/generated/cmd_c_routines.cpp"
    INCLUDE_DIRS "include"
    PRIV_INCLUDE_DIRS "src/generated" "src/priv_include"
    REQUIRES protobuf-c esp_matter
)

set_source_files_properties("${COMPONENT_DIR}/src/generated/cmd_c_routines.cpp" PROPERTIES GENERATED TRUE)

idf_build_get_property(python PYTHON)
set(GENERATOR_SCRIPT "${COMPONENT_DIR}/generator_utils/cluster_cmds_gen.py")
set(GENERATED_SRC "${COMPONENT_DIR}/src/generated/cmd_c_routines.cpp")

add_custom_command(
    OUTPUT ${GENERATED_SRC}
    COMMAND ${python} ${GENERATOR_SCRIPT} -o ${GENERATED_SRC}
    DEPENDS ${GENERATOR_SCRIPT}
    COMMENT "Generating cmd_c_routines.cpp"
    VERBATIM
)

add_custom_target(generate_cmd_c_routines ALL DEPENDS ${GENERATED_SRC})
add_dependencies(${COMPONENT_LIB} generate_cmd_c_routines)

get_filename_component(ABS_GENERATED_SRC "${GENERATED_SRC}" ABSOLUTE)
set_property(DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}" APPEND PROPERTY ADDITIONAL_CLEAN_FILES ${ABS_GENERATED_SRC})
