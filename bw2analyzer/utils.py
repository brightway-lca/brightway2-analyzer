from time import time

import bw2calc as bc
import numpy as np
import pyprind
from bw2data import Database, Method, config, databases, mapping, methods


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

    assert database in databases, f"Can't find database {database}"
    assert method in methods, f"Can't find method {method}"
    db = Database(database)
    assert len(db), f"Database {database} appears to have no datasets"

    # Array to store results
    results = np.zeros((len(db), len(db)), dtype=np.float32)

    # Instantiate LCA object
    lca = bc.LCA({db.random(): 1}, method=method)
    lca.lci()
    lca.lcia()

    rows = lca.characterized_inventory.shape[0]
    cols = lca.characterized_inventory.shape[1]
    all_cutoff = cols * 4

    results = {
        "activities": np.zeros((cols, cols), dtype=np.float32),
        "flows": np.zeros((rows, cols), dtype=np.float32),
        "all": np.zeros((all_cutoff, cols), dtype=np.float32),
    }

    pbar = pyprind.ProgBar(len(db), title="Activities:")

    # Actual calculations
    for ds in db:
        lca.redo_lcia({ds.id: 1})
        if not lca.score:
            continue

        col = lca.dicts.activity[ds.id]
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

    return results


def print_recursive_calculation(
    activity,
    lcia_method,
    amount=1,
    max_level=3,
    cutoff=1e-2,
    file_obj=None,
    tab_character="  ",
    level=0,
    lca_obj=None,
    total_score=None,
    first=True,
):
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
        lca_obj.redo_lcia({activity.id: amount})
        if abs(lca_obj.score) <= abs(total_score * cutoff):
            return
    if first:
        message = "Fraction of score | Absolute score | Amount | Activity"
        if file_obj is not None:
            file_obj.write(message + "\n")
        else:
            print(message)
    message = "{}{:04.3g} | {:5.4n} | {:5.4n} | {:.70}".format(
        tab_character * level,
        lca_obj.score / total_score,
        lca_obj.score,
        float(amount),
        str(activity),
    )
    if file_obj is not None:
        file_obj.write(message + "\n")
    else:
        print(message)
    if level < max_level:
        for exc in activity.technosphere():
            print_recursive_calculation(
                activity=exc.input,
                lcia_method=lcia_method,
                amount=amount * exc["amount"],
                max_level=max_level,
                cutoff=cutoff,
                first=False,
                file_obj=file_obj,
                tab_character=tab_character,
                lca_obj=lca_obj,
                total_score=total_score,
                level=level + 1,
            )


def print_recursive_supply_chain(
    activity,
    amount=1,
    max_level=2,
    cutoff=0,
    file_obj=None,
    tab_character="  ",
    level=0,
):
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
                amount=amount * exc["amount"],
                level=level + 1,
                max_level=max_level,
                cutoff=cutoff,
                file_obj=file_obj,
                tab_character=tab_character,
            )
