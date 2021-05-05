from os.path import commonprefix
from pandas import DataFrame
import bw2calc as bc
import bw2data as bd
import math
import numpy as np
import pandas as pd
import tabulate


def aggregated_dict(activity):
    """Return dictionary of inputs aggregated by input reference product."""
    results = {}
    for exc in activity.technosphere():
        results[exc.input["reference product"]] = (
            results.setdefault(exc.input["reference product"], 0) + exc["amount"]
        )

    for exc in activity.biosphere():
        results[exc.input["name"]] = (
            results.setdefault(exc.input["name"], 0) + exc["amount"]
        )

    return results


def compare_dictionaries(one, two, rel_tol=1e-4, abs_tol=1e-9):
    """Compare two dictionaries with form ``{str: float}``, and return a set of keys where differences where present.

    Tolerance values are inputs to `math.isclose <https://docs.python.org/3/library/math.html#math.isclose>`__."""
    return (
        set(one)
        .symmetric_difference(set(two))
        .union(
            {
                key
                for key in one
                if key in two
                and not math.isclose(
                    a=one[key], b=two[key], rel_tol=rel_tol, abs_tol=abs_tol
                )
            }
        )
    )


def find_differences_in_inputs(
    activity, rel_tol=1e-4, abs_tol=1e-9, locations=None, as_dataframe=False
):
    """Given an ``Activity``, try to see if other activities in the same database (with the same name and
    reference product) have the same input levels.

    Tolerance values are inputs to `math.isclose <https://docs.python.org/3/library/math.html#math.isclose>`__.

    If differences are present, a difference dictionary is constructed, with the form:

    .. code-block:: python

        {Activity instance: [(name of input flow (str), amount)]}

    Note that this doesn't reference a specific exchange, but rather sums **all exchanges with the same input reference product**.

    Assumes that all similar activities produce the same amount of reference product.

    ``(x, y)``, where ``x`` is the number of similar activities, and ``y`` is a dictionary of the differences. This dictionary is empty if no differences are found.

    Args:
        activity: ``Activity``. Activity to analyze.
        rel_tol: float. Relative tolerance to decide if two inputs are the same. See above.
        abs_tol: float. Absolute tolerance to decide if two inputs are the same. See above.
        locations: list, optional. Locations to restrict comparison to, if present.
        as_dataframe: bool. Return results as pandas DataFrame.

    Returns:
        dict or ``pandas.DataFrame``.


    """
    try:
        math.isclose(1, 1)
    except AttributeError:
        raise ImportError("This function requires Python >= 3.5")

    assert isinstance(activity, bd.backends.peewee.proxies.Activity)

    try:
        similar = [
            obj
            for obj in bd.Database(activity["database"])
            if obj != activity
            and obj.get("reference product") == activity.get("reference product")
            and obj.get("name") == activity["name"]
            and (not locations or obj.get("location") in locations)
        ]
    except KeyError:
        raise ValueError("Given activity has no `name`")

    result = {}

    origin_dict = aggregated_dict(activity)

    for target in similar:
        target_dict = aggregated_dict(target)
        difference = compare_dictionaries(origin_dict, target_dict, rel_tol, abs_tol)
        if difference:
            if activity not in result:
                result[activity] = {}
            result[activity].update(
                {key: value for key, value in origin_dict.items() if key in difference}
            )
            result[target] = {
                key: value for key, value in target_dict.items() if key in difference
            }

    if as_dataframe:
        return DataFrame(
            [{"location": obj.get("location"), **result[obj]} for obj in result]
        )
    else:
        return result


def compare_activities_by_lcia_score(activities, lcia_method, band=0.1):
    """Compare selected activities to see if they are substantially different.

    Substantially different means that all LCIA scores lie within a band of ``band * max_lcia_score``.

    Inputs:

        ``activities``: List of ``Activity`` objects.
        ``lcia_method``: Tuple identifying a ``Method``

    Returns:

        Nothing, but prints to stdout.

    """
    import bw2calc as bc

    lca = bc.LCA({a: 1 for a in activities}, lcia_method)
    lca.lci()
    lca.lcia()

    # First pass: Are all scores close?
    scores = []

    for a in activities:
        lca.redo_lcia({a: 1})
        scores.append(lca.score)

    if abs(max(scores) - min(scores)) < band * abs(max(scores)):
        print("All activities similar")
        return
    else:
        print("Differences observed. LCA scores:")
        for x, y in zip(scores, activities):
            print("\t{:5.3f} -> {}".format(x, y))


def find_leaves(
    activity,
    lcia_method,
    results=None,
    lca_obj=None,
    amount=1,
    total_score=None,
    level=0,
    max_level=3,
    cutoff=2.5e-2,
):
    """Traverse the supply chain of an activity to find leaves - places where the impact of that
    component falls below a threshold value.

    Returns a list of ``(fraction of total impact, specific impact, amount, Activity instance)`` tuples."""
    if results is None:
        results = []

    if lca_obj is None:
        lca_obj = bc.LCA({activity: amount}, lcia_method)
        lca_obj.lci()
        lca_obj.lcia()
        total_score = lca_obj.score
    elif total_score is None:
        raise ValueError
    else:
        lca_obj.redo_lcia({activity: amount})
        if abs(lca_obj.score) <= abs(total_score * cutoff) or level >= max_level:
            if abs(lca_obj.score) > abs(total_score * 1e-6):
                results.append(
                    (lca_obj.score / total_score, lca_obj.score, amount, activity)
                )
            return results

    # Add direct impacts from this activity, if relevant
    da = np.zeros_like(lca_obj.demand_array)
    da[lca_obj.product_dict[activity]] = amount
    direct = (lca_obj.characterization_matrix * lca_obj.biosphere_matrix * da).sum()
    if abs(direct) >= abs(total_score * cutoff):
        results.append((direct / total_score, direct, amount, activity))

    for exc in activity.technosphere():
        find_leaves(
            activity=exc.input,
            lcia_method=lcia_method,
            results=results,
            lca_obj=lca_obj,
            amount=amount * exc["amount"],
            total_score=total_score,
            level=level + 1,
            max_level=max_level,
            cutoff=cutoff,
        )

    return sorted(results, reverse=True)


def get_cpc(activity):
    try:
        return next(
            cl[1] for cl in activity.get("classifications", []) if cl[0] == "CPC"
        )
    except StopIteration:
        return


def get_value_for_cpc(lst, label, index):
    for elem in lst:
        if elem[3] == label:
            return elem[index]
    return 0


def group_leaves(leaves):
    """Group elements in ``leaves`` by their `CPC (Central Product Classification) <https://unstats.un.org/unsd/classifications/Econ/cpc>`__ code.

    Returns a list of ``(fraction of total impact, specific impact, amount, Activity instance)`` tuples."""
    results = {}

    for leaf in leaves:
        cpc = get_cpc(leaf[3])
        if cpc not in results:
            results[cpc] = np.zeros((3,))
        results[cpc] += np.array(leaf[:3])

    _ = lambda x: float(x)

    return sorted(
        [(_(a[0]), _(a[1]), _(a[2]), k) for k, a in results.items()], reverse=True
    )


def compare_activities_by_grouped_leaves(activities, lcia_method, mode="relative"):
    index = 0 if mode == "relative" else 1

    objs = [group_leaves(find_leaves(act, lcia_method)) for act in activities]
    sorted_keys = sorted(
        [
            (max([el[index] for obj in objs for el in obj if el[3] == key]), key)
            for key in {el[3] for obj in objs for el in obj}
        ],
        reverse=True,
    )
    name_common = commonprefix([act["name"] for act in activities])
    product_common = commonprefix([act["reference product"] for act in activities])

    lca = bc.LCA({act: 1 for act in activities}, lcia_method)
    lca.lci()
    lca.lcia()

    labels = ["activity", "product", "location", "unit", "total"] + [
        key for _, key in sorted_keys
    ]
    data = []
    for act, lst in zip(activities, objs):
        lca.redo_lcia({act: 1})
        data.append(
            [
                act["name"].replace(name_common, ""),
                act["reference product"].replace(product_common, ""),
                act["location"][:25],
                act["unit"],
                lca.score,
            ]
            + [get_value_for_cpc(lst, key, index) for _, key in sorted_keys]
        )

    return labels, data


def table_for_grouped_leaves_compared_activities(
    activities, lcia_method, mode="relative", str_cutoff=50
):
    labels, data = compare_activities_by_grouped_leaves(activities, lcia_method, mode)
    return tabulate.tabulate(
        sorted(data, key=lambda x: x[4]),
        [x[:str_cutoff] for x in labels],
        tablefmt="html",
        floatfmt=".3f",
    )
