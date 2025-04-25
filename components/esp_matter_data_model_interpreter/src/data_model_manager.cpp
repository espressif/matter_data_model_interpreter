/*
 * SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include "data_model_manager.hpp"
#include "data_model_storage.hpp"
#include "esp_log.h"
#include "esp_ota_ops.h"
#include <cstdio>
#include <vector>

static const char *TAG = "DataModelManager";

namespace data_model_manager {

DataModelManager::DataModelManager(IDataModelStorage &storage)
    : storage_(storage)
{
}

DataModelManager::~DataModelManager() { }

std::vector<uint8_t> DataModelManager::get_data_model_binary(size_t &data_model_binary_size)
{
    esp_err_t err;
    std::vector<uint8_t> data_model_binary;

    // Retrieve the running partition info using the OTA API.
    const esp_partition_t *running_partition = esp_ota_get_running_partition();
    if (!running_partition) {
        ESP_LOGE(TAG, "Failed to get running partition");
        data_model_binary_size = 0;
        return data_model_binary;  // Return empty vector on error.
    }

    // Construct the key using the partition label (e.g., "ota_0_dm" if partition label is "ota_0").
    char key[32] = {0};
    snprintf(key, sizeof(key), "%s_dm", running_partition->label);
    ESP_LOGD(TAG, "Looking for key: '%s'", key);

    // Attempt to retrieve the binary blob using the constructed key.
    err = storage_.get_data_model(key, data_model_binary);
    if (err != ESP_OK || data_model_binary.empty()) {
        ESP_LOGW(TAG, "Key '%s' not found; trying fallback key 'ota_0_dm'", key);
        data_model_binary.clear();
        err = storage_.get_data_model("ota_0_dm", data_model_binary);
        if (err != ESP_OK || data_model_binary.empty()) {
            ESP_LOGE(TAG, "Fallback key 'ota_0_dm' not found");
            data_model_binary.clear();
            data_model_binary_size = 0;
            return data_model_binary;
        }
        // Promote 'ota_0_dm' data model to current partition's key.
        err = storage_.set_data_model(key, data_model_binary);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Failed to write data model binary blob to new key '%s'", key);
            data_model_binary.clear();
            data_model_binary_size = 0;
            return data_model_binary;
        }
        // Remove stale 'ota_0_dm' data model.
        err = storage_.remove_key("ota_0_dm");
        if (err != ESP_OK) {
            ESP_LOGW(TAG, "Failed to erase fallback key 'ota_0_dm'");
        }
        ESP_LOGI(TAG, "Successfully renamed fallback key to '%s'", key);
    }
    data_model_binary_size = data_model_binary.size();
    return data_model_binary;
}

} // namespace data_model_manager
