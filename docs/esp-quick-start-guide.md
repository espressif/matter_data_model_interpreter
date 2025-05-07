# Quick Start Guide

This guide explains how to build a Matter application for an Espressif SoC using the data model interpreter and serializer tools contained in this repository.

---

## 1. Pre-requisites / Assumptions

1. **Data Model File:**
   You already have a data model available in either **.zap** or **.matter** format.  
   If not, please see the [ZAP documentation](https://github.com/project-chip/connectedhomeip/blob/master/docs/zap_and_codegen/zap_intro.md).  

   > [!IMPORTANT]
   > Your data model must be created using the same Matter version that you intend to use in your application.

2. **ESP-IDF Setup:**
   You have set up ESP-IDF and can build any standard esp-matter example (e.g., the [light example](https://github.com/espressif/esp-matter/tree/main/examples/light)).  
   If not, please follow the instructions at [ESP-Matter Development Guide](https://docs.espressif.com/projects/esp-matter/en/latest/esp32/developing.html).  
   
   > [!NOTE]
   > The components and tools in this repository are designed to work with recent and future releases of Matter.  
   > It has been tested with [release/v1.4](https://github.com/espressif/esp-matter/tree/release/v1.4) and [release/v1.3](https://github.com/espressif/esp-matter/tree/release/v1.3) of `esp-matter`, corresponding to Matter 1.4 and 1.3 respectively.

3. **Environment Configuration:**
   If you want to build a Matter application for an Espressif SoC, this repository assumes that you have exported the environment variable `$ESP_MATTER_PATH`.  
   To ensure this, follow the steps under "2.2.1.2 Configuring the Environment" in the [ESP-Matter documentation](https://docs.espressif.com/projects/esp-matter/en/latest/esp32/developing.html#id2).

---

## 2. Steps to Build and Run the Example

1. **Clone the Repository:**

```bash
git clone https://github.com/espressif/matter_data_model_interpreter.git
```

2. **Change to the Example Directory:**
```bash
cd matter_data_model_interpreter/examples/any_device
```

3. **Set the Target SoC:**
```bash
idf.py set-target <SoC>
```

4. **Build, Flash, and Monitor:**
```bash
idf.py build flash monitor
```

After the device boots up, you should see log output similar to:
```
I (966) app_main: Looking for NVS key: 'ota_0_dm'
W (986) app_main: Key 'ota_0_dm' not found; trying fallback key 'ota_0_dm'
E (986) app_main: Fallback key 'ota_0_dm' not found (4354)
E (986) app_main: Failed to load data model from NVS
I (996) main_task: Returned from app_main()
```

## 3. Generating the Data Model Binary and Flashing It

1. **Change to the Serializer Directory:**

```bash
cd matter_data_model_interpreter/tools/matter_data_model_serializer
```

2. **Install Python Dependencies:**

```bash
pip install -r requirements.txt
```
3. **Run the Serializer:**

  - For a .zap file:

    - ```bash
      python matter_data_model_serializer.py -z /path/to/your/data_model.zap

  - For a .matter file:

    - ```bash
      python matter_data_model_serializer.py -m /path/to/your/data_model.matter
      ```
4. **Locate the Generated Binary:**
The script generates the data model binary in the `serializer_output/` directory at the same level.  
At the end of the run, you will see output similar to:
```
NVS partition binary: matter_data_model_interpreter/tools/matter_data_model_serializer/serializer_output/<data-model-filename>/<data-model-filename>.nvs.bin
```
5. **Flash the Data Model Binary:**
    The `esp_matter_dm` partition is located at the 0x3E6000 offset by default.  
    To flash the binary, use:

```bash
esptool.py write_flash 0x3E6000 /path/to/<data-model-filename>.nvs.bin
```

6. **Reset the Device:**
After flashing the data model, reset the device.  
On boot, it should initialize the data model and you will see a log message like:
```
I (1843) app_main: Commissioning window opened
```

## 4. Limitations of the `esp_matter_data_model_interpreter` component

1. Client clusters are not supported.
2. For the clusters that [require a delegate](https://docs.espressif.com/projects/esp-matter/en/latest/esp32/app_guide.html#delegate-implementation) implementation, you will have to implement the delegate and set it using the [`set_delegate_and_init_callback`](https://github.com/espressif/esp-matter/blob/b6a21bcc2400575c7bcc323a05de83110afd5c21/components/esp_matter/esp_matter_core.h#L501) API.
