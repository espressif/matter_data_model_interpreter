# SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
import json
from matter_data_model_conversion.matter_enums import (
    AttributeFlags,
    CommandFlags,
    EndpointFlags,
    ClusterFlags,
    calculate_flag_value,
    print_flag_dictionary,
)
import matter_data_model_conversion.esp_matter_data_model_api_messages_pb2 as emdm_pb2
from google.protobuf.internal.encoder import _VarintBytes

skip_global_attributes = [
    "attributeList",
    "acceptedCommandList",
    "generatedCommandList",
    "eventList",
]


def compute_bitmap(entries):
    bitmap_value = 0
    for entry in entries:
        bitmap_value |= entry["code"]
    return bitmap_value


def get_esp_matter_attribute_type(attribute, attribute_type):
    if attribute["definition"]["is_list"] or attribute["definition"]["is_struct"]:
        return "ESP_MATTER_VAL_TYPE_ARRAY"

    mapping = {
        "boolean": "ESP_MATTER_VAL_TYPE_BOOLEAN",
        "single": "ESP_MATTER_VAL_TYPE_FLOAT",
        "double": "ESP_MATTER_VAL_TYPE_FLOAT",
        "char_string": "ESP_MATTER_VAL_TYPE_CHAR_STRING",
        "octet_string": "ESP_MATTER_VAL_TYPE_OCTET_STRING",
        "int8s": "ESP_MATTER_VAL_TYPE_INT8",
        "int8u": "ESP_MATTER_VAL_TYPE_UINT8",
        "int16s": "ESP_MATTER_VAL_TYPE_INT16",
        "int16u": "ESP_MATTER_VAL_TYPE_UINT16",
        "int32s": "ESP_MATTER_VAL_TYPE_INT32",
        "int32u": "ESP_MATTER_VAL_TYPE_UINT32",
        "int64s": "ESP_MATTER_VAL_TYPE_INT64",
        "int64u": "ESP_MATTER_VAL_TYPE_UINT64",
        "enum8": "ESP_MATTER_VAL_TYPE_ENUM8",
        "bitmap8": "ESP_MATTER_VAL_TYPE_BITMAP8",
        "bitmap16": "ESP_MATTER_VAL_TYPE_BITMAP16",
        "bitmap32": "ESP_MATTER_VAL_TYPE_BITMAP32",
        "enum16": "ESP_MATTER_VAL_TYPE_ENUM16",
        "long_char_string": "ESP_MATTER_VAL_TYPE_LONG_CHAR_STRING",
        "long_octet_string": "ESP_MATTER_VAL_TYPE_LONG_OCTET_STRING",
    }

    additional_mapping = {
        "ESP_MATTER_VAL_TYPE_UINT8": ["action_id", "fabric_idx", "status", "percent"],
        "ESP_MATTER_VAL_TYPE_UINT16": [
            "endpoint_no",
            "group_id",
            "vendor_id",
            "percent100ths",
        ],
        "ESP_MATTER_VAL_TYPE_UINT32": [
            "cluster_id",
            "attrib_id",
            "field_id",
            "event_id",
            "command_id",
            "trans_id",
            "devtype_id",
            "data_ver",
            "epoch_s",
            "elapsed_s",
        ],
        "ESP_MATTER_VAL_TYPE_INT64": [
            "amperage_ma",
            "energy_mwh",
            "power_mw",
            "voltage_mv",
        ],
        "ESP_MATTER_VAL_TYPE_UINT64": [
            "event_no",
            "fabric_id",
            "node_id",
            "bitmap64",
            "epoch_us",
            "posix_ms",
            "systime_ms",
            "systime_us",
        ],
        "ESP_MATTER_VAL_TYPE_INT16": ["temperature"],
    }

    # Check if the attribute type is in the primary mapping
    if attribute_type in mapping:
        return mapping[attribute_type]

    # Check if the attribute type is in the additional mapping
    for esp_type, types in additional_mapping.items():
        if attribute_type in types:
            return esp_type

    return "ESP_MATTER_VAL_TYPE_INVALID"


def compute_attribute_value(attribute, esp_matter_attribute_type):
    default_value = attribute.get("default")

    # Treat "NA" as None
    if default_value == "NA":
        default_value = None

    # Compute value based on ESP Matter type
    if esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_BOOLEAN":
        return bool(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_INT8":
        return int(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_UINT8":
        return int(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_INT16":
        return int(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_UINT16":
        return int(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_INT32":
        return int(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_UINT32":
        return int(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_INT64":
        return int(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_UINT64":
        return int(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_FLOAT":
        return float(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_CHAR_STRING":
        return str(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_LONG_CHAR_STRING":
        return str(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_OCTET_STRING":
        return bytes(default_value, "utf-8") if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_LONG_OCTET_STRING":
        return bytes(default_value, "utf-8") if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_BITMAP8":
        type_info = attribute["definition"]["type"]
        entries = type_info.get("entries", [])
        return int(default_value) if default_value is not None else compute_bitmap(entries) if entries else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_BITMAP16":
        type_info = attribute["definition"]["type"]
        entries = type_info.get("entries", [])
        return int(default_value) if default_value is not None else compute_bitmap(entries) if entries else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_BITMAP32":
        type_info = attribute["definition"]["type"]
        entries = type_info.get("entries", [])
        return int(default_value) if default_value is not None else compute_bitmap(entries) if entries else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_ARRAY":
        return default_value if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_ENUM8":
        return int(default_value) if default_value is not None else None
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_ENUM16":
        return int(default_value) if default_value is not None else None
    else:
        return None  # Default case if no other types match


def process_endpoint(endpoint):
    proto_msg = emdm_pb2.FunctionCall()
    proto_msg.function = emdm_pb2.FunctionCall.FunctionType.CREATE_ENDPOINT
    proto_msg.create_endpoint_params.endpoint_id = endpoint["number"]
    proto_msg.create_endpoint_params.flags = EndpointFlags.ENDPOINT_FLAG_NONE

    size = proto_msg.ByteSize()
    size = _VarintBytes(size)
    full_proto_msg = size + proto_msg.SerializeToString()
    return full_proto_msg.hex()


def process_device_type(device_type, endpoint_id):
    proto_msg = emdm_pb2.FunctionCall()
    proto_msg.function = emdm_pb2.FunctionCall.FunctionType.ENDPOINT_ADD_DEVICE_TYPE
    proto_msg.endpoint_add_device_type_params.endpoint_id = endpoint_id
    proto_msg.endpoint_add_device_type_params.device_type_id = device_type["code"]
    proto_msg.endpoint_add_device_type_params.device_type_version = device_type["version"]

    size = proto_msg.ByteSize()
    size = _VarintBytes(size)
    full_proto_msg = size + proto_msg.SerializeToString()
    return full_proto_msg.hex()


def process_cluster(cluster, endpoint_id):
    computed_cluster_flags = calculate_flag_value(ClusterFlags, cluster["flags"])
    proto_msg = emdm_pb2.FunctionCall()
    proto_msg.function = emdm_pb2.FunctionCall.FunctionType.CREATE_CLUSTER
    proto_msg.create_cluster_params.endpoint_id = endpoint_id
    proto_msg.create_cluster_params.cluster_id = cluster["code"]
    proto_msg.create_cluster_params.flags = computed_cluster_flags

    size = proto_msg.ByteSize()
    size = _VarintBytes(size)
    full_proto_msg = size + proto_msg.SerializeToString()
    return full_proto_msg.hex()


def set_bounds_value(bounds_val, esp_matter_attribute_type, value):
    if esp_matter_attribute_type in [
        "ESP_MATTER_VAL_TYPE_BOOLEAN",
        "ESP_MATTER_VAL_TYPE_FLOAT",
        "ESP_MATTER_VAL_TYPE_CHAR_STRING",
        "ESP_MATTER_VAL_TYPE_LONG_CHAR_STRING",
        "ESP_MATTER_VAL_TYPE_OCTET_STRING",
        "ESP_MATTER_VAL_TYPE_LONG_OCTET_STRING",
        "ESP_MATTER_VAL_TYPE_ARRAY",
    ]:
        return
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_INT8":
        bounds_val.i8 = value
    elif esp_matter_attribute_type in [
        "ESP_MATTER_VAL_TYPE_UINT8",
        "ESP_MATTER_VAL_TYPE_ENUM8",
    ]:
        bounds_val.u8 = value
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_INT16":
        bounds_val.i16 = value
    elif esp_matter_attribute_type in [
        "ESP_MATTER_VAL_TYPE_UINT16",
        "ESP_MATTER_VAL_TYPE_ENUM16",
    ]:
        bounds_val.u16 = value
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_INT32":
        bounds_val.i32 = value
    elif esp_matter_attribute_type == ["ESP_MATTER_VAL_TYPE_UINT32"]:
        bounds_val.u32 = value
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_INT64":
        bounds_val.i64 = value
    elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_UINT64":
        bounds_val.u64 = value
    elif esp_matter_attribute_type in [
        "ESP_MATTER_VAL_TYPE_BITMAP8",
        "ESP_MATTER_VAL_TYPE_BITMAP16",
        "ESP_MATTER_VAL_TYPE_BITMAP32",
    ]:
        bounds_val.u32 = value


def process_attribute(attribute, endpoint_id, cluster_id):
    attribute_flags = []

    if attribute["storage"] == "PERSIST":
        attribute_flags.append("ATTRIBUTE_FLAG_NONVOLATILE")
    if "NULLABLE" in attribute["definition"]["qualities"]:
        attribute_flags.append("ATTRIBUTE_FLAG_NULLABLE")
    if "WRITABLE" in attribute["qualities"]:
        attribute_flags.append("ATTRIBUTE_FLAG_WRITABLE")
    else:
        attribute_flags.append("ATTRIBUTE_FLAG_NONE")
    computed_attribute_flags = calculate_flag_value(AttributeFlags, attribute_flags)

    type_info = attribute["definition"]["type"]
    attribute_type = type_info.get("base_type", type_info["name"])  # Use base_type if available, otherwise use name
    esp_matter_attribute_type = get_esp_matter_attribute_type(attribute, attribute_type)
    esp_matter_value = compute_attribute_value(attribute, esp_matter_attribute_type)

    proto_msg = emdm_pb2.FunctionCall()
    proto_msg.function = emdm_pb2.FunctionCall.FunctionType.CREATE_ATTRIBUTE
    proto_msg.create_attribute_params.endpoint_id = endpoint_id
    proto_msg.create_attribute_params.cluster_id = cluster_id
    proto_msg.create_attribute_params.attribute_id = attribute["definition"]["code"]
    proto_msg.create_attribute_params.flags = computed_attribute_flags
    if attribute["definition"]["type"].get("max_length") is not None:
        proto_msg.create_attribute_params.max_val_size = attribute["definition"]["type"]["max_length"]

    attr_val = proto_msg.create_attribute_params.val
    attr_val.type = getattr(emdm_pb2.EspMatterValType, esp_matter_attribute_type)

    if esp_matter_value is not None:
        if esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_BOOLEAN":
            attr_val.val.b = esp_matter_value
        elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_INT8":
            attr_val.val.i8 = esp_matter_value
        elif esp_matter_attribute_type in [
            "ESP_MATTER_VAL_TYPE_UINT8",
            "ESP_MATTER_VAL_TYPE_ENUM8",
        ]:
            attr_val.val.u8 = esp_matter_value
        elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_INT16":
            attr_val.val.i16 = esp_matter_value
        elif esp_matter_attribute_type in [
            "ESP_MATTER_VAL_TYPE_UINT16",
            "ESP_MATTER_VAL_TYPE_ENUM16",
        ]:
            attr_val.val.u16 = esp_matter_value
        elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_INT32":
            attr_val.val.i32 = esp_matter_value
        elif esp_matter_attribute_type == ["ESP_MATTER_VAL_TYPE_UINT32"]:
            attr_val.val.u32 = esp_matter_value
        elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_INT64":
            attr_val.val.i64 = esp_matter_value
        elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_UINT64":
            attr_val.val.u64 = esp_matter_value
        elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_FLOAT":
            attr_val.val.f = esp_matter_value
        elif esp_matter_attribute_type in [
            "ESP_MATTER_VAL_TYPE_CHAR_STRING",
            "ESP_MATTER_VAL_TYPE_LONG_CHAR_STRING",
        ]:
            attr_val.val.char_string = esp_matter_value
        elif esp_matter_attribute_type in [
            "ESP_MATTER_VAL_TYPE_OCTET_STRING",
            "ESP_MATTER_VAL_TYPE_LONG_OCTET_STRING",
        ]:
            attr_val.val.octet_string = esp_matter_value
        elif esp_matter_attribute_type in [
            "ESP_MATTER_VAL_TYPE_BITMAP8",
            "ESP_MATTER_VAL_TYPE_BITMAP16",
            "ESP_MATTER_VAL_TYPE_BITMAP32",
        ]:
            attr_val.val.u32 = esp_matter_value
        elif esp_matter_attribute_type == "ESP_MATTER_VAL_TYPE_ARRAY":
            attr_val.val.a.elements = bytes(esp_matter_value)  # Assuming val is a list of elements
            attr_val.val.a.s = len(esp_matter_value)  # Size of the data
            attr_val.val.a.n = len(esp_matter_value)  # Count of the elements
            attr_val.val.a.t = len(esp_matter_value)  # Total size, assuming simple case

    # Handle bounds
    if attribute["definition"].get("bounds") is not None:
        bounds = attribute["definition"]["bounds"]
        min_value = bounds["min"]
        max_value = bounds["max"]

        # Set the bounds_min
        set_bounds_value(
            proto_msg.create_attribute_params.bounds_min,
            esp_matter_attribute_type,
            min_value,
        )

        # Set the bounds_max
        set_bounds_value(
            proto_msg.create_attribute_params.bounds_max,
            esp_matter_attribute_type,
            max_value,
        )

    # Serialize and return the protobuf message
    size = proto_msg.ByteSize()
    size = _VarintBytes(size)
    full_proto_msg = size + proto_msg.SerializeToString()

    return full_proto_msg.hex()


def process_command(command, endpoint_id, cluster_id):
    hex_messages = []
    # Process the main command
    command_flags = ["COMMAND_FLAG_ACCEPTED"]
    computed_command_flags = calculate_flag_value(CommandFlags, command_flags)
    proto_msg = emdm_pb2.FunctionCall()
    proto_msg.function = emdm_pb2.FunctionCall.FunctionType.CREATE_COMMAND
    proto_msg.create_command_params.endpoint_id = endpoint_id
    proto_msg.create_command_params.cluster_id = cluster_id
    proto_msg.create_command_params.command_id = command["code"]
    proto_msg.create_command_params.flags = computed_command_flags

    size = proto_msg.ByteSize()
    size = _VarintBytes(size)
    full_proto_msg = size + proto_msg.SerializeToString()
    hex_messages.append(full_proto_msg.hex())

    # Process generated command if it exists
    if command.get("generated") is not None:
        generated_command = command["generated"]
        generated_flags = ["COMMAND_FLAG_GENERATED"]
        computed_generated_flags = calculate_flag_value(CommandFlags, generated_flags)

        proto_msg = emdm_pb2.FunctionCall()
        proto_msg.function = emdm_pb2.FunctionCall.FunctionType.CREATE_COMMAND
        proto_msg.create_command_params.endpoint_id = endpoint_id
        proto_msg.create_command_params.cluster_id = cluster_id
        proto_msg.create_command_params.command_id = generated_command["code"]
        proto_msg.create_command_params.flags = computed_generated_flags

        size = proto_msg.ByteSize()
        size = _VarintBytes(size)
        full_proto_msg = size + proto_msg.SerializeToString()
        hex_messages.append(full_proto_msg.hex())

    return hex_messages


def process_event(event, endpoint_id, cluster_id):
    proto_msg = emdm_pb2.FunctionCall()
    proto_msg.function = emdm_pb2.FunctionCall.FunctionType.CREATE_EVENT
    proto_msg.create_event_params.endpoint_id = endpoint_id
    proto_msg.create_event_params.cluster_id = cluster_id
    proto_msg.create_event_params.event_id = event["code"]

    size = proto_msg.ByteSize()
    size = _VarintBytes(size)
    full_proto_msg = size + proto_msg.SerializeToString()
    return full_proto_msg.hex()


def process_data_model(data_model):
    hex_messages = []

    for endpoint in data_model["data_model"]["endpoints"]:
        hex_messages.append(process_endpoint(endpoint))

        for device_type in endpoint["device_types"]:
            hex_messages.append(process_device_type(device_type, endpoint["number"]))

        for cluster in endpoint["clusters"]:
            hex_messages.append(process_cluster(cluster, endpoint["number"]))

            for attribute in cluster["attributes"]:
                if attribute["definition"]["name"] not in skip_global_attributes:
                    hex_messages.append(process_attribute(attribute, endpoint["number"], cluster["code"]))

            for command in cluster["commands"]:
                hex_messages.extend(process_command(command, endpoint["number"], cluster["code"]))

            for event in cluster["events"]:
                hex_messages.append(process_event(event, endpoint["number"], cluster["code"]))

    return hex_messages


def create_binary_file(json_file_path, bin_file_path):
    with open(json_file_path) as f:
        data_model = json.load(f)
        hex_messages = process_data_model(data_model)

    combined_hex = "".join(hex_messages)
    bin_data = bytes.fromhex(combined_hex)
    with open(bin_file_path, "wb") as bin_file:
        bin_file.write(bin_data)

    print(f"Binary file written to: {bin_file_path}")
