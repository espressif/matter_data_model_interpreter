# SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace


def modify_zap_file(zap_file: Path, chip_sdk_root: Path):
    """
    Modifies the given .zap file (JSON) so that in its "package" list:
      - Each package's "pathRelativity" is set to "absolute".
      - The first package's "path" is set to "<chip_sdk_root>/src/app/zap-templates/zcl/zcl.json".
      - The second package's "path" is set to "<chip_sdk_root>/src/app/zap-templates/app-templates.json".
    """
    prefix = str(chip_sdk_root)
    try:
        with zap_file.open("r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {zap_file}: {e}")
        sys.exit(1)
    if "package" in data and isinstance(data["package"], list):
        packages = data["package"]
        if len(packages) >= 1:
            packages[0]["pathRelativity"] = "absolute"
            packages[0]["path"] = f"{prefix}/src/app/zap-templates/zcl/zcl.json"
        if len(packages) >= 2:
            packages[1]["pathRelativity"] = "absolute"
            packages[1]["path"] = f"{prefix}/src/app/zap-templates/app-templates.json"
    else:
        print("No package information found in the .zap file.")
        sys.exit(1)
    try:
        with zap_file.open("w") as f:
            json.dump(data, f, indent=2)
        print(f"Modified {zap_file} successfully.")
    except Exception as e:
        print(f"Error writing {zap_file}: {e}")
        sys.exit(1)


def run_generate_script(zap_dest: Path, out_dir: Path, chip_sdk_root: Path):
    """
    Runs the generate.py script (located in chip_sdk_root/scripts/tools/zap) to convert a .zap file to a .matter file.
    """
    generate_script_dir = chip_sdk_root / "scripts" / "tools" / "zap"
    generate_script = generate_script_dir / "generate.py"
    if not generate_script.exists():
        print(f"Generate script not found at {generate_script}")
        sys.exit(1)
    sys.path.insert(0, str(generate_script_dir))
    try:
        import generate
    except ImportError as e:
        print(f"Error importing generate module: {e}")
        sys.exit(1)
    original_argv = sys.argv
    sys.argv = [str(generate_script), "-o", str(out_dir), str(zap_dest)]
    print(f"Running generate.py with arguments: {sys.argv}")
    try:
        generate.main()
    except Exception as e:
        print(f"Error while running generate.py: {e}")
        sys.exit(1)
    finally:
        sys.argv = original_argv
        sys.path.pop(0)


def ensure_attribute_files(output_csv: Path, output_pickle: Path, chip_sdk_root: Path):
    """
    Ensure that the specified output_csv and output_pickle files exist.
    If they do not exist, attempt to generate them using XMLs from chip_sdk_root.

    Args:
        output_csv (Path): The path where the CSV file should be located.
        output_pickle (Path): The path where the pickle file should be located.
        chip_sdk_root (Path): The root directory containing the attribute data.

    Returns:
        bool: True if both files exist after the attempt, False otherwise.
    """

    def check_files_exist(file_paths):
        return all(path.exists() for path in file_paths)

    if not check_files_exist([output_csv, output_pickle]):
        print(f"{output_csv} or {output_pickle} not found, generating them...")
        from attribute_bounds.attribute_bounds_maker import process_directories

        directories = [chip_sdk_root / "src" / "app" / "zap-templates" / "zcl" / "data-model" / "chip"]
        process_directories([str(d) for d in directories], str(output_csv), str(output_pickle))

    return check_files_exist([output_csv, output_pickle])


def run_linter(idl_path: Path, chip_sdk_root: Path) -> None:
    """
    Invoke the Matter IDL linter, using either the legacy `idl_lint` module
    or the new `matter-idl-lint` CLI.

    Args:
        idl_path (Path):      Path to the `.matter` file to lint.
        chip_sdk_root (Path): Path to the repo root (where `.matterlint` lives).

    The function will:
      1. Try importing and running `idl_lint.main()`.
      2. On ImportError, fall back to `matter.idl.lint.main()`,
         automatically pointing `--rules` at chip_sdk_root/.matterlint.
    """
    # 1) Attempt the legacy linter
    try:
        import idl_lint

        linter_main = idl_lint.main
        script_name = "idl_lint.py"
        cli_args = []  # legacy linter already knows where its rules live
    except ImportError:
        # 2) Fallback to the newer CLI
        try:
            from matter.idl.lint import main as linter_main

            script_name = "matter-idl-lint"
        except ImportError as e:
            print(f"Error importing any linter backend: {e}")
            sys.exit(1)

        # Point `--rules` at the .matterlint file in the repo root
        rules_file = chip_sdk_root / ".matterlint"
        cli_args = ["--rules", str(rules_file)]

    # Temporarily replace sys.argv so `matter-idl-lint` will parse our args
    original_argv = sys.argv
    sys.argv = [script_name, *cli_args, str(idl_path)]

    try:
        linter_main()
    except SystemExit as e:
        if e.code != 0:
            print(f"Linter exited with code: {e.code}")
            sys.exit(e.code)
    except Exception as e:
        print(f"An error occurred during linting: {e}")
        sys.exit(1)
    finally:
        # Restore the original argv so we don’t pollute later code
        sys.argv = original_argv


def generate_nvs_input_csv(out_dir: Path, data_model_bin: Path) -> Path:
    """
    Generate a CSV file with the following content:
      key,type,encoding,value
      em_data_model,namespace,,
      ota_0_dm,file,binary,<absolute path to data_model_bin>
    """
    csv_path = out_dir / "nvs_input.csv"
    content = (
        "key,type,encoding,value\n"
        "em_data_model,namespace,,\n"
        f"ota_0_dm,file,binary,{str(data_model_bin.resolve())}\n"
    )
    try:
        with csv_path.open("w") as f:
            f.write(content)
        print(f"NVS input CSV generated at: {csv_path}")
    except Exception as e:
        print(f"Error writing NVS input CSV: {e}")
        sys.exit(1)
    return csv_path


def gen_nvs_partition_bin(
    nvs_partition_gen_module,
    filedir: str,
    output_bin_filename: str,
    output_encrypted_bin_filename: str,
    nvs_input_csv_filename: str,
    no_unencrypted_fctry: bool,
):
    if not no_unencrypted_fctry:
        nvs_args = SimpleNamespace(
            input=nvs_input_csv_filename,
            output=output_bin_filename,
            size="0x6000",
            outdir=filedir,
            version=2,
        )
        print("Generating NVS Partition Binary: " + os.path.join(filedir, output_bin_filename))
        nvs_partition_gen_module.generate(nvs_args)
