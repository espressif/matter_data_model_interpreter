# SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
from enum import IntFlag


def calculate_flag_value(enum_class, flag_list):
    flag_value = enum_class(0)
    for flag in flag_list:
        if hasattr(enum_class, flag):
            flag_value |= getattr(enum_class, flag)
        else:
            raise ValueError(f"Flag '{flag}' not found in {enum_class.__name__}")
    return flag_value


class AttributeFlags(IntFlag):
    ATTRIBUTE_FLAG_NONE = 0x00
    ATTRIBUTE_FLAG_WRITABLE = 0x01
    ATTRIBUTE_FLAG_NONVOLATILE = 0x02
    ATTRIBUTE_FLAG_MIN_MAX = 0x04
    ATTRIBUTE_FLAG_MUST_USE_TIMED_WRITE = 0x08
    ATTRIBUTE_FLAG_EXTERNAL_STORAGE = 0x10
    ATTRIBUTE_FLAG_SINGLETON = 0x20
    ATTRIBUTE_FLAG_NULLABLE = 0x40
    ATTRIBUTE_FLAG_OVERRIDE = 0x80  # ATTRIBUTE_FLAG_NULLABLE << 1 (0x40 << 1 = 0x80)
    ATTRIBUTE_FLAG_DEFERRED = 0x100  # ATTRIBUTE_FLAG_NULLABLE << 2 (0x40 << 2 = 0x100)


class CommandFlags(IntFlag):
    COMMAND_FLAG_NONE = 0x00
    COMMAND_FLAG_CUSTOM = 0x01
    COMMAND_FLAG_ACCEPTED = 0x02
    COMMAND_FLAG_GENERATED = 0x04


class EndpointFlags(IntFlag):
    ENDPOINT_FLAG_NONE = 0x00
    ENDPOINT_FLAG_DESTROYABLE = 0x01
    ENDPOINT_FLAG_BRIDGE = 0x02


class ClusterFlags(IntFlag):
    CLUSTER_FLAG_NONE = 0x00
    CLUSTER_FLAG_INIT_FUNCTION = 0x01
    CLUSTER_FLAG_ATTRIBUTE_CHANGED_FUNCTION = 0x02
    CLUSTER_FLAG_SHUTDOWN_FUNCTION = 0x10
    CLUSTER_FLAG_PRE_ATTRIBUTE_CHANGED_FUNCTION = 0x20
    CLUSTER_FLAG_SERVER = 0x40
    CLUSTER_FLAG_CLIENT = 0x80


def print_flag_dictionary(enum_class):
    print(f"Parsed Flags Dictionary for {enum_class.__name__}:")
    for flag in enum_class:
        print(f"{flag.name}: {flag.value:#04x}")
