/*
 * SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef IDATA_MODEL_STORAGE_HPP
#define IDATA_MODEL_STORAGE_HPP

#include <vector>
#include <string_view>

#include "esp_err.h"

/**
 * @brief Abstract interface for data model storage.
 *
 * This interface exposes methods to get, set, and remove data model binary blobs.
 */
class IDataModelStorage {
public:
    virtual ~IDataModelStorage() {}

    /**
     * @brief Retrieve the data model binary associated with the given key.
     *
     * The binary is returned in the provided vector. If the key is not found,
     * the vector will be left empty.
     *
     * @param key Key name as a std::string_view.
     * @param data Output vector that will be filled with the binary data.
     * @return ESP_OK on success or an error code on failure.
     */
    virtual esp_err_t get_data_model(std::string_view key, std::vector<uint8_t> &data) = 0;

    /**
     * @brief Store the given data model binary under the specified key.
     *
     * @param key Key name as a std::string_view.
     * @param data The binary data to store.
     * @return ESP_OK on success or an error code on failure.
     */
    virtual esp_err_t set_data_model(std::string_view key, const std::vector<uint8_t> &data) = 0;

    /**
     * @brief Remove the data model associated with the given key.
     *
     * @param key Key name as a std::string_view.
     * @return ESP_OK on success or an error code on failure.
     */
    virtual esp_err_t remove_key(std::string_view key) = 0;
};

#endif // IDATA_MODEL_STORAGE_HPP
