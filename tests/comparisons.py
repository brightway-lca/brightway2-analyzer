from .fixtures import method_fixture
from bw2analyzer import (
    compare_activities_by_grouped_leaves,
    find_differences_in_inputs,
    compare_activities_by_lcia_score,
)
from bw2data.tests import bw2test
import bw2data as bd
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
@bw2test
def cabls(capsys):
    bd.Database("a").write({("a", "flow"): {"type": "emission"}})

    data = {
        ("c", "flow"): {"name": "flow", "type": "biosphere"},
        ("c", "1"): {
            "name": "process 1",
            "exchanges": [{"input": ("c", "flow"), "type": "biosphere", "amount": 1}],
        },
        ("c", "2"): {
            "name": "process 2",
            "exchanges": [
                {"input": ("c", "flow"), "type": "biosphere", "amount": 1.25},
            ],
        },
    }
    db = bd.Database("c")
    db.write(data)

    method = bd.Method(("method",))
    method.register()
    method.write(method_fixture)
    capsys.readouterr()


@bw2test
def test_compare_activities_by_lcia_score_similar(capsys):
    bd.Database("a").write({("a", "flow"): {"type": "emission"}})

    data = {
        ("c", "flow"): {"name": "flow", "type": "biosphere"},
        ("c", "1"): {
            "name": "process 1",
            "exchanges": [{"input": ("c", "flow"), "type": "biosphere", "amount": 1}],
        },
        ("c", "2"): {
            "name": "process 2",
            "exchanges": [
                {"input": ("c", "flow"), "type": "biosphere", "amount": 1.1},
            ],
        },
    }
    db = bd.Database("c")
    db.write(data)

    method = bd.Method(("method",))
    method.register()
    method.write(method_fixture)

    capsys.readouterr()
    compare_activities_by_lcia_score([("c", "1"), ("c", "2")], ("method",))

    expected = "All activities similar\n"
    assert capsys.readouterr().out == expected


def test_compare_activities_by_lcia_score_different(cabls, capsys):
    compare_activities_by_lcia_score([("c", "1"), ("c", "2")], ("method",))

    expected = """Differences observed. LCA scores:
\t1.000 -> ('c', '1')
\t1.250 -> ('c', '2')\n"""
    assert capsys.readouterr().out == expected


def test_compare_activities_by_lcia_score_band(cabls, capsys):
    compare_activities_by_lcia_score([("c", "1"), ("c", "2")], ("method",), band=1.33)

    expected = "All activities similar\n"
    assert capsys.readouterr().out == expected


@pytest.fixture
@bw2test
def fdii():
    data = {
        ("c", "flow"): {"name": "flow", "type": "biosphere"},
        ("c", "1"): {
            "name": "yes",
            "reference product": "bar",
            "exchanges": [{"input": ("c", "flow"), "type": "biosphere", "amount": 0.1}],
        },
        ("c", "2"): {
            "name": "no",
            "reference product": "foo",
            "exchanges": [{"input": ("c", "flow"), "type": "biosphere", "amount": 10}],
        },
        ("c", "3"): {
            "name": "yes",
            "reference product": "foo",
            "location": "here",
            "exchanges": [
                {"input": ("c", "flow"), "type": "biosphere", "amount": 1},
                {"input": ("c", "1"), "type": "technosphere", "amount": 10},
            ],
        },
        ("c", "4"): {
            "name": "yes",
            "reference product": "foo",
            "location": "here",
            "exchanges": [
                {"input": ("c", "flow"), "type": "biosphere", "amount": 0.6},
                {"input": ("c", "flow"), "type": "biosphere", "amount": 0.5},
                {"input": ("c", "1"), "type": "technosphere", "amount": 10},
            ],
        },
        ("c", "5"): {
            "name": "yes",
            "reference product": "foo",
            "location": "there",
            "exchanges": [
                {"input": ("c", "flow"), "type": "biosphere", "amount": 0.95},
                {"input": ("c", "1"), "type": "technosphere", "amount": 10},
            ],
        },
        ("c", "6"): {
            "reference product": "bar",
            "exchanges": [{"input": ("c", "flow"), "type": "biosphere", "amount": 1}],
        },
    }
    db = bd.Database("c")
    db.write(data)


def test_find_differences_in_inputs(fdii):
    expected = {
        bd.get_activity(("c", "3")): {"flow": 1},
        bd.get_activity(("c", "4")): {"flow": 1.1},
        bd.get_activity(("c", "5")): {"flow": 0.95},
    }
    assert find_differences_in_inputs(bd.get_activity(("c", "3"))) == expected


def test_find_differences_in_inputs_tolerances(fdii):
    assert not find_differences_in_inputs(bd.get_activity(("c", "3")), rel_tol=0.2)

    expected = {
        bd.get_activity(("c", "3")): {"flow": 1},
        bd.get_activity(("c", "4")): {"flow": 1.1},
    }
    assert (
        find_differences_in_inputs(bd.get_activity(("c", "3")), abs_tol=0.075)
        == expected
    )


def test_find_differences_in_inputs_locations(fdii):
    expected = {
        bd.get_activity(("c", "3")): {"flow": 1},
        bd.get_activity(("c", "4")): {"flow": 1.1},
    }
    assert (
        find_differences_in_inputs(bd.get_activity(("c", "3")), locations=["here"])
        == expected
    )


def test_find_differences_in_inputs_dataframe(fdii):
    df = find_differences_in_inputs(bd.get_activity(("c", "3")), as_dataframe=True)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3


def test_find_differences_in_inputs_errors(fdii):
    with pytest.raises(AssertionError):
        find_differences_in_inputs(("c", "3"))
    with pytest.raises(ValueError):
        find_differences_in_inputs(bd.get_activity(("c", "6")))


@pytest.fixture
@bw2test
def cabgl():
    bd.Database("a").write({("a", "flow"): {"type": "emission"}})

    data = {
        ("c", "flow"): {"name": "flow", "type": "biosphere"},
        ("c", "1"): {
            "name": "1",
            "reference product": "bar",
            "exchanges": [{"input": ("c", "flow"), "type": "biosphere", "amount": 1}],
            "classifications": [
                ("foo", "bar"),
                ("CPC", "product A"),
            ],
        },
        ("c", "2"): {
            "name": "2",
            "reference product": "foo",
            "exchanges": [
                {"input": ("c", "flow"), "type": "biosphere", "amount": 2},
                {"input": ("c", "1"), "type": "technosphere", "amount": 2},
            ],
            "classifications": [
                ("CPC", "product B"),
            ],
        },
        ("c", "3"): {
            "name": "3",
            "reference product": "foo",
            "location": "here",
            "exchanges": [
                {"input": ("c", "1"), "type": "technosphere", "amount": 1},
            ],
            "classifications": [
                ("CPC", "product B"),
            ],
        },
        ("c", "4"): {
            "name": "4",
            "reference product": "foo",
            "location": "here",
            "exchanges": [
                {"input": ("c", "flow"), "type": "biosphere", "amount": 4},
                {"input": ("c", "3"), "type": "technosphere", "amount": 3},
            ],
            "classifications": [
                ("CPC", "product C"),
            ],
        },
        ("c", "5"): {
            "name": "5",
            "reference product": "foo",
            "location": "there",
            "exchanges": [
                {"input": ("c", "flow"), "type": "biosphere", "amount": 5},
                {"input": ("c", "3"), "type": "technosphere", "amount": 5},
                {"input": ("c", "2"), "type": "technosphere", "amount": 4},
            ],
            "classifications": [
                ("CPC", "product D"),
            ],
        },
        ("c", "6"): {
            "name": "6",
            "reference product": "bar",
            "exchanges": [
                {"input": ("c", "flow"), "type": "biosphere", "amount": 6},
                {"input": ("c", "5"), "type": "technosphere", "amount": 7},
                {"input": ("c", "4"), "type": "technosphere", "amount": 9},
            ],
            "classifications": [
                ("CPC", "product E"),
            ],
        },
        ("c", "7"): {
            "name": "7",
            "reference product": "bar",
            "exchanges": [
                {"input": ("c", "flow"), "type": "biosphere", "amount": 0},
                {"input": ("c", "5"), "type": "technosphere", "amount": 6},
                {"input": ("c", "4"), "type": "technosphere", "amount": 8},
            ],
            "classifications": [
                ("CPC", "product E"),
            ],
        },
    }
    db = bd.Database("c")
    db.write(data)

    method = bd.Method(("method",))
    method.register()
    method.write(method_fixture)


def test_compare_activities_by_grouped_leaves(cabgl):
    labels, result = compare_activities_by_grouped_leaves(
        [bd.get_activity(("c", "6")), bd.get_activity(("c", "7"))], ("method",)
    )
    assert labels == [
        "activity",
        "product",
        "location",
        "unit",
        "total",
        "direct emissions",
        "product A",
        "product B",
        "product C",
        "product D",
    ]
    assert result[0][0] == "6"
    assert result[1][0] == "7"
    assert np.allclose(
        result[0][4:],
        [251, 6 / 251, (27 + 35 + 56) / 251, 56 / 251, 36 / 251, 35 / 251],
    )
    assert np.allclose(
        result[1][4:], [212, 0, (30 + 48 + 24) / 212, 48 / 212, 32 / 212, 30 / 212]
    )


def test_compare_activities_by_grouped_leaves_html(cabgl):
    result = compare_activities_by_grouped_leaves(
        [bd.get_activity(("c", "6")), bd.get_activity(("c", "7"))],
        ("method",),
        output_format="html",
    )
    assert isinstance(result, str)


def test_compare_activities_by_grouped_leaves_pandas(cabgl):
    result = compare_activities_by_grouped_leaves(
        [bd.get_activity(("c", "6")), bd.get_activity(("c", "7"))],
        ("method",),
        output_format="pandas",
    )
    assert isinstance(result, pd.DataFrame)


def test_compare_activities_by_grouped_leaves_max_level(cabgl):
    labels, result = compare_activities_by_grouped_leaves(
        [bd.get_activity(("c", "6")), bd.get_activity(("c", "7"))],
        ("method",),
        max_level=1,
    )
    assert labels == [
        "activity",
        "product",
        "location",
        "unit",
        "total",
        "direct emissions",
        "product D",
        "product C",
    ]
    assert result[0][0] == "6"
    assert result[1][0] == "7"
    assert np.allclose(
        result[0][4:], [251, 6 / 251, (35 + 35 + 56 + 56) / 251, (36 + 27) / 251]
    )


def test_compare_activities_by_grouped_leaves_max_cutoff(cabgl):
    labels, result = compare_activities_by_grouped_leaves(
        [bd.get_activity(("c", "6")), bd.get_activity(("c", "7"))],
        ("method",),
        cutoff=0.2,
    )
    assert labels == [
        "activity",
        "product",
        "location",
        "unit",
        "total",
        "direct emissions",
        "product B",
        "product A",
        "product C",
        "product D",
    ]
    assert result[0][0] == "6"
    assert result[1][0] == "7"
    assert np.allclose(
        result[0][4:],
        [251, 6 / 251, (56 + 27 + 35) / 251, (56) / 251, 36 / 251, 35 / 251],
    )
