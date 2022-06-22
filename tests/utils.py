import io
import pandas as pd

import bw2calc as bc
import bw2data as bd
import pytest
from bw2data.tests import bw2test

from bw2analyzer.utils import (
    print_recursive_calculation,
    print_recursive_supply_chain,
    recursive_calculation_to_object,
)

from .fixtures import method_fixture, recursive_fixture


@bw2test
def test_print_recursive_calculation_nonunitary_production(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "exchanges": [
                    {"input": ("f", "1"), "amount": 2, "type": "production"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ],
                "location": "GLO",
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ],
            },
        }
    )
    bd.Method(("m",)).write([(("f", "b"), 1)])

    print_recursive_calculation(("f", "1"), ("m",))
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 |     1 |     1 | Activity with missing fields (call ``valid(why=True)`` to see more)
  0001 |     1 |     1 | Activity with missing fields (call ``valid(why=True)`` to see more)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_calculation_nonunitary_production_losses(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "1"), "amount": 3, "type": "production"},
                    {"input": ("f", "1"), "amount": 1, "type": "technosphere"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ],
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ],
            },
        }
    )
    bd.Method(("m",)).write([(("f", "b"), 1)])

    print_recursive_calculation(("f", "1"), ("m",))
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 |     1 |     1 | Activity with missing fields (call ``valid(why=True)`` to see more)
  0001 |     1 |     1 | Activity with missing fields (call ``valid(why=True)`` to see more)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_calculation_nonunitary_production_multiple_production(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "1"), "amount": 1, "type": "production"},
                    {"input": ("f", "1"), "amount": 1, "type": "production"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ],
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ],
            },
        }
    )
    bd.Method(("m",)).write([(("f", "b"), 1)])

    with pytest.warns(UserWarning, match="Hit multiple production exchanges"):
        print_recursive_calculation(("f", "1"), ("m",))

    expected = """Fraction of score | Absolute score | Amount | Activity
0001 |     1 |     1 | Activity with missing fields (call ``valid(why=True)`` to see more)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_calculation(capsys):
    bd.Database("c").write({("c", "flow"): {"type": "emission"}})
    db = bd.Database("a")

    db.write(recursive_fixture)
    method = bd.Method(("method",))
    method.register()
    method.write(method_fixture)

    act = bd.get_activity(("a", "1"))
    lca = bc.LCA({act: 1}, ("method",))
    lca.lci()
    lca.lcia()

    print_recursive_calculation(act, ("method",))
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 | 4.836 |     1 | 'process 1' (b, RU, None)
  0.586 | 2.836 |   0.8 | 'process 2' (b, UA, None)
    0.504 | 2.436 |  0.48 | 'process 3' (b, BY, None)
      0.499 | 2.412 | 0.048 | 'process 5' (b, RO, None)
"""
    assert capsys.readouterr().out == expected

    # max_level
    print_recursive_calculation(act, ("method",), max_level=1)
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 | 4.836 |     1 | 'process 1' (b, RU, None)
  0.586 | 2.836 |   0.8 | 'process 2' (b, UA, None)
"""
    assert capsys.readouterr().out == expected

    # amount
    print_recursive_calculation(act, ("method",), amount=2, max_level=1)
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 | 9.671 |     2 | 'process 1' (b, RU, None)
  0.586 | 5.671 |   1.6 | 'process 2' (b, UA, None)
"""
    assert capsys.readouterr().out == expected

    # cutoff
    print_recursive_calculation(act, ("method",), cutoff=0.00025)
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 | 4.836 |     1 | 'process 1' (b, RU, None)
  0.586 | 2.836 |   0.8 | 'process 2' (b, UA, None)
    0.504 | 2.436 |  0.48 | 'process 3' (b, BY, None)
      0.00496 | 0.024 |   4.8 | 'process 4' (b, MD, None)
      0.499 | 2.412 | 0.048 | 'process 5' (b, RO, None)
"""
    assert capsys.readouterr().out == expected
    # io test
    io_ = io.StringIO()
    print_recursive_calculation(act, ("method",), max_level=1, file_obj=io_)
    io_.seek(0)
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 | 4.836 |     1 | 'process 1' (b, RU, None)
  0.586 | 2.836 |   0.8 | 'process 2' (b, UA, None)
"""
    assert io_.read() == expected

    # tab_character
    print_recursive_calculation(act, ("method",), max_level=1, tab_character="🐎")
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 | 4.836 |     1 | 'process 1' (b, RU, None)
🐎0.586 | 2.836 |   0.8 | 'process 2' (b, UA, None)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_supply_chain(capsys):
    db = bd.Database("a")
    db.write(recursive_fixture)
    act = bd.get_activity(("a", "1"))

    print_recursive_supply_chain(activity=act)
    expected = """1: 'process 1' (b, RU, None)
  0.8: 'process 2' (b, UA, None)
    0.48: 'process 3' (b, BY, None)
"""
    assert capsys.readouterr().out == expected

    print_recursive_supply_chain(activity=act, amount=2)
    expected = """2: 'process 1' (b, RU, None)
  1.6: 'process 2' (b, UA, None)
    0.96: 'process 3' (b, BY, None)
"""
    assert capsys.readouterr().out == expected

    print_recursive_supply_chain(activity=act, tab_character="🐎")
    expected = """1: 'process 1' (b, RU, None)
🐎0.8: 'process 2' (b, UA, None)
🐎🐎0.48: 'process 3' (b, BY, None)
"""
    assert capsys.readouterr().out == expected

    io_ = io.StringIO()
    print_recursive_supply_chain(activity=act, file_obj=io_)
    io_.seek(0)
    expected = """1: 'process 1' (b, RU, None)
  0.8: 'process 2' (b, UA, None)
    0.48: 'process 3' (b, BY, None)
"""
    assert io_.read() == expected

    print_recursive_supply_chain(activity=act, cutoff=0.05, max_level=5)
    expected = """1: 'process 1' (b, RU, None)
  0.8: 'process 2' (b, UA, None)
    0.48: 'process 3' (b, BY, None)
      4.8: 'process 4' (b, MD, None)
"""
    assert capsys.readouterr().out == expected

    print_recursive_supply_chain(activity=act, cutoff=0, max_level=5)
    expected = """1: 'process 1' (b, RU, None)
  0.8: 'process 2' (b, UA, None)
    0.48: 'process 3' (b, BY, None)
      4.8: 'process 4' (b, MD, None)
      0.048: 'process 5' (b, RO, None)
        0.0024: 'process 1' (b, RU, None)
          0.00192: 'process 2' (b, UA, None)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_supply_chain_nonunitary_production(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "1"), "amount": 2, "type": "production"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ],
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ],
            },
        }
    )

    print_recursive_supply_chain(("f", "1"))
    expected = """1: Activity with missing fields (call ``valid(why=True)`` to see more)
  1: Activity with missing fields (call ``valid(why=True)`` to see more)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_supply_chain_nonunitary_production_losses(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "1"), "amount": 3, "type": "production"},
                    {"input": ("f", "1"), "amount": 1, "type": "technosphere"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ],
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ],
            },
        }
    )

    print_recursive_supply_chain(("f", "1"))
    expected = """1: Activity with missing fields (call ``valid(why=True)`` to see more)
  1: Activity with missing fields (call ``valid(why=True)`` to see more)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_supply_chain_nonunitary_production_multiple_production(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "1"), "amount": 1, "type": "production"},
                    {"input": ("f", "1"), "amount": 1, "type": "production"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ],
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ],
            },
        }
    )

    with pytest.warns(UserWarning, match="Hit multiple production exchanges"):
        print_recursive_supply_chain(("f", "1"))

    expected = """1: Activity with missing fields (call ``valid(why=True)`` to see more)
"""
    assert capsys.readouterr().out == expected


@pytest.fixture
@bw2test
def rcto_fixture():
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "exchanges": [
                    {"input": ("f", "2"), "amount": 1, "type": "technosphere"},
                ],
                "location": "GLO",
            },
            ("f", "2"): {
                "location": "GLO",
                "name": "foo",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                    {"input": ("f", "1"), "amount": 0.8, "type": "technosphere"},
                ],
            },
        }
    )
    bd.Method(("m",)).write([(("f", "b"), 1)])


def test_recursive_calculation_to_object_return_dataframe(rcto_fixture):
    df = recursive_calculation_to_object(("f", "1"), ("m",), max_level=10, as_dataframe=True)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 11


def test_recursive_calculation_to_object_deep_recursion(rcto_fixture):
    expected = [
        {
            "label": "root",
            "parent": None,
            "score": 5.000000298023242,
            "fraction": 1.0,
            "amount": 1.0,
            "name": "(Unknown name)",
            "key": ("f", "1"),
        },
        {
            "label": "root_a",
            "parent": "root",
            "score": 5.000000298023242,
            "fraction": 1.0,
            "amount": 1.0,
            "name": "foo",
            "key": ("f", "2"),
        },
        {
            "label": "root_a_a",
            "parent": "root_a",
            "score": 4.000000238418593,
            "fraction": 0.8,
            "amount": 0.8,
            "name": "(Unknown name)",
            "key": ("f", "1"),
        },
        {
            "label": "root_a_a_a",
            "parent": "root_a_a",
            "score": 4.000000238418593,
            "fraction": 0.8,
            "amount": 0.8,
            "name": "foo",
            "key": ("f", "2"),
        },
        {
            "label": "root_a_a_a_a",
            "parent": "root_a_a_a",
            "score": 3.200000190734875,
            "fraction": 0.6400000000000001,
            "amount": 0.6400000000000001,
            "name": "(Unknown name)",
            "key": ("f", "1"),
        },
        {
            "label": "root_a_a_a_a_a",
            "parent": "root_a_a_a_a",
            "score": 3.200000190734875,
            "fraction": 0.6400000000000001,
            "amount": 0.6400000000000001,
            "name": "foo",
            "key": ("f", "2"),
        },
        {
            "label": "root_a_a_a_a_a_a",
            "parent": "root_a_a_a_a_a",
            "score": 2.5600001525879,
            "fraction": 0.5120000000000001,
            "amount": 0.5120000000000001,
            "name": "(Unknown name)",
            "key": ("f", "1"),
        },
        {
            "label": "root_a_a_a_a_a_a_a",
            "parent": "root_a_a_a_a_a_a",
            "score": 2.5600001525879,
            "fraction": 0.5120000000000001,
            "amount": 0.5120000000000001,
            "name": "foo",
            "key": ("f", "2"),
        },
        {
            "label": "root_a_a_a_a_a_a_a_a",
            "parent": "root_a_a_a_a_a_a_a",
            "score": 2.0480001220703206,
            "fraction": 0.40960000000000013,
            "amount": 0.40960000000000013,
            "name": "(Unknown name)",
            "key": ("f", "1"),
        },
        {
            "label": "root_a_a_a_a_a_a_a_a_a",
            "parent": "root_a_a_a_a_a_a_a_a",
            "score": 2.0480001220703206,
            "fraction": 0.40960000000000013,
            "amount": 0.40960000000000013,
            "name": "foo",
            "key": ("f", "2"),
        },
        {
            "label": "root_a_a_a_a_a_a_a_a_a_a",
            "parent": "root_a_a_a_a_a_a_a_a_a",
            "score": 1.6384000976562565,
            "fraction": 0.32768000000000014,
            "amount": 0.32768000000000014,
            "name": "(Unknown name)",
            "key": ("f", "1"),
        },
    ]
    assert recursive_calculation_to_object(("f", "1"), ("m",), max_level=10) == expected


@pytest.fixture
@bw2test
def rcto_fixture_2():
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "exchanges": [
                    {"input": ("f", "1"), "amount": 2, "type": "production"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ],
                "location": "GLO",
            },
            ("f", "2"): {
                "location": "GLO",
                "name": "foo",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ],
            },
        }
    )
    bd.Method(("m",)).write([(("f", "b"), 1)])


def test_recursive_calculation_to_object_custom_prefix(rcto_fixture_2):
    expected = [
        {
            "label": "foo",
            "parent": None,
            "score": 1.0,
            "fraction": 1.0,
            "amount": 1.0,
            "name": "(Unknown name)",
            "key": ("f", "1"),
        },
        {
            "label": "foo_a",
            "parent": "foo",
            "score": 1.0,
            "fraction": 1.0,
            "amount": 1.0,
            "name": "foo",
            "key": ("f", "2"),
        },
    ]
    assert (
        recursive_calculation_to_object(("f", "1"), ("m",), root_label="foo")
        == expected
    )


def test_recursive_calculation_to_object_nonunitary_production(rcto_fixture_2):
    expected = [
        {
            "label": "root",
            "parent": None,
            "score": 1.0,
            "fraction": 1.0,
            "amount": 1.0,
            "name": "(Unknown name)",
            "key": ("f", "1"),
        },
        {
            "label": "root_a",
            "parent": "root",
            "score": 1.0,
            "fraction": 1.0,
            "amount": 1.0,
            "name": "foo",
            "key": ("f", "2"),
        },
    ]
    assert recursive_calculation_to_object(("f", "1"), ("m",)) == expected


@bw2test
def test_recursive_calculation_to_object_nonunitary_production_losses(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "1"), "amount": 3, "type": "production"},
                    {"input": ("f", "1"), "amount": 1, "type": "technosphere"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ],
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ],
            },
        }
    )
    bd.Method(("m",)).write([(("f", "b"), 1)])

    expected = [
        {
            "label": "root",
            "parent": None,
            "score": 1.0,
            "fraction": 1.0,
            "amount": 1.0,
            "name": "(Unknown name)",
            "key": ("f", "1"),
        },
        {
            "label": "root_b",
            "parent": "root",
            "score": 1.0,
            "fraction": 1.0,
            "amount": 1.0,
            "name": "(Unknown name)",
            "key": ("f", "2"),
        },
    ]
    assert recursive_calculation_to_object(("f", "1"), ("m",)) == expected


@bw2test
def test_recursive_calculation_to_object_nonunitary_production_multiple_production(
    capsys,
):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "1"), "amount": 1, "type": "production"},
                    {"input": ("f", "1"), "amount": 1, "type": "production"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ],
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ],
            },
        }
    )
    bd.Method(("m",)).write([(("f", "b"), 1)])

    with pytest.warns(UserWarning, match="Hit multiple production exchanges"):
        result = recursive_calculation_to_object(("f", "1"), ("m",))
    assert result is None
