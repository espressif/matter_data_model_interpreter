/*
 * SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef NVS_DATA_MODEL_STORAGE_HPP
#define NVS_DATA_MODEL_STORAGE_HPP

#include <string>
#include <vector>

#include "data_model_storage.hpp"

class NVSDataModelStorage : public IDataModelStorage {
public:
    NVSDataModelStorage();
    virtual ~NVSDataModelStorage();

    virtual esp_err_t get_data_model(std::string_view key, std::vector<uint8_t> &data) override;
    virtual esp_err_t set_data_model(std::string_view key, const std::vector<uint8_t> &data) override;
    virtual esp_err_t remove_key(std::string_view key) override;

private:
    const char *nvs_partition_name, *nvs_namespace;
};

#endif // NVS_DATA_MODEL_STORAGE_HPP
