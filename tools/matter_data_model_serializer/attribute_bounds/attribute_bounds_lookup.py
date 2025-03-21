# SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
import pickle


class BoundsLookup:
    def __init__(self, pickle_file):
        with open(pickle_file, "rb") as pfile:
            self.lookup_table = pickle.load(pfile)

    def get_min_max(self, cluster_id, attribute_id):
        cluster_id = int(cluster_id)
        attribute_id = int(attribute_id)

        if cluster_id in self.lookup_table and attribute_id in self.lookup_table[cluster_id]:
            return self.lookup_table[cluster_id][attribute_id]
        else:
            return None
