# SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
import json

from attribute_bounds.attribute_bounds_lookup import BoundsLookup

try:
    from matter_idl.matter_idl_parser import CreateParser
    from matter_idl.matter_idl_types import *
except ImportError:
    from matter.idl.matter_idl_parser import CreateParser
    from matter.idl.matter_idl_types import *


def load_idl_text(file_path):
    with open(file_path, "r") as file:
        return file.read()


def parseText(txt, skip_meta=True):
    return CreateParser(skip_meta=skip_meta).parse(txt)


def find_cluster_by_name(name, clusters):
    for cluster in clusters:
        if cluster.name == name:
            return cluster
    return None


def find_enum_by_name(name, enums):
    for enum in enums:
        if enum.name == name:
            return enum
    return None


def find_bitmap_by_name(name, bitmaps):
    for bitmap in bitmaps:
        if bitmap.name == name:
            return bitmap
    return None


def find_struct_by_name(name, structs):
    for struct in structs:
        if struct.name == name:
            return struct
    return None


def determine_cluster_flags(cluster_name, endpoint):
    flags = []
    if any(cluster.name == cluster_name for cluster in endpoint.server_clusters):
        flags.append("CLUSTER_FLAG_SERVER")
    if cluster_name in endpoint.client_bindings:
        flags.append("CLUSTER_FLAG_CLIENT")
    return flags


def find_attribute_instantiation_by_name(name, server_cluster):
    for attr_inst in server_cluster.attributes:
        if attr_inst.name == name:
            return attr_inst
    return None


def collect_instantiated_attributes(endpoints):
    instantiated_attributes = {}
    for endpoint in endpoints:
        endpoint_attrs = {}
        for cluster in endpoint.server_clusters:
            if cluster.name not in endpoint_attrs:
                endpoint_attrs[cluster.name] = set()
            for attribute in cluster.attributes:
                endpoint_attrs[cluster.name].add(attribute.name)
        instantiated_attributes[endpoint.number] = endpoint_attrs
    return instantiated_attributes


def collect_instantiated_commands(endpoints):
    instantiated_commands = {}
    for endpoint in endpoints:
        endpoint_cmds = {}
        for cluster in endpoint.server_clusters:
            if cluster.name not in endpoint_cmds:
                endpoint_cmds[cluster.name] = set()
            for command in cluster.commands:
                endpoint_cmds[cluster.name].add(command.name)
        instantiated_commands[endpoint.number] = endpoint_cmds
    return instantiated_commands


def collect_instantiated_events(endpoints):
    instantiated_events = {}
    for endpoint in endpoints:
        endpoint_events = {}
        for cluster in endpoint.server_clusters:
            if cluster.name not in endpoint_events:
                endpoint_events[cluster.name] = set()
            for event_name in cluster.events_emitted:
                endpoint_events[cluster.name].add(event_name)
        instantiated_events[endpoint.number] = endpoint_events
    return instantiated_events


def generate_json_data_model(idl_text, attribute_bounds_pkl_path):
    parsed_idl = parseText(idl_text)
    bounds_lookup = BoundsLookup(attribute_bounds_pkl_path)

    instantiated_attributes = collect_instantiated_attributes(parsed_idl.endpoints)
    instantiated_commands = collect_instantiated_commands(parsed_idl.endpoints)
    instantiated_events = collect_instantiated_events(parsed_idl.endpoints)

    data_model = {
        "data_model": {
            "endpoints": [
                {
                    "number": endpoint.number,
                    "device_types": [
                        {
                            "name": device_type.name,
                            "code": device_type.code,
                            "version": device_type.version,
                        }
                        for device_type in endpoint.device_types
                    ],
                    "clusters": [
                        {
                            "name": cluster.name,
                            "code": find_cluster_by_name(cluster.name, parsed_idl.clusters).code,
                            "revision": find_cluster_by_name(cluster.name, parsed_idl.clusters).revision,
                            "flags": determine_cluster_flags(cluster.name, endpoint),
                            "attributes": [
                                {
                                    "definition": {
                                        "name": attribute.definition.name,
                                        "code": attribute.definition.code,
                                        "is_list": attribute.definition.is_list,
                                        "type": {
                                            "name": attribute.definition.data_type.name,
                                            "min_length": attribute.definition.data_type.min_length,
                                            "max_length": attribute.definition.data_type.max_length,
                                            "min_value": attribute.definition.data_type.min_value,
                                            "max_value": attribute.definition.data_type.max_value,
                                        },
                                        "qualities": [
                                            q.name for q in FieldQuality if q & attribute.definition.qualities
                                        ],
                                    },
                                    "storage": find_attribute_instantiation_by_name(
                                        attribute.definition.name, cluster
                                    ).storage.name
                                    if find_attribute_instantiation_by_name(attribute.definition.name, cluster)
                                    else "NA",  # Handle NoneType by providing a default value or skipping
                                    "default": find_attribute_instantiation_by_name(
                                        attribute.definition.name, cluster
                                    ).default
                                    if find_attribute_instantiation_by_name(attribute.definition.name, cluster)
                                    else "NA",  # Include default value, handle NoneType
                                    "qualities": [q.name for q in AttributeQuality if q & attribute.qualities],
                                    "readacl": attribute.readacl.name,
                                    "writeacl": attribute.writeacl.name,
                                    "api_maturity": attribute.api_maturity.name,
                                }
                                for attribute in find_cluster_by_name(cluster.name, parsed_idl.clusters).attributes
                                if attribute.definition.name
                                in instantiated_attributes.get(endpoint.number, {}).get(cluster.name, set())
                            ],
                            "commands": [
                                {
                                    "name": command.name,
                                    "code": command.code,
                                    "input_param": command.input_param,
                                    "output_param": command.output_param,
                                    "qualities": [q.name for q in CommandQuality if q & command.qualities],
                                    "invokeacl": command.invokeacl.name,
                                    "api_maturity": command.api_maturity.name,
                                }
                                for command in find_cluster_by_name(cluster.name, parsed_idl.clusters).commands
                                if command.name
                                in instantiated_commands.get(endpoint.number, {}).get(cluster.name, set())
                            ],
                            "events": [
                                {"name": event.name, "code": event.code}
                                for event in find_cluster_by_name(cluster.name, parsed_idl.clusters).events
                                if event.name in instantiated_events.get(endpoint.number, {}).get(cluster.name, set())
                            ],
                        }
                        for cluster in endpoint.server_clusters
                    ],
                }
                for endpoint in parsed_idl.endpoints
            ]
        }
    }

    for endpoint in data_model["data_model"]["endpoints"]:
        for cluster in endpoint["clusters"]:
            cluster_def = find_cluster_by_name(cluster["name"], parsed_idl.clusters)
            for attribute in cluster["attributes"]:
                bounds = bounds_lookup.get_min_max(cluster_def.code, attribute["definition"]["code"])
                if bounds:
                    attribute["definition"]["bounds"] = bounds
                struct_def = find_struct_by_name(
                    attribute["definition"]["type"]["name"],
                    getattr(cluster_def, "structs", []),
                )
                if struct_def:
                    attribute["definition"]["type"]["fields"] = [
                        {
                            "name": field.name,
                            "type": field.data_type.name,
                            "code": field.code,
                            "qualities": [q.name for q in FieldQuality if q & field.qualities],
                        }
                        for field in struct_def.fields
                    ]
                    attribute["definition"]["is_struct"] = True
                else:
                    attribute["definition"]["is_struct"] = False
                if "Enum" in attribute["definition"]["type"]["name"]:
                    enum_def = find_enum_by_name(attribute["definition"]["type"]["name"], cluster_def.enums)
                    if enum_def:
                        attribute["definition"]["type"]["base_type"] = enum_def.base_type
                        attribute["definition"]["type"]["entries"] = [
                            {"name": entry.name, "code": entry.code} for entry in enum_def.entries
                        ]
                elif (
                    attribute["definition"]["name"] == "featureMap"
                    or "bitmap" in attribute["definition"]["type"]["name"].lower()
                ):
                    bitmap_name = (
                        "Feature"
                        if attribute["definition"]["name"] == "featureMap"
                        else attribute["definition"]["type"]["name"]
                    )
                    bitmap_def = find_bitmap_by_name(bitmap_name, cluster_def.bitmaps)
                    if bitmap_def:
                        attribute["definition"]["type"]["base_type"] = bitmap_def.base_type
                        attribute["definition"]["type"]["entries"] = [
                            {"name": entry.name, "code": entry.code} for entry in bitmap_def.entries
                        ]
            for command in cluster["commands"]:
                if command["output_param"] != "DefaultSuccess":
                    struct_def = find_struct_by_name(command["output_param"], cluster_def.structs)
                    if struct_def:
                        command["generated"] = {
                            "name": struct_def.name,
                            "code": struct_def.code,
                        }

    return data_model


def create_json_data_model(idl_file_path, json_file_path, attribute_bounds_pkl_path):
    idl_text = load_idl_text(idl_file_path)
    json_data_model = generate_json_data_model(idl_text, attribute_bounds_pkl_path)

    with open(json_file_path, "w") as json_file:
        json.dump(json_data_model, json_file, indent=4)

    print(f"JSON file written to: {json_file_path}")
