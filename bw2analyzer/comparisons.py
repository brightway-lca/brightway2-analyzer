import math
import operator
from os.path import commonprefix

import bw2calc as bc
import bw2data as bd
import numpy as np
import pandas as pd
import tabulate
from pandas import DataFrame


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
    assert isinstance(activity, bd.backends.proxies.Activity)

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
        raise ValueError("Given activity has no `name`; can't find similar names")

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
        df = DataFrame(
            [{"location": obj.get("location"), **result[obj]} for obj in result]
        )
        df.set_index("location", inplace=True)
        return df
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

    activities = [bd.get_activity(obj) for obj in activities]

    lca = bc.LCA({a: 1 for a in activities}, lcia_method)
    lca.lci()
    lca.lcia()

    # First pass: Are all scores close?
    scores = []

    for a in activities:
        lca.redo_lcia({a.id: 1})
        scores.append(lca.score)

    if abs(max(scores) - min(scores)) < band * abs(max(scores)):
        print("All activities similar")
        return
    else:
        print("Differences observed. LCA scores:")
        for x, y in zip(scores, activities):
            print("\t{:5.3f} -> {}".format(x, y.key))


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

    Returns a list of ``(impact of this activity, amount consumed, Activity instance)`` tuples."""
    first_level = results is None

    activity = bd.get_activity(activity)

    if first_level:
        level = 0
        results = []

        lca_obj = bc.LCA({activity: amount}, lcia_method)
        lca_obj.lci()
        lca_obj.lcia()
        total_score = lca_obj.score
    else:
        lca_obj.redo_lcia({activity.id: amount})

        # If this is a leaf, add the leaf and return
        if abs(lca_obj.score) <= abs(total_score * cutoff) or level >= max_level:

            # Only add leaves with scores that matter
            if abs(lca_obj.score) > abs(total_score * 1e-4):
                results.append((lca_obj.score, amount, activity))
            return results

        else:
            # Add direct emissions from this demand
            direct = (
                lca_obj.characterization_matrix
                * lca_obj.biosphere_matrix
                * lca_obj.demand_array
            ).sum()
            if abs(direct) >= abs(total_score * 1e-4):
                results.append((direct, amount, activity))

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


def get_value_for_cpc(lst, label):
    for elem in lst:
        if elem[2] == label:
            return elem[0]
    return 0


def group_leaves(leaves):
    """Group elements in ``leaves`` by their `CPC (Central Product Classification) <https://unstats.un.org/unsd/classifications/Econ/cpc>`__ code.

    Returns a list of ``(fraction of total impact, specific impact, amount, Activity instance)`` tuples."""
    results = {}

    for leaf in leaves:
        cpc = get_cpc(leaf[2])
        if cpc not in results:
            results[cpc] = np.zeros((2,))
        results[cpc] += np.array(leaf[:2])

    return sorted([v.tolist() + [k] for k, v in results.items()], reverse=True)


def compare_activities_by_grouped_leaves(
    activities,
    lcia_method,
    mode="relative",
    max_level=4,
    cutoff=7.5e-3,
    output_format="list",
    str_length=50,
):
    """Compare activities by the impact of their different inputs, aggregated by the product classification of those inputs.

    Args:
        activities: list of ``Activity`` instances.
        lcia_method: tuple. LCIA method to use when traversing supply chain graph.
        mode: str. If "relative" (default), results are returned as a fraction of total input. Otherwise, results are absolute impact per input exchange.
        max_level: int. Maximum level in supply chain to examine.
        cutoff: float. Fraction of total impact to cutoff supply chain graph traversal at.
        output_format: str. See below.
        str_length; int. If ``output_format`` is ``html``, this controls how many characters each column label can have.

    Raises:
        ValueError: ``activities`` is malformed.

    Returns:
        Depends on ``output_format``:

        * ``list``: Tuple of ``(column labels, data)``
        * ``html``: HTML string that will print nicely in Jupyter notebooks.
        * ``pandas``: a pandas ``DataFrame``.

    """
    for act in activities:
        if not isinstance(act, bd.backends.proxies.Activity):
            raise ValueError("`activities` must be an iterable of `Activity` instances")

    objs = [
        group_leaves(find_leaves(act, lcia_method, max_level=max_level, cutoff=cutoff))
        for act in activities
    ]
    sorted_keys = sorted(
        [
            (max([el[0] for obj in objs for el in obj if el[2] == key]), key)
            for key in {el[2] for obj in objs for el in obj}
        ],
        reverse=True,
    )
    name_common = commonprefix([act["name"] for act in activities])

    if " " not in name_common:
        name_common = ""
    else:
        last_space = len(name_common) - operator.indexOf(reversed(name_common), " ")
        name_common = name_common[:last_space]
        print("Omitting activity name common prefix: '{}'".format(name_common))

    product_common = commonprefix(
        [act.get("reference product", "") for act in activities]
    )

    lca = bc.LCA({act: 1 for act in activities}, lcia_method)
    lca.lci()
    lca.lcia()

    labels = [
        "activity",
        "product",
        "location",
        "unit",
        "total",
        "direct emissions",
    ] + [key for _, key in sorted_keys]
    data = []
    for act, lst in zip(activities, objs):
        lca.redo_lcia({act.id: 1})
        data.append(
            [
                act["name"].replace(name_common, ""),
                act.get("reference product", "").replace(product_common, ""),
                act.get("location", "")[:25],
                act.get("unit", ""),
                lca.score,
            ]
            + [
                (
                    lca.characterization_matrix
                    * lca.biosphere_matrix
                    * lca.demand_array
                ).sum()
            ]
            + [get_value_for_cpc(lst, key) for _, key in sorted_keys]
        )

    data.sort(key=lambda x: x[4], reverse=True)

    if mode == "relative":
        for row in data:
            for index, point in enumerate(row[5:]):
                row[index + 5] = point / row[4]

    if output_format == "list":
        return labels, data
    elif output_format == "pandas":
        return pd.DataFrame(data, columns=labels)
    elif output_format == "html":
        return tabulate.tabulate(
            data,
            [x[:str_length] for x in labels],
            tablefmt="html",
            floatfmt=".3f",
        )
