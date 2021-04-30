from bw2data import Database, methods, databases, mapping, Method, config
from time import time
import bw2calc as bc
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
    lca = bc.LCA({keys[0]: 1}, method=method)
    lca.lci()
    lca.decompose_technosphere()
    lca.lcia()

    rows = lca.characterized_inventory.shape[0]
    cols = lca.characterized_inventory.shape[1]
    all_cutoff = cols * 4

    results = {
        "activities": np.zeros((cols, cols), dtype=np.float32),
        "flows": np.zeros((rows, cols), dtype=np.float32),
        "all": np.zeros((all_cutoff, cols), dtype=np.float32),
    }

    pbar = pyprind.ProgBar(len(keys), title="Activities:")

    # Actual calculations
    for key in keys:
        lca.redo_lcia({key: 1})
        if lca.score == 0.0:
            continue

        col = lca.activity_dict[mapping[key]]
        results["activities"][:, col] = get_normalized_scores(lca, "activities")
        results["flows"][:, col] = get_normalized_scores(lca, "flows")
        results_all = get_normalized_scores(lca, "all")
        results_all.sort()
        results_all = results_all[::-1]
        fill_number = results_all.shape[0]
        assert fill_number < all_cutoff, "Too many values in 'all'"
        results["all"][:fill_number, col] = results_all

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
            flow.get("unit", "Unknown"),
        )
        grouped.setdefault(label, []).append(cf)

    return grouped


def print_recursive_calculation(activity, lcia_method, amount=1, max_level=3, cutoff=1e-2, file_obj=None, tab_character="  ", level=0, lca_obj=None, total_score=None, first=True, ):
    """Traverse a supply chain graph, and calculate the LCA scores of each component. Prints the result with the format:

    {tab_character * level }{fraction of total score} ({absolute LCA score for this input} | {amount of input}) {input activity}

    Args:
        activity: ``Activity``. The starting point of the supply chain graph.
        lcia_method: tuple. LCIA method to use when traversing supply chain graph.
        amount: int. Amount of ``activity`` to assess.
        max_level: int. Maximum depth to traverse.
        cutoff: float. Fraction of total score to use as cutoff when deciding whether to traverse deeper.
        file_obj: File-like object (supports ``.write``), optional. Output will be written to this object if provided.
        tab_character: str. Character to use to indicate indentation.

    Internal args (used during recursion, do not touch);
        level: int.
        lca_obj: ``LCA``.
        total_score: float.
        first: bool.

    Returns:
        Nothing. Prints to ``sys.stdout`` or ``file_obj``

    """

    if lca_obj is None:
        lca_obj = bc.LCA({activity: amount}, lcia_method)
        lca_obj.lci()
        lca_obj.lcia()
        total_score = lca_obj.score
    elif total_score is None:
        raise ValueError
    else:
        lca_obj.redo_lcia({activity: amount})
        if abs(lca_obj.score) <= abs(total_score * cutoff):
            return
    if first:
        message = "Fraction of score | Absolute score | Amount | Activity"
        if file_obj is not None:
            file_obj.write(message + "\n")
        else:
            print(message)
    message = "{}{:04.3g} | {:5.4n} | {:5.4n} | {:.70}".format(tab_character * level, lca_obj.score / total_score, lca_obj.score, float(amount), str(activity))
    if file_obj is not None:
        file_obj.write(message + "\n")
    else:
        print(message)
    if level < max_level:
        for exc in activity.technosphere():
            print_recursive_calculation(
                activity=exc.input,
                lcia_method=lcia_method,
                amount=amount * exc['amount'],
                max_level=max_level,
                cutoff=cutoff,
                first=False,
                file_obj=file_obj,
                tab_character=tab_character,
                lca_obj=lca_obj,
                total_score=total_score,
                level=level + 1,
            )


def print_recursive_supply_chain(activity, amount=1, max_level=2, cutoff=0, file_obj=None, tab_character="  ", level=0):
    """Traverse a supply chain graph, and prints the inputs of each component.

    This function is only for exploration; use ``bw2calc.GraphTraversal`` for a better performing function.

    Args:
        activity: ``Activity``. The starting point of the supply chain graph.
        amount: int. Supply chain inputs will be scaled to this value.
        max_level: int. Max depth to search for.
        cutoff: float. Inputs with amounts less than ``amount * cutoff`` will not be printed or traversed further.
        file_obj: File-like object (supports ``.write``), optional. Output will be written to this object if provided.
        tab_character: str. Character to use to indicate indentation.
        level: int. Current level of the calculation. Only used internally, do not touch.

    Returns:
        Nothing. Prints to ``stdout`` or ``file_obj``

    """

    if cutoff > 0 and amount < cutoff:
        return
    message = "{}{:.3g}: {:.70}".format(tab_character * level, amount, str(activity))
    if file_obj is not None:
        file_obj.write(message + "\n")
    else:
        print(message)
    if level < max_level:
        for exc in activity.technosphere():
            print_recursive_supply_chain(
                activity=exc.input,
                amount=amount * exc['amount'],
                level=level + 1,
                max_level=max_level,
                cutoff=cutoff,
                file_obj=file_obj,
                tab_character=tab_character,
            )
