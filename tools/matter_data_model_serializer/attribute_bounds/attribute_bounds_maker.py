# SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
import csv
import os
import pickle
import xml.etree.ElementTree as ET


def hex_to_int(value):
    try:
        if value.startswith("0x"):
            return int(value, 16)
        else:
            return int(value)
    except ValueError:
        return value


def extract_attributes(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    attributes = []

    for cluster in root.findall(".//cluster"):
        cluster_id = cluster.find("code").text if cluster.find("code") is not None else None
        for attribute in cluster.findall(".//attribute[@min][@max]"):
            attribute_id = attribute.get("code")
            min_value = attribute.get("min")
            max_value = attribute.get("max")
            attributes.append(
                {
                    "cluster_id": cluster_id,
                    "attribute_id": attribute_id,
                    "min": min_value,
                    "max": max_value,
                }
            )

    return attributes


def process_directories(directories, output_csv, output_pickle):
    all_attributes = []

    for directory in directories:
        for filename in os.listdir(directory):
            if filename.endswith(".xml"):
                file_path = os.path.join(directory, filename)
                attributes = extract_attributes(file_path)
                all_attributes.extend(attributes)

    # Write to CSV
    with open(output_csv, "w", newline="") as csvfile:
        fieldnames = ["cluster_id", "attribute_id", "min", "max"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_attributes)

    # Create lookup table and write to pickle
    lookup_table = {}
    for attr in all_attributes:
        cluster_id = hex_to_int(attr["cluster_id"])
        attribute_id = hex_to_int(attr["attribute_id"])
        min_value = hex_to_int(attr["min"])
        max_value = hex_to_int(attr["max"])

        if cluster_id not in lookup_table:
            lookup_table[cluster_id] = {}
        lookup_table[cluster_id][attribute_id] = {"min": min_value, "max": max_value}

    with open(output_pickle, "wb") as pfile:
        pickle.dump(lookup_table, pfile)


if __name__ == "__main__":
    directories = [
        os.path.expandvars(
            os.path.join(
                "$ESP_MATTER_PATH",
                "connectedhomeip",
                "connectedhomeip",
                "src",
                "app",
                "zap-templates",
                "zcl",
                "data-model",
                "chip",
            )
        ),
        # add more directories if needed
    ]
    output_csv = "attribute_bounds.csv"
    output_pickle = "attribute_bounds.pkl"
    process_directories(directories, output_csv, output_pickle)
