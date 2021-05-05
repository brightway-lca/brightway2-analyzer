# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from .fixtures import method_fixture
from bw2analyzer import (
    table_for_grouped_leaves_compared_activities,
    compare_activities_by_grouped_leaves,
    find_differences_in_inputs,
    compare_activities_by_lcia_score,
)
from bw2data.tests import bw2test
import bw2calc as bc
import bw2data as bd
import pandas as pd
import pytest


@pytest.fixture
@bw2test
def cabls(capsys):
    method = bd.Method(("method",))
    method.register()
    method.write(method_fixture)
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
    capsys.readouterr()


@bw2test
def test_compare_activities_by_lcia_score_similar(capsys):
    method = bd.Method(("method",))
    method.register()
    method.write(method_fixture)
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
    assert "location" in df.columns


def test_find_differences_in_inputs_errors(fdii):
    with pytest.raises(AssertionError):
        find_differences_in_inputs(("c", "3"))
    with pytest.raises(ValueError):
        find_differences_in_inputs(bd.get_activity(("c", "6")))
