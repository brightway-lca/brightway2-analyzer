# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from ..tagged import traverse_tagged_databases, multi_traverse_tagged_databases, get_cum_impact, get_multi_cum_impact
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
            'secondary tag': 'X',
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
            'secondary tag': 'X',
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
            'secondary tag': 'X',
            'exchanges': [{
                'input': ("biosphere", "bad"),
                'amount': 8,
                'type': 'biosphere',
            }, {
                'input': ("biosphere", "worse"),
                'amount': 7,
                'tag field': 'D',
                'secondary tag': 'Y',
                'type': 'biosphere',
            }],
        },
        ("foreground", "iii"): {
            # Default tag: "B"
            # Default secondary tag: "unknown"
            'exchanges': [{
                'input': ("background", "first"),
                'amount': 10,
                'type': 'technosphere',
            }, {
                'input': ("biosphere", "bad"),
                'tag field': 'A',
                'secondary tag': 'Y',
                'amount': 9,
                'type': 'biosphere',
            }],
        },
        ("foreground", "iv"): {
            "tag field": "C",
            'secondary tag': 'Y',
            'exchanges': [{
                'input': ("background", "second"),
                'amount': 12,
                'type': 'technosphere',
            }, {
                'input': ("biosphere", "worse"),
                'tag field': 'B',
                'secondary tag': 'Y',
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
                {'amount': 5, 'impact': 10, 'tag': 'C', 'secondary_tags': []},
                {'amount': 6, 'impact': 18, 'tag': 'A', 'secondary_tags': []}
            ],
            'activity': get_activity(("foreground", "i")),
            'technosphere': [{
                'amount': 2,
                'biosphere': [
                    {'amount': 16, 'impact': 32, 'tag': 'C', 'secondary_tags': []},
                    {'amount': 14, 'impact': 42, 'tag': 'D', 'secondary_tags': []}
                ],
                'activity': get_activity(("foreground", "ii")),
                'technosphere': [],
                'impact': 0,
                'tag': 'C',
                'secondary_tags': []
            }, {
                'amount': 3,
                'biosphere': [{'amount': 27, 'impact': 54, 'tag': 'A', 'secondary_tags': []}],
                'activity': get_activity(("foreground", "iii")),
                'technosphere': [],
                'impact': 60.0, #0000000000001,  # Yeah floating point numbers...
                'tag': 'B',
                'secondary_tags': []
            }],
            'impact': 0,
            'tag': 'A',
            'secondary_tags': []
        }, {
            'amount': 4,
            'biosphere': [{'amount': 44, 'impact': 132, 'tag': 'B', 'secondary_tags': []}],
            'activity': get_activity(("foreground", "iv")),
            'technosphere': [],
            'impact': 144.0,
            'tag': 'C',
            'secondary_tags': []
        }],
        'impact': 0,
        'tag': 'functional unit',
        'secondary_tags': []
    }]
    assert graph == expected

def test_multi_traverse_tagged_databases_scores(tagged_fixture):
    scores, _ = multi_traverse_tagged_databases(
        {("foreground", "fu"): 1}, [("test method",),("test method",)],
        label="tag field", default_tag="B"
    )
    assert scores == {
        "functional unit": [0, 0],
        "A": [72, 72],
        "B": [192, 192],
        "C": [186, 186],
        "D": [42, 42],
    }

def test_multi_traverse_tagged_databases_graph(tagged_fixture):
    _, graph = multi_traverse_tagged_databases(
        {("foreground", "fu"): 1}, [("test method",), ("test method",)],
        label="tag field", default_tag="B"
    )
    expected = [{
        'amount': 1,
        'biosphere': [],
        'activity': get_activity(("foreground", "fu")),
        'technosphere': [{
            'amount': 1,
            'biosphere': [
                {'amount': 5, 'impact': [10, 10], 'tag': 'C', 'secondary_tags': []},
                {'amount': 6, 'impact': [18, 18], 'tag': 'A', 'secondary_tags': []}
            ],
            'activity': get_activity(("foreground", "i")),
            'technosphere': [{
                'amount': 2,
                'biosphere': [
                    {'amount': 16, 'impact': [32, 32], 'tag': 'C', 'secondary_tags': []},
                    {'amount': 14, 'impact': [42, 42], 'tag': 'D', 'secondary_tags': []}
                ],
                'activity': get_activity(("foreground", "ii")),
                'technosphere': [],
                'impact': [0, 0],
                'tag': 'C',
                'secondary_tags': []
            }, {
                'amount': 3,
                'biosphere': [{'amount': 27, 'impact': [54, 54], 'tag': 'A', 'secondary_tags': []}],
                'activity': get_activity(("foreground", "iii")),
                'technosphere': [],
                'impact': [60, 60],
                'tag': 'B',
                'secondary_tags': []
            }],
            'impact': [0, 0],
            'tag': 'A',
            'secondary_tags': []
        }, {
            'amount': 4,
            'biosphere': [{'amount': 44, 'impact': [132, 132], 'tag': 'B', 'secondary_tags': []}],
            'activity': get_activity(("foreground", "iv")),
            'technosphere': [],
            'impact': [144, 144],
            'tag': 'C',
            'secondary_tags': []
        }],
        'impact': [0, 0],
        'tag': 'functional unit',
        'secondary_tags': []
    }]
    assert graph == expected


def test_traverse_tagged_databases_graph_secondary_tag(tagged_fixture):
    _, graph = traverse_tagged_databases(
        {("foreground", "fu"): 1}, ("test method",),
        label="tag field", default_tag="B", secondary_tags=[('secondary tag', 'unknown')]
    )
    expected = [{
        'amount': 1,
        'biosphere': [],
        'activity': get_activity(("foreground", "fu")),
        'technosphere': [{
            'amount': 1,
            'biosphere': [
                {'amount': 5, 'impact': 10, 'tag': 'C', 'secondary_tags': ['X']},
                {'amount': 6, 'impact': 18, 'tag': 'A', 'secondary_tags': ['X']}
            ],
            'activity': get_activity(("foreground", "i")),
            'technosphere': [{
                'amount': 2,
                'biosphere': [
                    {'amount': 16, 'impact': 32, 'tag': 'C', 'secondary_tags': ['X']},
                    {'amount': 14, 'impact': 42, 'tag': 'D', 'secondary_tags': ['Y']}
                ],
                'activity': get_activity(("foreground", "ii")),
                'technosphere': [],
                'impact': 0,
                'tag': 'C',
                'secondary_tags': ['X']
            }, {
                'amount': 3,
                'biosphere': [{'amount': 27, 'impact': 54, 'tag': 'A', 'secondary_tags': ['Y']}],
                'activity': get_activity(("foreground", "iii")),
                'technosphere': [],
                'impact': 60.0, #0000000000001,  # Yeah floating point numbers...
                'tag': 'B',
                'secondary_tags': ['unknown']
            }],
            'impact': 0,
            'tag': 'A',
            'secondary_tags': ['X']
        }, {
            'amount': 4,
            'biosphere': [{'amount': 44, 'impact': 132, 'tag': 'B', 'secondary_tags': ['Y']}],
            'activity': get_activity(("foreground", "iv")),
            'technosphere': [],
            'impact': 144.0,
            'tag': 'C',
            'secondary_tags': ['Y']
        }],
        'impact': 0,
        'tag': 'functional unit',
        'secondary_tags': ['X']
    }]
    assert graph == expected

def test_multi_traverse_tagged_databases_graph_secondary_tag(tagged_fixture):
    _, graph = multi_traverse_tagged_databases(
        {("foreground", "fu"): 1}, [("test method",), ("test method",)],
        label="tag field", default_tag="B", secondary_tags=[('secondary tag', 'unknown')]
    )
    expected = [{
        'amount': 1,
        'biosphere': [],
        'activity': get_activity(("foreground", "fu")),
        'technosphere': [{
            'amount': 1,
            'biosphere': [
                {'amount': 5, 'impact': [10, 10], 'tag': 'C', 'secondary_tags': ['X']},
                {'amount': 6, 'impact': [18, 18], 'tag': 'A', 'secondary_tags': ['X']}
            ],
            'activity': get_activity(("foreground", "i")),
            'technosphere': [{
                'amount': 2,
                'biosphere': [
                    {'amount': 16, 'impact': [32, 32], 'tag': 'C', 'secondary_tags': ['X']},
                    {'amount': 14, 'impact': [42, 42], 'tag': 'D', 'secondary_tags': ['Y']}
                ],
                'activity': get_activity(("foreground", "ii")),
                'technosphere': [],
                'impact': [0, 0],
                'tag': 'C',
                'secondary_tags': ['X']
            }, {
                'amount': 3,
                'biosphere': [{'amount': 27, 'impact': [54, 54], 'tag': 'A', 'secondary_tags': ['Y']}],
                'activity': get_activity(("foreground", "iii")),
                'technosphere': [],
                'impact': [60, 60],
                'tag': 'B',
                'secondary_tags': ['unknown']
            }],
            'impact': [0, 0],
            'tag': 'A',
            'secondary_tags': ['X']
        }, {
            'amount': 4,
            'biosphere': [{'amount': 44, 'impact': [132, 132], 'tag': 'B', 'secondary_tags': ['Y']}],
            'activity': get_activity(("foreground", "iv")),
            'technosphere': [],
            'impact': [144, 144],
            'tag': 'C',
            'secondary_tags': ['Y']
        }],
        'impact': [0, 0],
        'tag': 'functional unit',
        'secondary_tags': ['X']
    }]
    assert graph == expected

def test_get_cum_impact(tagged_fixture):
    _, graph = traverse_tagged_databases(
        {("foreground", "fu"): 1}, ("test method",),
        label="tag field", default_tag="B"
    )

    cum_graph = get_cum_impact(graph)

    expected = [{
        'amount': 1,
        'biosphere': [],
        'activity': get_activity(("foreground", "fu")),
        'technosphere': [{
            'amount': 1,
            'biosphere': [
                {'amount': 5, 'impact': 10, 'tag': 'C', 'secondary_tags': []},
                {'amount': 6, 'impact': 18, 'tag': 'A', 'secondary_tags': []}
            ],
            'activity': get_activity(("foreground", "i")),
            'technosphere': [{
                'amount': 2,
                'biosphere': [
                    {'amount': 16, 'impact': 32, 'tag': 'C', 'secondary_tags': []},
                    {'amount': 14, 'impact': 42, 'tag': 'D', 'secondary_tags': []}
                ],
                'activity': get_activity(("foreground", "ii")),
                'technosphere': [],
                'impact': 0,
                'cum_impact': 74,
                'tag': 'C',
                'secondary_tags': []
            }, {
                'amount': 3,
                'biosphere': [{'amount': 27, 'impact': 54, 'tag': 'A', 'secondary_tags': []}],
                'activity': get_activity(("foreground", "iii")),
                'technosphere': [],
                'impact': 60.0, #0000000000001,  # Yeah floating point numbers...
                'cum_impact': 54,
                'tag': 'B',
                'secondary_tags': []
            }],
            'impact': 0,
            'cum_impact': 216.0,
            'tag': 'A',
            'secondary_tags': []
        }, {
            'amount': 4,
            'biosphere': [{'amount': 44, 'impact': 132, 'tag': 'B', 'secondary_tags': []}],
            'activity': get_activity(("foreground", "iv")),
            'technosphere': [],
            'impact': 144.0,
            'cum_impact': 132,
            'tag': 'C',
            'secondary_tags': []
        }],
        'impact': 0,
        'cum_impact': 492.0,
        'tag': 'functional unit',
        'secondary_tags': []
    }]
    assert cum_graph == expected

def test_get_multi_cum_impact(tagged_fixture):
    _, graph = multi_traverse_tagged_databases(
        {("foreground", "fu"): 1}, [("test method",),("test method",)],
        label="tag field", default_tag="B"
    )

    cum_graph = get_multi_cum_impact(graph)

    expected = [{
        'amount': 1,
        'biosphere': [],
        'activity': get_activity(("foreground", "fu")),
        'technosphere': [{
            'amount': 1,
            'biosphere': [
                {'amount': 5, 'impact': [10, 10], 'tag': 'C', 'secondary_tags': []},
                {'amount': 6, 'impact': [18, 18], 'tag': 'A', 'secondary_tags': []}
            ],
            'activity': get_activity(("foreground", "i")),
            'technosphere': [{
                'amount': 2,
                'biosphere': [
                    {'amount': 16, 'impact': [32, 32], 'tag': 'C', 'secondary_tags': []},
                    {'amount': 14, 'impact': [42, 42], 'tag': 'D', 'secondary_tags': []}
                ],
                'activity': get_activity(("foreground", "ii")),
                'technosphere': [],
                'impact': [0, 0],
                'cum_impact': [74, 74],
                'tag': 'C',
                'secondary_tags': []
            }, {
                'amount': 3,
                'biosphere': [{'amount': 27, 'impact': [54, 54], 'tag': 'A', 'secondary_tags': []}],
                'activity': get_activity(("foreground", "iii")),
                'technosphere': [],
                'impact': [60, 60],
                'cum_impact': [54, 54],
                'tag': 'B',
                'secondary_tags': []
            }],
            'impact': [0, 0],
            'cum_impact': [216.0, 216.0],
            'tag': 'A',
            'secondary_tags': []
        }, {
            'amount': 4,
            'biosphere': [{'amount': 44, 'impact': [132, 132], 'tag': 'B', 'secondary_tags': []}],
            'activity': get_activity(("foreground", "iv")),
            'technosphere': [],
            'impact': [144.0, 144.0],
            'cum_impact': [132, 132],
            'tag': 'C',
            'secondary_tags': []
        }],
        'impact': [0, 0],
        'cum_impact': [492.0, 492.0],
        'tag': 'functional unit',
        'secondary_tags': []
    }]
    assert cum_graph == expected