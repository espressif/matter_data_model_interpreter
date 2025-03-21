/*
 * SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef CMD_C_ROUTINES_H
#define CMD_C_ROUTINES_H

#include <esp_err.h>
#include "esp_matter.h"

#ifdef __cplusplus
extern "C" {
#endif

esp_err_t register_command_cb(esp_matter::cluster_t *cluster, uint32_t cluster_id, uint32_t command_id, uint8_t flag);
esp_err_t cluster_plugin_init(esp_matter::cluster_t *cluster, uint32_t cluster_id);

#ifdef __cplusplus
}
#endif

#endif // CMD_C_ROUTINES_H
