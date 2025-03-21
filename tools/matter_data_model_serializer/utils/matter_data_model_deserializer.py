# SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
import json
import os
import sys

from google.protobuf.internal.decoder import _DecodeVarint32
from matter_data_model_serializer.matter_data_model_conversion import (
    esp_matter_data_model_api_messages_pb2 as emdm_pb2,
)


def read_protobuf_messages(file_path):
    """
    Generator function that reads Protobuf messages one by one from the given file.
    Yields each message in JSON (dict) form.
    """
    index = 0

    with open(file_path, "rb") as f:
        while True:
            # Read the size of the next message (varint)
            buf = f.read(1)
            if not buf:
                break  # End of file

            # Read more bytes if necessary until we can decode the varint
            while buf[-1] & 0x80:
                more_byte = f.read(1)
                if not more_byte:
                    raise IOError("Unexpected end of file while reading varint.")
                buf += more_byte

            # Decode the size from the varint
            size, _ = _DecodeVarint32(buf, 0)

            # Read the message itself
            message_data = f.read(size)
            if len(message_data) != size:
                raise IOError(f"Incomplete message read, expected {size} bytes but got {len(message_data)}.")

            # Parse the message
            function_call = emdm_pb2.FunctionCall()
            function_call.ParseFromString(message_data)

            # Convert the message to JSON (dict)
            message_json = json.loads(function_call_to_json(function_call))
            message_json["message_index"] = index

            yield message_json
            index += 1


def function_call_to_json(function_call):
    result = {"function": emdm_pb2.FunctionCall.FunctionType.Name(function_call.function)}

    if function_call.HasField("create_attribute_params"):
        result["create_attribute_params"] = create_attribute_params_to_json(function_call.create_attribute_params)
    elif function_call.HasField("create_command_params"):
        result["create_command_params"] = create_command_params_to_json(function_call.create_command_params)
    elif function_call.HasField("create_event_params"):
        result["create_event_params"] = create_event_params_to_json(function_call.create_event_params)
    elif function_call.HasField("create_cluster_params"):
        result["create_cluster_params"] = create_cluster_params_to_json(function_call.create_cluster_params)
    elif function_call.HasField("create_endpoint_params"):
        result["create_endpoint_params"] = create_endpoint_params_to_json(function_call.create_endpoint_params)
    elif function_call.HasField("endpoint_add_device_type_params"):
        result["endpoint_add_device_type_params"] = endpoint_add_device_type_params_to_json(
            function_call.endpoint_add_device_type_params
        )

    return json.dumps(result, default=str)


def create_attribute_params_to_json(params):
    def extract_val(val):
        return {
            key: value
            for key, value in {
                "b": val.b if val.HasField("b") else None,
                "i": val.i if val.HasField("i") else None,
                "f": val.f if val.HasField("f") else None,
                "i8": val.i8 if val.HasField("i8") else None,
                "u8": val.u8 if val.HasField("u8") else None,
                "i16": val.i16 if val.HasField("i16") else None,
                "u16": val.u16 if val.HasField("u16") else None,
                "i32": val.i32 if val.HasField("i32") else None,
                "u32": val.u32 if val.HasField("u32") else None,
                "i64": val.i64 if val.HasField("i64") else None,
                "u64": val.u64 if val.HasField("u64") else None,
                "a": val.a.elements.hex() if val.HasField("a") else None,
                "char_string": val.char_string if val.HasField("char_string") else None,
                "octet_string": val.octet_string.hex() if val.HasField("octet_string") else None,
            }.items()
            if value is not None
        }

    return {
        "endpoint_id": params.endpoint_id,
        "cluster_id": params.cluster_id,
        "attribute_id": params.attribute_id,
        "flags": params.flags,
        "val": {
            "type": emdm_pb2.EspMatterValType.Name(params.val.type),
            "val": extract_val(params.val.val),
        },
        "max_val_size": params.max_val_size,
        "bounds_min": extract_val(params.bounds_min),
        "bounds_max": extract_val(params.bounds_max),
    }


def create_command_params_to_json(params):
    return {
        "endpoint_id": params.endpoint_id,
        "cluster_id": params.cluster_id,
        "command_id": params.command_id,
        "flags": params.flags,
    }


def create_event_params_to_json(params):
    return {
        "endpoint_id": params.endpoint_id,
        "cluster_id": params.cluster_id,
        "event_id": params.event_id,
    }


def create_cluster_params_to_json(params):
    return {
        "endpoint_id": params.endpoint_id,
        "cluster_id": params.cluster_id,
        "flags": params.flags,
    }


def create_endpoint_params_to_json(params):
    return {"endpoint_id": params.endpoint_id, "flags": params.flags}


def endpoint_add_device_type_params_to_json(params):
    return {
        "endpoint_id": params.endpoint_id,
        "device_type_id": params.device_type_id,
        "device_type_version": params.device_type_version,
    }


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python -m matter_data_model_serializer.utils.matter_data_model_deserializer <path_to_data_model.bin>"
        )
        sys.exit(1)

    bin_file_path = sys.argv[1]

    if not os.path.exists(bin_file_path):
        print(f"File not found: {bin_file_path}")
        sys.exit(1)

    base_filename = os.path.splitext(bin_file_path)[0]
    jsonl_file_path = f"{base_filename}_decoded.jsonl"

    # Open the .jsonl file and write each message line by line.
    with open(jsonl_file_path, "w") as jsonl_file:
        for message in read_protobuf_messages(bin_file_path):
            # Dump the message as JSON on a new line
            jsonl_file.write(json.dumps(message) + "\n")

    print(f"Decoded messages written to: {jsonl_file_path}")


if __name__ == "__main__":
    main()
