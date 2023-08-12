import itertools
import string
import sys
from warnings import warn

from bw2data import Database, databases, get_activity, methods
from tqdm import tqdm
import bw2calc as bc
import numpy as np
import pandas as pd


def contribution_for_all_datasets_one_method(database, method, progress=True):
    """Calculate contribution analysis (for technosphere processes) for all inventory datasets in one database for one LCIA method.

    Args:
        *database* (str): Name of database
        *method* (tuple): Method tuple

    Returns:
        NumPy array of relative contributions. Each column sums to one.
        Lookup dictionary, dataset keys to row/column indices

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

    # Actual calculations
    for ds in tqdm(db):
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

    return results


def print_recursive_calculation(
    activity,
    lcia_method,
    amount=1,
    max_level=3,
    cutoff=1e-2,
    string_length=130,
    file_obj=None,
    tab_character="  ",
    use_matrix_values=False,
    _lca_obj=None,
    _total_score=None,
    __level=0,
    __first=True,
):
    """Traverse a supply chain graph, and calculate the LCA scores of each component. Prints the result with the format:

    {tab_character * level }{fraction of total score} ({absolute LCA score for this input} | {amount of input}) {input activity}

    Args:
        activity: ``Activity``. The starting point of the supply chain graph.
        lcia_method: tuple. LCIA method to use when traversing supply chain graph.
        amount: int. Amount of ``activity`` to assess.
        max_level: int. Maximum depth to traverse.
        cutoff: float. Fraction of total score to use as cutoff when deciding whether to traverse deeper.
        string_length: int. Maximum length of printed string.
        file_obj: File-like object (supports ``.write``), optional. Output will be written to this object if provided.
        tab_character: str. Character to use to indicate indentation.
        use_matrix_values: bool. Take exchange values from the matrix instead of the exchange instance ``amount``. Useful for Monte Carlo, but can be incorrect if there is more than one exchange from the same pair of nodes.

    Normally internal args:
        _lca_obj: ``LCA``. Can give an instance of the LCA class (e.g. when doing regionalized or Monte Carlo LCA)
        _total_score: float. Needed if specifying ``_lca_obj``.

    Internal args (used during recursion, do not touch);
        __level: int.
        __first: bool.

    Returns:
        Nothing. Prints to ``sys.stdout`` or ``file_obj``

    """
    activity = get_activity(activity)
    if file_obj is None:
        file_obj = sys.stdout

    if _lca_obj is None:
        _lca_obj = bc.LCA({activity: amount}, lcia_method)
        _lca_obj.lci()
        _lca_obj.lcia()
        _total_score = _lca_obj.score
    elif _total_score is None:
        raise ValueError
    else:
        _lca_obj.redo_lcia({activity.id: amount})
        if abs(_lca_obj.score) <= abs(_total_score * cutoff):
            return
    if __first:
        file_obj.write("Fraction of score | Absolute score | Amount | Activity\n")
    message = "{}{:04.3g} | {:5.4n} | {:5.4n} | {}".format(
        tab_character * __level,
        _lca_obj.score / _total_score,
        _lca_obj.score,
        float(amount),
        str(activity),
    )
    file_obj.write(message[:string_length] + "\n")
    if __level < max_level:
        prod_exchanges = list(activity.production())
        if not prod_exchanges:
            prod_amount = 1
        elif len(prod_exchanges) > 1:
            warn("Hit multiple production exchanges; aborting in this branch")
            return
        else:
            prod_amount = _lca_obj.technosphere_matrix[
                _lca_obj.dicts.product[prod_exchanges[0].input.id],
                _lca_obj.dicts.activity[prod_exchanges[0].output.id],
            ]

        for exc in activity.technosphere():
            if exc.input.id == exc.output.id:
                continue

            if use_matrix_values:
                sign = (
                    -1
                    if exc.get("type") in ("technosphere", "generic technosphere")
                    else 1
                )
                tm_amount = (
                    _lca_obj.technosphere_matrix[
                        _lca_obj.dicts.product[exc.input.id],
                        _lca_obj.dicts.activity[exc.output.id],
                    ]
                    * sign
                )
            else:
                tm_amount = exc["amount"]

            print_recursive_calculation(
                activity=exc.input,
                lcia_method=lcia_method,
                amount=amount * tm_amount / prod_amount,
                max_level=max_level,
                cutoff=cutoff,
                string_length=string_length,
                file_obj=file_obj,
                tab_character=tab_character,
                __first=False,
                _lca_obj=_lca_obj,
                _total_score=_total_score,
                __level=__level + 1,
            )


def print_recursive_supply_chain(
    activity,
    amount=1,
    max_level=2,
    cutoff=0,
    string_length=130,
    file_obj=None,
    tab_character="  ",
    __level=0,
):
    """Traverse a supply chain graph, and prints the inputs of each component.

    This function is only for exploration; use ``bw2calc.GraphTraversal`` for a better performing function.

    The results displayed here can also be incorrect if

    Args:
        activity: ``Activity``. The starting point of the supply chain graph.
        amount: int. Supply chain inputs will be scaled to this value.
        max_level: int. Max depth to search for.
        cutoff: float. Inputs with amounts less than ``amount * cutoff`` will not be printed or traversed further.
        string_length: int. Maximum length of each line.
        file_obj: File-like object (supports ``.write``), optional. Output will be written to this object if provided.
        tab_character: str. Character to use to indicate indentation.
        __level: int. Current level of the calculation. Only used internally, do not touch.

    Returns:
        Nothing. Prints to ``stdout`` or ``file_obj``

    """
    activity = get_activity(activity)
    if file_obj is None:
        file_obj = sys.stdout

    if cutoff > 0 and amount < cutoff:
        return
    message = "{}{:.3g}: {}".format(tab_character * __level, amount, str(activity))
    file_obj.write(message[:string_length] + "\n")
    if __level < max_level:
        prod_exchanges = list(activity.production())
        if not prod_exchanges:
            prod_amount = 1
        elif len(prod_exchanges) > 1:
            warn("Hit multiple production exchanges; aborting in this branch")
            return
        else:
            prod_amount = prod_exchanges[0]["amount"]
            for other in activity.technosphere():
                if other.input == prod_exchanges[0].input:
                    prod_amount -= other["amount"]

        for exc in activity.technosphere():
            if exc.input.id == exc.output.id:
                continue
            print_recursive_supply_chain(
                activity=exc.input,
                amount=amount * exc["amount"] / prod_amount,
                max_level=max_level,
                cutoff=cutoff,
                string_length=string_length,
                file_obj=file_obj,
                tab_character=tab_character,
                __level=__level + 1,
            )


def infinite_alphabet():
    """Return generator with values a-z, then aa-az, ba-bz, then aaa-aaz, aba-abz, etc."""
    for value in itertools.chain.from_iterable(
        itertools.product(string.ascii_lowercase, repeat=i) for i in itertools.count(1)
    ):
        yield "".join(value)


def recursive_calculation_to_object(
    activity,
    lcia_method,
    amount=1,
    max_level=3,
    cutoff=1e-2,
    as_dataframe=False,
    root_label="root",
    use_matrix_values=False,
    _lca_obj=None,
    _total_score=None,
    __result_list=None,
    __level=0,
    __label="",
    __parent=None,
):
    """Traverse a supply chain graph, and calculate the LCA scores of each component. Adds a dictionary to ``result_list`` of the form:

        {
            'label': Label of this branch. Starts with nothing, then A, AA, AB, AAA, AAB, etc.
            'score': Absolute score of this activity
            'fraction': Fraction of total score of this activity
            'amount': Input amount of the reference product of this activity
            'name': Name of this activity
            'key': Activity key
            'root_label': Starting label of root element for recursion.
        }

    Args:
        activity: ``Activity``. The starting point of the supply chain graph.
        lcia_method: tuple. LCIA method to use when traversing supply chain graph.
        amount: int. Amount of ``activity`` to assess.
        max_level: int. Maximum depth to traverse.
        cutoff: float. Fraction of total score to use as cutoff when deciding whether to traverse deeper.
        as_dataframe: Return results as a list (default) or a pandas ``DataFrame``
        use_matrix_values: bool. Take exchange values from the matrix instead of the exchange instance ``amount``. Useful for Monte Carlo, but can be incorrect if there is more than one exchange from the same pair of nodes.

    Internal args (used during recursion, do not touch):
        __result_list: list.
        __level: int.
        __label: str.
        __parent: str.

    Returns:
        List of dicts

    """
    activity = get_activity(activity)
    if __result_list is None:
        __result_list = []
        __label = root_label

    if _lca_obj is None:
        _lca_obj = bc.LCA({activity: amount}, lcia_method)
        _lca_obj.lci()
        _lca_obj.lcia()
        _total_score = _lca_obj.score
    elif _total_score is None:
        raise ValueError
    else:
        _lca_obj.redo_lcia({activity.id: amount})
        if abs(_lca_obj.score) <= abs(_total_score * cutoff):
            return
    __result_list.append(
        {
            "label": __label,
            "parent": __parent,
            "score": _lca_obj.score,
            "fraction": _lca_obj.score / _total_score,
            "amount": float(amount),
            "name": activity.get("name", "(Unknown name)"),
            "key": activity.key,
        }
    )
    if __level < max_level:
        prod_exchanges = list(activity.production())
        if not prod_exchanges:
            prod_amount = 1
        elif len(prod_exchanges) > 1:
            warn(
                "Hit multiple production exchanges for {}; aborting in this branch".format(
                    activity
                )
            )
            return
        else:
            prod_amount = _lca_obj.technosphere_matrix[
                _lca_obj.dicts.product[prod_exchanges[0].input.id],
                _lca_obj.dicts.activity[prod_exchanges[0].output.id],
            ]

        for child_label, exc in zip(infinite_alphabet(), activity.technosphere()):
            if exc.input.id == exc.output.id:
                continue

            if use_matrix_values:
                sign = (
                    -1
                    if exc.get("type") in ("technosphere", "generic technosphere")
                    else 1
                )
                tm_amount = (
                    _lca_obj.technosphere_matrix[
                        _lca_obj.dicts.product[exc.input.id],
                        _lca_obj.dicts.activity[exc.output.id],
                    ]
                    * sign
                )
            else:
                tm_amount = exc["amount"]

            recursive_calculation_to_object(
                activity=exc.input,
                lcia_method=lcia_method,
                amount=amount * tm_amount / prod_amount,
                max_level=max_level,
                cutoff=cutoff,
                as_dataframe=as_dataframe,
                __result_list=__result_list,
                __parent=__label,
                __label=__label + "_" + child_label if __label else child_label,
                _lca_obj=_lca_obj,
                _total_score=_total_score,
                __level=__level + 1,
            )

    if as_dataframe and __label == root_label:
        return pd.DataFrame(__result_list)
    else:
        return __result_list
