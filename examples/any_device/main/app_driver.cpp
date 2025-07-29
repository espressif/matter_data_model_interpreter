/*
 * SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Unlicense OR CC0-1.0
 */
#include <esp_log.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

#include <esp_matter.h>

#include <app_priv.h>

using namespace chip::app::Clusters;
using namespace esp_matter;

static const char *TAG = "app_driver";

esp_err_t app_driver_attribute_update(app_driver_handle_t driver_handle, uint16_t endpoint_id, uint32_t cluster_id,
                                      uint32_t attribute_id, esp_matter_attr_val_t *val)
{
    esp_err_t err = ESP_OK;

    ESP_LOGI(TAG, "Endpoint ID: %" PRIu16 ", Cluster ID: %" PRIu32 ", Attribute ID: %" PRIu32, endpoint_id, cluster_id, attribute_id);

    switch (val->type) {
    case ESP_MATTER_VAL_TYPE_BOOLEAN:
    case ESP_MATTER_VAL_TYPE_NULLABLE_BOOLEAN:
        ESP_LOGI(TAG, "Attribute Value (Boolean): %s", val->val.b ? "true" : "false");
        break;
    case ESP_MATTER_VAL_TYPE_INTEGER:
    case ESP_MATTER_VAL_TYPE_NULLABLE_INTEGER:
        ESP_LOGI(TAG, "Attribute Value (Integer): %d", val->val.i);
        break;
    case ESP_MATTER_VAL_TYPE_FLOAT:
    case ESP_MATTER_VAL_TYPE_NULLABLE_FLOAT:
        ESP_LOGI(TAG, "Attribute Value (Float): %f", val->val.f);
        break;
    case ESP_MATTER_VAL_TYPE_INT8:
    case ESP_MATTER_VAL_TYPE_NULLABLE_INT8:
        ESP_LOGI(TAG, "Attribute Value (Int8): %" PRId8, val->val.i8);
        break;
    case ESP_MATTER_VAL_TYPE_UINT8:
    case ESP_MATTER_VAL_TYPE_NULLABLE_UINT8:
        ESP_LOGI(TAG, "Attribute Value (UInt8): %" PRIu8, val->val.u8);
        break;
    case ESP_MATTER_VAL_TYPE_INT16:
    case ESP_MATTER_VAL_TYPE_NULLABLE_INT16:
        ESP_LOGI(TAG, "Attribute Value (Int16): %" PRId16, val->val.i16);
        break;
    case ESP_MATTER_VAL_TYPE_UINT16:
    case ESP_MATTER_VAL_TYPE_NULLABLE_UINT16:
        ESP_LOGI(TAG, "Attribute Value (UInt16): %" PRIu16, val->val.u16);
        break;
    case ESP_MATTER_VAL_TYPE_INT32:
    case ESP_MATTER_VAL_TYPE_NULLABLE_INT32:
        ESP_LOGI(TAG, "Attribute Value (Int32): %" PRId32, val->val.i32);
        break;
    case ESP_MATTER_VAL_TYPE_UINT32:
    case ESP_MATTER_VAL_TYPE_NULLABLE_UINT32:
        ESP_LOGI(TAG, "Attribute Value (UInt32): %" PRIu32, val->val.u32);
        break;
    case ESP_MATTER_VAL_TYPE_INT64:
    case ESP_MATTER_VAL_TYPE_NULLABLE_INT64:
        ESP_LOGI(TAG, "Attribute Value (Int64): %" PRId64, val->val.i64);
        break;
    case ESP_MATTER_VAL_TYPE_UINT64:
    case ESP_MATTER_VAL_TYPE_NULLABLE_UINT64:
        ESP_LOGI(TAG, "Attribute Value (UInt64): %" PRIu64, val->val.u64);
        break;
    case ESP_MATTER_VAL_TYPE_CHAR_STRING:
    case ESP_MATTER_VAL_TYPE_LONG_CHAR_STRING:
        ESP_LOGI(TAG, "Attribute Value (Char String): %s", (char *)val->val.p);
        break;
    case ESP_MATTER_VAL_TYPE_OCTET_STRING:
    case ESP_MATTER_VAL_TYPE_LONG_OCTET_STRING:
        ESP_LOG_BUFFER_HEX_LEVEL(TAG, val->val.a.b, val->val.a.s, ESP_LOG_INFO);
        break;
    default:
        ESP_LOGI(TAG, "Attribute Value: Unsupported type");
        break;
    }

    return err;
}
