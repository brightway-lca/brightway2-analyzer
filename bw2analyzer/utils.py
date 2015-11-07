# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division
from eight import *

from time import time
from bw2calc import LCA
from bw2data import Database, methods, databases, mapping, Method, config
import numpy as np
import pyprind


def contribution_for_all_datasets_one_method(database, method, progress=True):
    """Calculate contribution analysis (for technosphere processes) for all inventory datasets in one database for one LCIA method.

    Args:
        *database* (str): Name of database
        *method* (tuple): Method tuple

    Returns:
        NumPy array of relative contributions. Each column sums to one.
        Lookup dictionary, dataset keys to row/column indices
        Total elapsed time in seconds

    """
    def get_normalized_scores(lca, kind):
        if kind == "activities":
            data = lca.characterized_inventory.sum(axis=0)
        elif kind == "flows":
            data = lca.characterized_inventory.sum(axis=1)
        elif kind == "all":
            data = lca.characterized_inventory.data
        scores = np.abs(np.array(data).ravel())
        summed = scores.sum()
        if summed == 0:
            return np.zeros(scores.shape)
        else:
            return scores / summed

    start = time()
    assert database in databases, "Can't find database %s" % database
    assert method in methods, "Can't find method %s" % method
    keys = Database(database).load().keys()
    assert keys, "Database %s appears to have no datasets" % database

    # Array to store results
    results = np.zeros((len(keys), len(keys)), dtype=np.float32)

    # Instantiate LCA object
    lca = LCA({keys[0]: 1}, method=method)
    lca.lci()
    lca.decompose_technosphere()
    lca.lcia()

    rows = lca.characterized_inventory.shape[0]
    cols = lca.characterized_inventory.shape[1]
    all_cutoff = cols * 4

    results = {
        'activities': np.zeros((cols, cols), dtype=np.float32),
        'flows': np.zeros((rows, cols), dtype=np.float32),
        'all': np.zeros((all_cutoff, cols), dtype=np.float32)
    }

    pbar = pyprind.ProgBar(len(keys), title="Activities:")

    # Actual calculations
    for key in keys:
        lca.redo_lcia({key: 1})
        if lca.score == 0.:
            continue

        col = lca.activity_dict[mapping[key]]
        results['activities'][:, col] = get_normalized_scores(lca, 'activities')
        results['flows'][:, col] = get_normalized_scores(lca, 'flows')
        results_all = get_normalized_scores(lca, 'all')
        results_all.sort()
        results_all = results_all[::-1]
        fill_number = results_all.shape[0]
        assert fill_number < all_cutoff, "Too many values in 'all'"
        results['all'][:fill_number, col] = results_all

        pbar.update()

    print(pbar)

    return results, lca.activity_dict, time() - start


def group_by_emissions(method):
    """Group characterization factors by name, realm, and unit.

    **realm** is the general category, e.g. air, soil, water.

    Does not work on regionalized LCIA methods!

    Args:
        *method* (tuple or Method): LCIA method

    Returns:
        Dictionary: {(name, realm, unit)}: [cfs... ]

    """
    if isinstance(method, Method):
        data = method.load()
    elif isinstance(method, tuple):
        data = Method(method).load()
    else:
        raise ValueError("Can't interpret %s as a LCIA method" % method)

    biosphere = Database(config.biosphere).load()
    grouped = {}

    for key, cf, geo in data:
        if geo != config.global_location:
            raise ValueError(
                "`group_by_emissions` doesn't work on regionalized methods"
            )
        if key[0] != config.biosphere:
            # Alternative biosphere, e.g. Ecoinvent 3. Add new biosphere DB
            biosphere.update(Database(key[0]).load())
        flow = biosphere[key]
        label = (
            flow.get("name", "Unknown"),
            flow.get("categories", [""])[0],
            flow.get("unit", "Unknown")
        )
        grouped.setdefault(label, []).append(cf)

    return grouped
