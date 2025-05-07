#!/usr/bin/env python
# SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

"""
matter_data_model_serializer.py

Usage:
    python matter_data_model_serializer.py -z <path_to_.zap_file> [--chip-sdk-path <chip_sdk_root>] [--no-nvs-bin]
    python matter_data_model_serializer.py -m <path_to_.matter_file> [--chip-sdk-path <chip_sdk_root>] [--no-nvs-bin]

"""

import argparse
import os
import sys
from pathlib import Path
from shutil import copy2


def setup_matter_paths(chip_sdk_root: Path = None) -> Path:
    """
    Adds Matter-related directories to sys.path.

    If chip_sdk_root is provided explicitly (via --chip-sdk-path), it is assumed to already be
    the correct root (i.e. it contains 'scripts' and 'py_matter_idl').
    Otherwise, it falls back to ESP_MATTER_PATH and appends "connectedhomeip/connectedhomeip".

    Returns the final chip_sdk_root value used.
    """
    if chip_sdk_root is None:
        chip_env = os.getenv("ESP_MATTER_PATH")
        if chip_env is None:
            print("Error: Neither --chip-sdk-path provided, nor ESP_MATTER_PATH is set.")
            sys.exit(1)
        chip_sdk_root = Path(chip_env) / "connectedhomeip" / "connectedhomeip"
    else:
        chip_sdk_root = Path(chip_sdk_root)

    script_path = chip_sdk_root / "scripts"
    matter_idl_path = script_path / "py_matter_idl"
    sys.path.extend([str(script_path), str(matter_idl_path)])
    return chip_sdk_root


def parse_args():
    parser = argparse.ArgumentParser(description="Tool to convert and serialize Matter Data Model")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-z", "--zap", help="Path to .zap file", type=str)
    group.add_argument("-m", "--matter", help="Path to .matter file", type=str)
    parser.add_argument(
        "--chip-sdk-path",
        help="Path to connectedhomeip SDK root (if not using esp-matter)",
        type=str,
    )
    parser.add_argument("--no-nvs-bin", help="Do not generate NVS partition binary", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    # Determine chip_sdk_root from --chip-sdk-path or use None to trigger fallback.
    if args.chip_sdk_path:
        chip_sdk_root = Path(args.chip_sdk_path)
    else:
        chip_sdk_root = None
    chip_sdk_root = setup_matter_paths(chip_sdk_root)

    from matter_data_model_conversion.create_json import create_json_data_model
    from matter_data_model_conversion.create_binary import create_binary_file
    from utils.matter_data_model_serializer_helpers import (
        modify_zap_file,
        run_generate_script,
        ensure_attribute_files,
        run_linter,
        generate_nvs_input_csv,
        gen_nvs_partition_bin,
    )

    # Determine input type and file.
    if args.zap:
        file_type = "zap"
        input_file = Path(args.zap)
    else:
        file_type = "matter"
        input_file = Path(args.matter)

    if not input_file.exists():
        print(f"File not found: {input_file}")
        sys.exit(1)

    # Create output directories.
    out_dir = Path("serializer_output").resolve()
    out_dir.mkdir(exist_ok=True)
    sub_out_dir = out_dir / input_file.stem
    sub_out_dir.mkdir(exist_ok=True)

    if file_type == "zap":
        # Copy and modify the .zap file.
        zap_dest = (sub_out_dir / input_file.name).resolve()
        copy2(input_file, zap_dest)
        print(f"Copied {input_file} to {zap_dest}")
        modify_zap_file(zap_dest, chip_sdk_root)

        # Run generate.py to convert the .zap file to a .matter file.
        run_generate_script(zap_dest, sub_out_dir, chip_sdk_root)
        matter_file = sub_out_dir / (input_file.stem + ".matter")
        if not matter_file.exists():
            print(f"Failed to generate .matter file: {matter_file}")
            sys.exit(1)
        print(f"Generated .matter file: {matter_file}")
    else:
        # For a .matter input, simply copy it to the output directory.
        matter_file = (sub_out_dir / input_file.name).resolve()
        copy2(input_file, matter_file)
        print(f"Copied {input_file} to {matter_file}")

    # Process the .matter file.

    # Create the attribute_bounds files (for looking up attribute bounds)
    attr_csv = out_dir / "attribute_bounds.csv"
    attr_pickle = out_dir / "attribute_bounds.pkl"
    ensure_attribute_files(attr_csv, attr_pickle, chip_sdk_root)

    # Run the linter on the .matter file
    run_linter(matter_file, chip_sdk_root)
    json_file_path = sub_out_dir / (input_file.stem + ".json")

    # Pass attribute_bounds pickle file to create_json_data_model
    create_json_data_model(matter_file, json_file_path, attr_pickle)
    print(f"Created JSON data model: {json_file_path}")

    # Convert the data model JSON to a binary file (containing proto messages)
    bin_file_path = sub_out_dir / (input_file.stem + ".bin")
    create_binary_file(json_file_path, bin_file_path)
    print(f"Created binary file: {bin_file_path}")

    # Optionally generate the NVS partition binary.
    if not args.no_nvs_bin:
        try:
            import esp_idf_nvs_partition_gen.nvs_partition_gen as nvs_partition_gen
        except ImportError:
            if os.getenv("IDF_PATH"):
                sys.path.insert(
                    0,
                    os.path.join(
                        os.getenv("IDF_PATH"),
                        "components",
                        "nvs_flash",
                        "nvs_partition_generator",
                    ),
                )
                try:
                    import esp_idf_nvs_partition_gen.nvs_partition_gen as nvs_partition_gen
                except ImportError:
                    print("Failed to import NVS partition generator even after inserting IDF_PATH. Exiting.")
                    sys.exit(1)
            else:
                print("Please set the IDF_PATH environment variable.")
                sys.exit(1)
        nvs_csv = generate_nvs_input_csv(sub_out_dir, bin_file_path)
        gen_nvs_partition_bin(
            nvs_partition_gen,
            filedir=str(sub_out_dir),
            output_bin_filename=input_file.stem + ".nvs.bin",
            output_encrypted_bin_filename=input_file.stem + ".nvs.encrypted.bin",
            nvs_input_csv_filename=str(nvs_csv),
            no_unencrypted_fctry=False,
        )
    else:
        print("Skipping NVS partition binary generation as per --no-nvs-bin flag.")

    print("Serialization complete. The output directory contains:")
    if file_type == "zap":
        print(f" - Original .zap file: {zap_dest}")
    else:
        print(f" - Provided .matter file: {matter_file}")
    print(f" - Generated .matter file: {matter_file}")
    print(f" - JSON data model: {json_file_path}")
    print(f" - Binary file: {bin_file_path}")
    if not args.no_nvs_bin:
        print(f" - NVS partition binary: {sub_out_dir / (input_file.stem + '.nvs.bin')}")
    else:
        print(" - NVS partition binary: (not generated)")


if __name__ == "__main__":
    main()
