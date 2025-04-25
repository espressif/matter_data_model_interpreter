# Matter Data Model Interpreter

## Table of Contents

- [What Does This Repository Contain?](#what-does-this-repository-contain)
- [Current Use Cases](#current-use-cases)
  - [Potential Use Cases](#potential-use-cases)
- [How Do I Get Started?](#how-do-i-get-started)
  - [Build a Matter Application for Espressif SoC](#build-a-matter-application-for-espressif-soc)
  - [Run the `matter_data_model_serializer` only](#run-the-matter_data_model_serializer-only)
- [How Does It Work?](#how-does-it-work)
  - [Why Use Protobufs?](#why-use-protobufs)
  - [Limitations](#limitations)

## What Does This Repository Contain?

This repository is home to:

1. **Data Model Serialization Tools:**  
   A set of tools that serialize standard Matter data model formats (`.zap` and `.matter`) into a stream of function calls and encode them into a platform-agnostic *data model binary*.

2. ***Interpreter* ESP-IDF Component and esp-matter Example:**  
   An IDF component and an esp-matter example that can read and interpret the *data model binary*, enabling you to build a Matter application independent of the data model and to flash the data model separately.

## Current Use Cases

- **Decoupled Development:**  
  It offers you the flexibility of developing your application once and iterating on the data model separately.

- **Leverage ZAP Tool Capabilities:**  
  esp-matter users can benefit from the modeling capabilities of the ZAP tool while still using esp-matter's dynamic data model.

- **Espressif LowCode Solutions:**  
  Espressif's [ExL (Hosted)](https://zerocode.espressif.com/exl) and [LowCode](https://github.com/espressif/esp-lowcode-matter) solutions use the Matter Data Model Interpreter.

### Potential Use Cases

- **Eliminate Code Generators:**  
  Matter implementations in other languages can read and interpret the data model binary instead of using or implementing code generators for the data model.

## How Do I Get Started?

### Build a Matter Application for Espressif SoC

Please refer to the [Quick Start Guide](docs/esp-quick-start-guide.md) for instructions on building a Matter application for Espressif SoC.

### Run the `matter_data_model_serializer` Only

For details on running just the serializer, see the [Serializer Only Guide](docs/run-serializer-only.md).

## How Does It Work?

1. The Matter data model is a well-defined hierarchical representation of a device, consisting of:
```
Matter Device
`-- Endpoint
    |-- Device Types
    `-- Clusters
        |-- Attributes
        |-- Commands
        `-- Events
```
2. Assume that each of these can be created using a function call like:
```c
create_endpoint(endpoint_id);
create_cluster(endpoint_id, cluster_id);
...
```

3. The `matter_data_model_serializer` python tool converts a standard Matter data model (`.zap` or `.matter` file) into a serialized stream of such function calls (with parameters).

   - These calls are then encoded as protobuf messages and stored in a binary file using a `<length><value>` format.

   - This binary can be flashed or stored in a separate partition, entirely independent of the application.

4. The `esp_matter_data_model_interpreter` component (or equivalent) deserializes the binary and executes the function calls to initialize the Matter data model.

### Why Use Protobufs?
- **Platform Agnostic:**
The data model binary is platform independent.

- **Language Flexibility:**
Any language with a protobuf compiler can generate deserialization code, enabling broad interoperability.

- **Space Efficiency:**
Typical data model binary size is less than 5KB.

- **Compatibility and Extensibility:**
Protobufs offer backward and forward compatibility friendliness, making future extensions straightforward.

### Limitations
- **Parent Endpoint Information**
Currently, the `.zap` to `.matter` conversion process doesn't preserve the parent endpoint information.
Support for providing this information will be available in a future release.
