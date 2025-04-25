# Serializer Only Guide

It is possible to run the python `matter_data_model_serializer` without setting up or downloading esp-matter and ESP-IDF. (Only cloning the `connectedhomeip` repo is required.)

This is useful if you only want to generate the data model binary.

---

## 1. Cloning the Repositories

```bash
git clone https://github.com/espressif/matter_data_model_interpreter.git
```

```bash
git clone https://github.com/project-chip/connectedhomeip.git
```

*(There is no need to initialize or clone the submodules of the `connectedhomeip` repo)*

## 2. Pre-Requisite Setup

- **For a `.matter` file:**  
  No additional setup is required before running the tool.
- **For a `.zap` file:**  
  You need to install the ZAP tool. You can either:
  - Follow the instructions in the [connectedhomeip BUILDING guide](https://github.com/project-chip/connectedhomeip/blob/master/docs/guides/BUILDING.md#installing-zap-tool), or
  - Download a ZAP release from [zap/releases](https://github.com/project-chip/zap/releases) and set the `ZAP_INSTALL_PATH` environment variable to point to where the zap release (e.g., `zap-linux-x64.zip`) was unpacked.

## 3. Change to the Serializer Directory

```bash
cd matter_data_model_interpreter/tools/matter_data_model_serializer
```

## 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## 5. Run the Serializer

> [!NOTE]
> The commands given below include the `--no-nvs-bin` argument to provide the raw data model binary to the user.

- **For a `.zap` file:**

  ```bash
  python matter_data_model_serializer.py -z /path/to/your/data_model.zap --chip-sdk-path /path/to/cloned/connectedhomeip --no-nvs-bin
  ```

- **For a `.matter` file:**

  ```bash
  python matter_data_model_serializer.py -m /path/to/your/data_model.matter --chip-sdk-path /path/to/cloned/connectedhomeip --no-nvs-bin
  ```

## 6. Locate the Generated Binary

After the script finishes, it generates the data model binary in the `serializer_output/` directory.  
At the end of the run, you will see output similar to:

```
- Binary file: matter_data_model_interpreter/tools/matter_data_model_serializer/serializer_output/<data-model-filename>/<data-model-filename>.bin
```

This binary file is now ready for use.
