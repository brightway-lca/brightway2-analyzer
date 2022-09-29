import pytest
from bw2data.tests import bw2test
from bw2data import Database, Method, get_activity
from bw2calc import LCA
from bw2analyzer import perturbation_analysis as pa


@pytest.fixture
@bw2test
def pa_fixture():
    Database("biosphere").write(
        {
            ("biosphere", "bio-exc1"): {
                "name": "bio-exc1",
                "type": "emission",
            },
            ("biosphere", "bio-exc2"): {
                "name": "bio-exc2",
                "type": "emission",
            },
            ("biosphere", "bio-exc3"): {
                "name": "bio-exc3",
                "type": "emission",
            },
            ("biosphere", "bio-exc4"): {
                "name": "bio-exc4",
                "type": "emission",
            },
            ("biosphere", "bio-exc5"): {
                "name": "bio-exc5",
                "type": "emission",
            },
        }
    )

    method = Method(("test method",))
    method.register()
    method.write(
        [
            (("biosphere", "bio-exc1"), 1),
            (("biosphere", "bio-exc2"), 2),
            (("biosphere", "bio-exc3"), 3),
            (("biosphere", "bio-exc4"), 4),
            (("biosphere", "bio-exc5"), 5),
        ]
    )

    Database("foreground").write(
        {
            ("foreground", "act 1"): {
                "exchanges": [
                    {
                        "input": ("foreground", "act 1"),
                        "amount": 1,
                        "type": "production",
                    },
                    {
                        "input": ("biosphere", "bio-exc1"),
                        "amount": 1,
                        "type": "biosphere",
                    },
                    {
                        "input": ("biosphere", "bio-exc2"),
                        "amount": 1,
                        "type": "biosphere",
                    },
                    {
                        "input": ("foreground", "act 2"),
                        "amount": 1,
                        "type": "technosphere",
                    },
                    {
                        "input": ("foreground", "act 3"),
                        "amount": 1,
                        "type": "technosphere",
                    },
                    {
                        "input": ("foreground", "act 3"),
                        "amount": 2,
                        "type": "technosphere",
                    },
                    {
                        "input": ("foreground", "act 4"),
                        "amount": 1,
                        "type": "technosphere",
                    },
                ],
            },
            ("foreground", "act 2"): {
                "exchanges": [
                    {
                        "input": ("foreground", "act 2"),
                        "amount": 1,
                        "type": "production",
                    },
                    {
                        "input": ("biosphere", "bio-exc3"),
                        "amount": 1,
                        "type": "biosphere",
                    },
                ]
            },
            ("foreground", "act 3"): {
                "exchanges": [
                    {
                        "input": ("foreground", "act 3"),
                        "amount": 1,
                        "type": "technosphere",
                    },
                    {
                        "input": ("biosphere", "bio-exc4"),
                        "amount": 1,
                        "type": "biosphere",
                    },
                ]
            },
            ("foreground", "act 4"): {
                "exchanges": [
                    {
                        "input": ("foreground", "act 4"),
                        "amount": 1,
                        "type": "production",
                    },
                    {
                        "input": ("biosphere", "bio-exc5"),
                        "amount": 1,
                        "type": "biosphere",
                    },
                    {
                        "input": ("foreground", "act 2"),
                        "amount": 1,
                        "type": "technosphere",
                    },
                ]
            },
        }
    )

def test_fixture_no_errors(pa_fixture):
    bio = Database("biosphere")
    db = Database("foreground")
    act2 = get_activity(("foreground", "act 2"))
    method = ("test method",)
    lca = LCA({act2:1}, method)
    lca.lci()
    lca.lcia()
    assert lca.score == 3

def test_select_parameters_by_activity_list(pa_fixture):
    act1= get_activity(('foreground', 'act 1'))
    act2 = get_activity(('foreground', 'act 2'))
    act_list=[act1,act2]
    exc_types=['technosphere', 'biosphere', 'all']

    for exc_type in exc_types:
        if exc_type == 'technosphere':
            exclist=pa.select_parameters_by_activity_list(act_list)
            assert exclist == [*act1.technosphere(), *act2.technosphere()]
        elif exc_type == 'biosphere':
            exclist=pa.select_parameters_by_activity_list(act_list)
            assert exclist == [*act1.biosphere(), *act2.biosphere()]
        elif exc_type == 'all':
            exclist=pa.select_parameters_by_activity_list(act_list)
            assert exclist == [*act1.exchanges(), *act2.exchanges()]
        else:
            exclist=pa.select_parameters_by_activity_list(act_list)
            assert exclist == [*act1.exchanges(), *act2.exchanges()]


#def test_select_parameters_by_supply_chain_level():
#    supply_chain_levels=[1,3,5]
#    for s in
#    exclist = pa.select_parameters_by_supply_chain_level(activity,max_level=1)
#    assert



if __name__ == "__main__":
    pa_fixture()
    test_fixture_no_errors(None)
#    test_parameter_selection()
