/*
 * SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include "nvs_data_model_storage.hpp"
#include "nvs_handle.hpp"
#include "nvs_flash.h"
#include "esp_log.h"
#include <memory>
#include <string.h>

static const char *TAG = "NVSDataModelStorage";

NVSDataModelStorage::NVSDataModelStorage() : nvs_partition_name("esp_matter_dm"), nvs_namespace("em_data_model")
{
    // Initialize the NVS partition for the data model.
    esp_err_t err = nvs_flash_init_partition(nvs_partition_name);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize NVS partition '%s': %d", nvs_partition_name, err);
    }
}

NVSDataModelStorage::~NVSDataModelStorage()
{
    // No explicit cleanup needed.
}

esp_err_t NVSDataModelStorage::get_data_model(std::string_view key, std::vector<uint8_t> &data)
{
    esp_err_t err;
    // Open the NVS "em_data_model" namespace from the "esp_matter_dm" partition.
    std::unique_ptr<nvs::NVSHandle> handle = nvs::open_nvs_handle_from_partition(nvs_partition_name, nvs_namespace, NVS_READWRITE, &err);
    if (!handle || err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to open NVS handle from partition '%s'", nvs_partition_name);
        return err;
    }

    // Get the size of the blob.
    size_t size = 0;
    err = handle->get_item_size(nvs::ItemType::BLOB_DATA, key.data(), size);
    if (err == ESP_ERR_NVS_NOT_FOUND) {
        data.clear();
        return ESP_ERR_NVS_NOT_FOUND;
    } else if (err != ESP_OK) {
        return err;
    }

    // Resize vector and read blob.
    data.resize(size);
    err = handle->get_blob(key.data(), data.data(), size);
    if (err != ESP_OK) {
        data.clear();
        return err;
    }
    return ESP_OK;
}

esp_err_t NVSDataModelStorage::set_data_model(std::string_view key, const std::vector<uint8_t> &data)
{
    esp_err_t err;
    std::unique_ptr<nvs::NVSHandle> handle = nvs::open_nvs_handle_from_partition(nvs_partition_name, nvs_namespace, NVS_READWRITE, &err);
    if (!handle || err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to open NVS handle from partition '%s'", nvs_partition_name);
        return err;
    }

    err = handle->set_blob(key.data(), data.data(), data.size());
    if (err != ESP_OK) {
        return err;
    }

    err = handle->commit();
    return err;
}

esp_err_t NVSDataModelStorage::remove_key(std::string_view key)
{
    esp_err_t err;
    std::unique_ptr<nvs::NVSHandle> handle = nvs::open_nvs_handle_from_partition(nvs_partition_name, nvs_namespace, NVS_READWRITE, &err);
    if (!handle || err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to open NVS handle from partition '%s'", nvs_partition_name);
        return err;
    }

    err = handle->erase_item(key.data());
    if (err != ESP_OK) {
        return err;
    }

    err = handle->commit();
    return err;
}
