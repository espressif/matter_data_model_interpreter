/*
 * SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef DATA_MODEL_MANAGER_HPP
#define DATA_MODEL_MANAGER_HPP

#include <vector>
#include <cstddef>

#include "data_model_storage.hpp"

namespace data_model_manager {

/**
 * @brief Manager class that orchestrates the retrieval (and later update)
 *        of the data model binary.
 *
 * This class uses an underlying storage implementation (via IDataModelStorage)
 * to load the data model binary. It handles the key selection and fallback logic.
 */
class DataModelManager {
public:
    /**
     * @brief Construct a DataModelManager with a storage object.
     *
     * @param storage Reference to an object implementing IDataModelStorage.
     */
    DataModelManager(IDataModelStorage &storage);
    ~DataModelManager();

    /**
     * @brief Get the data model binary.
     *
     * This function retrieves the data model binary from storage using a key constructed
     * from the current running partition label. If that key is not found,
     * it falls back to the key "ota_0_dm" and renames it.
     *
     * @param[out] data_model_binary_size Output parameter for the binary size.
     * @return A vector containing the data model binary. An empty vector indicates an error.
     */
    std::vector<uint8_t> get_data_model_binary(size_t &data_model_binary_size);

private:
    class IDataModelStorage &storage_;
};

} // namespace data_model_manager

#endif // DATA_MODEL_MANAGER_HPP
