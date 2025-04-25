/*
 * SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef ESP_MATTER_DATA_MODEL_INTERPRETER_HPP
#define ESP_MATTER_DATA_MODEL_INTERPRETER_HPP

#include <cstddef>
#include <cstdint>
#include <memory>

#include "esp_matter.h"

namespace esp_matter_data_model_interpreter {

/**
 * @brief Interprets the data model binary and creates a Matter node.
 *
 * Internally, it makes the relevant API esp_matter::create* calls
 * to initialise the Matter data model.
 */
class Interpreter {
public:
    Interpreter();
    ~Interpreter();

    /**
     * @brief Interpret the provided data model binary.
     *
     * @param data Pointer to the binary data.
     * @param length Length of the binary data.
     * @return Pointer to the created Matter node, or nullptr on failure.
     */
    esp_matter::node_t* interpret_data(const uint8_t *data, size_t length);

private:
    // Forward declaration of the implementation.
    class Impl;
    std::unique_ptr<Impl> pimpl_;
};

} // namespace esp_matter_data_model_interpreter

#endif // ESP_MATTER_DATA_MODEL_INTERPRETER_HPP
