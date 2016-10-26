# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from ..tagged import traverse_tagged_databases
from bw2data import Database, Method, get_activity
from bw2data.tests import bw2test
import pytest


@pytest.fixture
@bw2test
def tagged_fixture():
    Database("biosphere").write({
        ("biosphere", "bad"): {
            'name': 'bad',
            'type': 'emission'
        },
        ("biosphere", "worse"): {
            'name': 'worse',
            'type': 'emission'
        },
    })
    method = Method(("test method",))
    method.register()
    method.write([
        (("biosphere", "bad"), 2),
        (("biosphere", "worse"), 3),
    ])
    Database("background").write({
        ("background", "first"): {
            'exchanges': [{
                'input': ("biosphere", "bad"),
                'amount': 1,
                'type': 'biosphere',
            }],
        },
        ("background", "second"): {
            'exchanges': [{
                'input': ("biosphere", "worse"),
                'amount': 1,
                'type': 'biosphere',
            }],
        },
    })
    Database("foreground").write({
        ("foreground", "fu"): {
            'name': 'functional unit',
            'tag field': 'functional unit',
            'exchanges': [{
                'input': ("foreground", "i"),
                'amount': 1,
                'type': 'technosphere',
            }, {
                'input': ("foreground", "iv"),
                'amount': 4,
                'type': 'technosphere',
            }],
        },
        ("foreground", "i"): {
            'tag field': "A",
            'exchanges': [{
                'input': ("foreground", "ii"),
                'amount': 2,
                'type': 'technosphere',
            }, {
                'input': ("foreground", "iii"),
                'amount': 3,
                'type': 'technosphere',
            }, {
                'input': ("biosphere", "bad"),
                'amount': 5,
                'tag field': 'C',
                'type': 'biosphere',
            }, {
                'input': ("biosphere", "worse"),
                'amount': 6,
                'type': 'biosphere',
            }],
        },
        ("foreground", "ii"): {
            'tag field': "C",
            'exchanges': [{
                'input': ("biosphere", "bad"),
                'amount': 8,
                'type': 'biosphere',
            }, {
                'input': ("biosphere", "worse"),
                'amount': 7,
                'tag field': 'D',
                'type': 'biosphere',
            }],
        },
        ("foreground", "iii"): {
            # Default tag: "B"
            'exchanges': [{
                'input': ("background", "first"),
                'amount': 10,
                'type': 'technosphere',
            }, {
                'input': ("biosphere", "bad"),
                'tag field': 'A',
                'amount': 9,
                'type': 'biosphere',
            }],
        },
        ("foreground", "iv"): {
            "tag field": "C",
            'exchanges': [{
                'input': ("background", "second"),
                'amount': 12,
                'type': 'technosphere',
            }, {
                'input': ("biosphere", "worse"),
                'tag field': 'B',
                'amount': 11,
                'type': 'biosphere',
            }],
        },
    })


def test_fixture_no_errors(tagged_fixture):
    pass

def test_traverse_tagged_databases_scores(tagged_fixture):
    scores, _ = traverse_tagged_databases(
        {("foreground", "fu"): 1}, ("test method",),
        label="tag field", default_tag="B"
    )
    assert scores == {
        "functional unit": 0,
        "A": 72,
        "B": 192,
        "C": 186,
        "D": 42,
    }

def test_traverse_tagged_databases_graph(tagged_fixture):
    _, graph = traverse_tagged_databases(
        {("foreground", "fu"): 1}, ("test method",),
        label="tag field", default_tag="B"
    )
    expected = [{
        'amount': 1,
        'biosphere': [],
        'activity': get_activity(("foreground", "fu")),
        'technosphere': [{
            'amount': 1,
            'biosphere': [
                {'amount': 5, 'impact': 10, 'tag': 'C'},
                {'amount': 6, 'impact': 18, 'tag': 'A'}
            ],
            'activity': get_activity(("foreground", "i")),
            'technosphere': [{
                'amount': 2,
                'biosphere': [
                    {'amount': 16, 'impact': 32, 'tag': 'C'},
                    {'amount': 14, 'impact': 42, 'tag': 'D'}
                ],
                'activity': get_activity(("foreground", "ii")),
                'technosphere': [],
                'impact': 0,
                'tag': 'C'
            }, {
                'amount': 3,
                'biosphere': [{'amount': 27, 'impact': 54, 'tag': 'A'}],
                'activity': get_activity(("foreground", "iii")),
                'technosphere': [],
                'impact': 60.00000000000001,  # Yeah floating point numbers...
                'tag': 'B'
            }],
            'impact': 0,
            'tag': 'A'
        }, {
            'amount': 4,
            'biosphere': [{'amount': 44, 'impact': 132, 'tag': 'B'}],
            'activity': get_activity(("foreground", "iv")),
            'technosphere': [],
            'impact': 144.0,
            'tag': 'C'
        }],
        'impact': 0,
        'tag': 'functional unit'
    }]
    assert graph == expected
