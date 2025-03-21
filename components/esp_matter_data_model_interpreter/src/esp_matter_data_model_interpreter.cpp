/*
 * SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
 * SPDX-License-Identifier: BSD-2-Clause AND Apache-2.0
 * SPDX-FileContributor: Dave Benson and the protobuf-c authors (for scan_length_prefixed_data)
 */
#include <inttypes.h>

#include "esp_log.h"

#include "cmd_c_routines.h"

#include "esp_matter_data_model_interpreter.hpp"
#include "esp_matter_data_model_api_messages.pb-c.h"

static const char *TAG = "Interpreter";

namespace esp_matter_data_model_interpreter {

class Interpreter::Impl {
public:
    Impl() : current_endpoint(nullptr), current_cluster(nullptr), raw_node(nullptr) {}

    ~Impl() {}

    esp_matter::endpoint_t *current_endpoint;
    esp_matter::cluster_t *current_cluster;
    esp_matter::node_t *raw_node;

    /* Taken from protobuf-c.c, but it was static there, so it had to be copied */
    size_t scan_length_prefixed_data(size_t len, const uint8_t *data, size_t *prefix_len_out)
    {
        unsigned hdr_max = len < 5 ? len : 5;
        unsigned hdr_len;
        size_t val = 0;
        unsigned i;
        unsigned shift = 0;

        for (i = 0; i < hdr_max; i++) {
            val |= ((size_t)data[i] & 0x7f) << shift;
            shift += 7;
            if ((data[i] & 0x80) == 0) {
                break;
            }
        }
        if (i == hdr_max) {
            ESP_LOGE(TAG, "error parsing length for length-prefixed data");
            return 0;
        }
        hdr_len = i + 1;
        *prefix_len_out = hdr_len;
        if (val > INT_MAX) {
            // Protobuf messages should always be less than 2 GiB in size.
            // We also want to return early here so that hdr_len + val does
            // not overflow on 32-bit systems.
            ESP_LOGE(TAG, "length prefix of %lu is too large",
                     (unsigned long int)val);
            return 0;
        }
        if (hdr_len + val > len) {
            ESP_LOGE(TAG, "data too short after length-prefix of %lu",
                     (unsigned long int)val);
            return 0;
        }
        return hdr_len + val;
    }

    esp_err_t handle_function_call(const Datamodel__FunctionCall *message)
    {
        esp_err_t err = ESP_OK;

        switch (message->params_case) {
        case DATAMODEL__FUNCTION_CALL__PARAMS_CREATE_ATTRIBUTE_PARAMS:
            err = create_attribute(message->create_attribute_params);
            break;
        case DATAMODEL__FUNCTION_CALL__PARAMS_CREATE_COMMAND_PARAMS:
            err = create_command(message->create_command_params);
            break;
        case DATAMODEL__FUNCTION_CALL__PARAMS_CREATE_EVENT_PARAMS:
            err = create_event(message->create_event_params);
            break;
        case DATAMODEL__FUNCTION_CALL__PARAMS_CREATE_CLUSTER_PARAMS:
            err = create_cluster(message->create_cluster_params);
            break;
        case DATAMODEL__FUNCTION_CALL__PARAMS_CREATE_ENDPOINT_PARAMS:
            err = create_endpoint(message->create_endpoint_params);
            break;
        case DATAMODEL__FUNCTION_CALL__PARAMS_ENDPOINT_ADD_DEVICE_TYPE_PARAMS:
            err = endpoint_add_device_type(message->endpoint_add_device_type_params);
            break;
        default:
            ESP_LOGE(TAG, "Unknown params");
            err = ESP_ERR_INVALID_ARG;
            break;
        }

        return err;
    }

    esp_err_t create_endpoint(const Datamodel__CreateEndpointParams *params)
    {
        current_endpoint = nullptr;
        current_endpoint = esp_matter::endpoint::create(raw_node, params->flags, nullptr);
        if (current_endpoint == nullptr) {
            ESP_LOGE(TAG, "create_endpoint: Failed to create endpoint with endpoint_id: %" PRIu32, params->endpoint_id);
            return ESP_FAIL;
        } else {
            ESP_LOGD(TAG, "create_endpoint: Created endpoint with id: %" PRIu32, params->endpoint_id);
            return ESP_OK;
        }
    }

    esp_err_t create_cluster(const Datamodel__CreateClusterParams *params)
    {
        current_cluster = nullptr;
        current_cluster = esp_matter::cluster::create(current_endpoint, params->cluster_id, params->flags);
        if (current_cluster == nullptr) {
            ESP_LOGE(TAG, "create_cluster: Failed to create cluster with id: %" PRIu32, params->cluster_id);
            return ESP_FAIL;
        } else {
            ESP_LOGD(TAG, "create_cluster: Created cluster with id: %" PRIu32 " on endpoint", params->cluster_id);
            esp_err_t err = cluster_plugin_init(current_cluster, params->cluster_id);
            if (err != ESP_OK) {
                ESP_LOGE(TAG, "cmd_c_routines: cluster_plugin_init failed for cluster id: %" PRIu32 ", error: %d", params->cluster_id, err);
                return err;
            }
            return ESP_OK;
        }
    }

    esp_err_t create_attribute(const Datamodel__CreateAttributeParams *params)
    {
        if (!params) {
            return ESP_ERR_INVALID_ARG;
        }

        bool is_nullable = params->flags & esp_matter::ATTRIBUTE_FLAG_NULLABLE;

        Datamodel__EspMatterValType value_type = params->val ? params->val->type : DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_INVALID;
        bool value_is_set = params->val && params->val->val && params->val->val->value_case != DATAMODEL__ESP_MATTER_VAL__VALUE__NOT_SET;

        esp_matter::attribute_t *created_attribute = nullptr;

        switch (value_type) {
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_BOOLEAN:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_bool(params->val->val->b)
                                                                              : esp_matter_bool(params->val->val->b))
                                                              : (is_nullable ? esp_matter_nullable_bool(nullable<bool>())
                                                                 : esp_matter_bool(false)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_INT8:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_int8(params->val->val->i8)
                                                                              : esp_matter_int8(params->val->val->i8))
                                                              : (is_nullable ? esp_matter_nullable_int8(nullable<int8_t>())
                                                                 : esp_matter_int8(0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_UINT8:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_uint8(params->val->val->u8)
                                                                              : esp_matter_uint8(params->val->val->u8))
                                                              : (is_nullable ? esp_matter_nullable_uint8(nullable<uint8_t>())
                                                                 : esp_matter_uint8(0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_INT16:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_int16(params->val->val->i16)
                                                                              : esp_matter_int16(params->val->val->i16))
                                                              : (is_nullable ? esp_matter_nullable_int16(nullable<int16_t>())
                                                                 : esp_matter_int16(0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_UINT16:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_uint16(params->val->val->u16)
                                                                              : esp_matter_uint16(params->val->val->u16))
                                                              : (is_nullable ? esp_matter_nullable_uint16(nullable<uint16_t>())
                                                                 : esp_matter_uint16(0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_INT32:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_int32(params->val->val->i32)
                                                                              : esp_matter_int32(params->val->val->i32))
                                                              : (is_nullable ? esp_matter_nullable_int32(nullable<int32_t>())
                                                                 : esp_matter_int32(0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_UINT32:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_uint32(params->val->val->u32)
                                                                              : esp_matter_uint32(params->val->val->u32))
                                                              : (is_nullable ? esp_matter_nullable_uint32(nullable<uint32_t>())
                                                                 : esp_matter_uint32(0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_INT64:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_int64(params->val->val->i64)
                                                                              : esp_matter_int64(params->val->val->i64))
                                                              : (is_nullable ? esp_matter_nullable_int64(nullable<int64_t>())
                                                                 : esp_matter_int64(0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_UINT64:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_uint64(params->val->val->u64)
                                                                              : esp_matter_uint64(params->val->val->u64))
                                                              : (is_nullable ? esp_matter_nullable_uint64(nullable<uint64_t>())
                                                                 : esp_matter_uint64(0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_FLOAT:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_float(params->val->val->f)
                                                                              : esp_matter_float(params->val->val->f))
                                                              : (is_nullable ? esp_matter_nullable_float(nullable<float>())
                                                                 : esp_matter_float(0.0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_CHAR_STRING:
            if (params->has_max_val_size) {
                created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                                  value_is_set ? esp_matter_char_str(params->val->val->char_string, strlen(params->val->val->char_string))
                                                                  : (is_nullable ? esp_matter_char_str(nullptr, 0)
                                                                     : esp_matter_char_str(nullptr, 0)),
                                                                  params->max_val_size);
            } else {
                created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                                  value_is_set ? esp_matter_char_str(params->val->val->char_string, strlen(params->val->val->char_string))
                                                                  : (is_nullable ? esp_matter_char_str(nullptr, 0)
                                                                     : esp_matter_char_str(nullptr, 0)));
            }
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_LONG_CHAR_STRING:
            if (params->has_max_val_size) {
                created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                                  value_is_set ? esp_matter_long_char_str(params->val->val->char_string, strlen(params->val->val->char_string))
                                                                  : (is_nullable ? esp_matter_long_char_str(nullptr, 0)
                                                                     : esp_matter_long_char_str(nullptr, 0)),
                                                                  params->max_val_size);
            } else {
                created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                                  value_is_set ? esp_matter_long_char_str(params->val->val->char_string, strlen(params->val->val->char_string))
                                                                  : (is_nullable ? esp_matter_long_char_str(nullptr, 0)
                                                                     : esp_matter_long_char_str(nullptr, 0)));
            }
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_OCTET_STRING:
            if (params->has_max_val_size) {
                created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                                  value_is_set ? esp_matter_octet_str(params->val->val->octet_string.data, params->val->val->octet_string.len)
                                                                  : (is_nullable ? esp_matter_octet_str(nullptr, 0)
                                                                     : esp_matter_octet_str(nullptr, 0)),
                                                                  params->max_val_size);
            } else {
                created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                                  value_is_set ? esp_matter_octet_str(params->val->val->octet_string.data, params->val->val->octet_string.len)
                                                                  : (is_nullable ? esp_matter_octet_str(nullptr, 0)
                                                                     : esp_matter_octet_str(nullptr, 0)));
            }
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_LONG_OCTET_STRING:
            if (params->has_max_val_size) {
                created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                                  value_is_set ? esp_matter_long_octet_str(params->val->val->octet_string.data, params->val->val->octet_string.len)
                                                                  : (is_nullable ? esp_matter_long_octet_str(nullptr, 0)
                                                                     : esp_matter_long_octet_str(nullptr, 0)),
                                                                  params->max_val_size);
            } else {
                created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                                  value_is_set ? esp_matter_long_octet_str(params->val->val->octet_string.data, params->val->val->octet_string.len)
                                                                  : (is_nullable ? esp_matter_long_octet_str(nullptr, 0)
                                                                     : esp_matter_long_octet_str(nullptr, 0)));
            }
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_BITMAP8:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_bitmap8(params->val->val->u8)
                                                                              : esp_matter_bitmap8(params->val->val->u8))
                                                              : (is_nullable ? esp_matter_nullable_bitmap8(nullable<uint8_t>())
                                                                 : esp_matter_bitmap8(0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_BITMAP16:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_bitmap16(params->val->val->u16)
                                                                              : esp_matter_bitmap16(params->val->val->u16))
                                                              : (is_nullable ? esp_matter_nullable_bitmap16(nullable<uint16_t>())
                                                                 : esp_matter_bitmap16(0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_BITMAP32:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_bitmap32(params->val->val->u32)
                                                                              : esp_matter_bitmap32(params->val->val->u32))
                                                              : (is_nullable ? esp_matter_nullable_bitmap32(nullable<uint32_t>())
                                                                 : esp_matter_bitmap32(0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_ARRAY:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? esp_matter_array(params->val->val->a->elements.data, params->val->val->a->elements.len, params->val->val->a->n)
                                                              : esp_matter_array(nullptr, 0, 0));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_ENUM8:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_enum8(params->val->val->u8)
                                                                              : esp_matter_enum8(params->val->val->u8))
                                                              : (is_nullable ? esp_matter_nullable_enum8(nullable<uint8_t>())
                                                                 : esp_matter_enum8(0)));
            break;
        case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_ENUM16:
            created_attribute = esp_matter::attribute::create(current_cluster, params->attribute_id, params->flags,
                                                              value_is_set ? (is_nullable ? esp_matter_nullable_enum16(params->val->val->u16)
                                                                              : esp_matter_enum16(params->val->val->u16))
                                                              : (is_nullable ? esp_matter_nullable_enum16(nullable<uint16_t>())
                                                                 : esp_matter_enum16(0)));
            break;
        default:
            ESP_LOGE(TAG, "create_attribute: Unknown type");
            return ESP_ERR_INVALID_ARG;
        }

        if (!created_attribute) {
            ESP_LOGE(TAG, "create_attribute: Failed to create attribute_id: %" PRIu32, params->attribute_id);
            return ESP_ERR_NO_MEM;
        }

        if (created_attribute && value_is_set && params->bounds_min && params->bounds_max) {
            esp_matter_attr_val_t min_val, max_val;
            switch (value_type) {
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_INT8:
                min_val = is_nullable ? esp_matter_nullable_int8(params->bounds_min->i8) : esp_matter_int8(params->bounds_min->i8);
                max_val = is_nullable ? esp_matter_nullable_int8(params->bounds_max->i8) : esp_matter_int8(params->bounds_max->i8);
                break;
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_UINT8:
                min_val = is_nullable ? esp_matter_nullable_uint8(params->bounds_min->u8) : esp_matter_uint8(params->bounds_min->u8);
                max_val = is_nullable ? esp_matter_nullable_uint8(params->bounds_max->u8) : esp_matter_uint8(params->bounds_max->u8);
                break;
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_INT16:
                min_val = is_nullable ? esp_matter_nullable_int16(params->bounds_min->i16) : esp_matter_int16(params->bounds_min->i16);
                max_val = is_nullable ? esp_matter_nullable_int16(params->bounds_max->i16) : esp_matter_int16(params->bounds_max->i16);
                break;
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_UINT16:
                min_val = is_nullable ? esp_matter_nullable_uint16(params->bounds_min->u16) : esp_matter_uint16(params->bounds_min->u16);
                max_val = is_nullable ? esp_matter_nullable_uint16(params->bounds_max->u16) : esp_matter_uint16(params->bounds_max->u16);
                break;
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_INT32:
                min_val = is_nullable ? esp_matter_nullable_int32(params->bounds_min->i32) : esp_matter_int32(params->bounds_min->i32);
                max_val = is_nullable ? esp_matter_nullable_int32(params->bounds_max->i32) : esp_matter_int32(params->bounds_max->i32);
                break;
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_UINT32:
                min_val = is_nullable ? esp_matter_nullable_uint32(params->bounds_min->u32) : esp_matter_uint32(params->bounds_min->u32);
                max_val = is_nullable ? esp_matter_nullable_uint32(params->bounds_max->u32) : esp_matter_uint32(params->bounds_max->u32);
                break;
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_INT64:
                min_val = is_nullable ? esp_matter_nullable_int64(params->bounds_min->i64) : esp_matter_int64(params->bounds_min->i64);
                max_val = is_nullable ? esp_matter_nullable_int64(params->bounds_max->i64) : esp_matter_int64(params->bounds_max->i64);
                break;
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_UINT64:
                min_val = is_nullable ? esp_matter_nullable_uint64(params->bounds_min->u64) : esp_matter_uint64(params->bounds_min->u64);
                max_val = is_nullable ? esp_matter_nullable_uint64(params->bounds_max->u64) : esp_matter_uint64(params->bounds_max->u64);
                break;
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_ENUM8:
                min_val = is_nullable ? esp_matter_nullable_enum8(params->bounds_min->u8) : esp_matter_enum8(params->bounds_min->u8);
                max_val = is_nullable ? esp_matter_nullable_enum8(params->bounds_max->u8) : esp_matter_enum8(params->bounds_max->u8);
                break;
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_ENUM16:
                min_val = is_nullable ? esp_matter_nullable_enum16(params->bounds_min->u16) : esp_matter_enum16(params->bounds_min->u16);
                max_val = is_nullable ? esp_matter_nullable_enum16(params->bounds_max->u16) : esp_matter_enum16(params->bounds_max->u16);
                break;
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_BITMAP8:
                min_val = is_nullable ? esp_matter_nullable_bitmap8(params->bounds_min->u8) : esp_matter_bitmap8(params->bounds_min->u8);
                max_val = is_nullable ? esp_matter_nullable_bitmap8(params->bounds_max->u8) : esp_matter_bitmap8(params->bounds_max->u8);
                break;
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_BITMAP16:
                min_val = is_nullable ? esp_matter_nullable_bitmap16(params->bounds_min->u16) : esp_matter_bitmap16(params->bounds_min->u16);
                max_val = is_nullable ? esp_matter_nullable_bitmap16(params->bounds_max->u16) : esp_matter_bitmap16(params->bounds_max->u16);
                break;
            case DATAMODEL__ESP_MATTER_VAL_TYPE__ESP_MATTER_VAL_TYPE_BITMAP32:
                min_val = is_nullable ? esp_matter_nullable_bitmap32(params->bounds_min->u32) : esp_matter_bitmap32(params->bounds_min->u32);
                max_val = is_nullable ? esp_matter_nullable_bitmap32(params->bounds_max->u32) : esp_matter_bitmap32(params->bounds_max->u32);
                break;
            default:
                ESP_LOGE(TAG, "create_bounds: Unknown bounds type");
                return ESP_ERR_INVALID_ARG;
            }

            esp_err_t bounds_result = esp_matter::attribute::add_bounds(created_attribute, min_val, max_val);
            if (bounds_result != ESP_OK) {
                ESP_LOGE(TAG, "create_attribute: Failed to add bounds for attribute_id: %" PRIu32, params->attribute_id);
                return bounds_result;
            }
        }

        return ESP_OK;
    }

    esp_err_t create_command(const Datamodel__CreateCommandParams *params)
    {
        esp_err_t err = register_command_cb(current_cluster, params->cluster_id, params->command_id, params->flags);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "create_command: register_command_cb failed for cluster id: %" PRIu32 ", command id: %" PRIu32 ", error: %d",
                     params->cluster_id, params->command_id, err);
        }
        return err;
    }

    esp_err_t create_event(const Datamodel__CreateEventParams *params)
    {
        if (esp_matter::event::create(current_cluster, params->event_id) == nullptr) {
            ESP_LOGE(TAG, "create_event: Failed to create event with id: %" PRIu32, params->event_id);
            return ESP_FAIL;
        } else {
            ESP_LOGD(TAG, "create_event: Created event with id: %" PRIu32 " on cluster", params->event_id);
            return ESP_OK;
        }
    }

    esp_err_t endpoint_add_device_type(const Datamodel__EndpointAddDeviceTypeParams *params)
    {
        if (esp_matter::endpoint::add_device_type(current_endpoint, params->device_type_id, params->device_type_version) != ESP_OK) {
            ESP_LOGE(TAG, "endpoint_add_device_type: Failed to add device type to endpoint");
            return ESP_FAIL;
        } else {
            ESP_LOGD(TAG, "endpoint_add_device_type: Added device type id: %" PRIu32 " to endpoint", params->device_type_id);
            return ESP_OK;
        }
    }

    esp_matter::node_t* interpret_data(const uint8_t *data, size_t length)
    {
        raw_node = esp_matter::node::create_raw();
        if (raw_node == nullptr) {
            ESP_LOGE(TAG, "Failed to create raw node");
            return nullptr;
        }

        size_t offset = 0;
        size_t message_index = 0;
        while (offset < length) {
            size_t prefix_len = 0;
            size_t total_len = scan_length_prefixed_data(length - offset, &data[offset], &prefix_len);

            if (total_len == 0 || prefix_len == 0) {
                ESP_LOGE(TAG, "Failed to read length-prefixed data");
                return nullptr;
            }

            size_t msg_len = total_len - prefix_len;
            if (offset + total_len > length) {
                ESP_LOGE(TAG, "Message length exceeds buffer");
                return nullptr;
            }

            Datamodel__FunctionCall *message = datamodel__function_call__unpack(nullptr, msg_len, &data[offset + prefix_len]);
            if (!message) {
                ESP_LOGE(TAG, "Failed to unpack message at index %zu", message_index);
                return nullptr;
            }

            esp_err_t err = handle_function_call(message);
            if (err != ESP_OK) {
                ESP_LOGE(TAG, "Failed to handle function call for message at index %zu, error: %d", message_index, err);
            }

            datamodel__function_call__free_unpacked(message, nullptr);
            offset += total_len;
            message_index++;
        }

        return raw_node;
    }
};

//////////////////////////
// Public Interface API //
//////////////////////////

Interpreter::Interpreter() : pimpl_(std::make_unique<Impl>()) {}

Interpreter::~Interpreter() = default;

esp_matter::node_t* Interpreter::interpret_data(const uint8_t *data, size_t length)
{
    return pimpl_->interpret_data(data, length);
}

} // namespace esp_matter_data_model_interpreter
