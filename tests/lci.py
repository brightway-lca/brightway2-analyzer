from .tagged import tagged_fixture
from bw2data import get_activity, methods
from bw2calc import LCA
from bw2analyzer.lci import get_labeled_inventory
import pytest
import pandas as pd
from pandas.testing import assert_frame_equal


def test_labeled_inventory_before_lci(tagged_fixture):
    act = get_activity(("foreground", "fu"))
    method = list(methods)[0]
    lca = LCA({act: 1}, method)
    with pytest.raises(AssertionError) as e_info:
        get_labeled_inventory(lca)


def test_labeled_inventory(tagged_fixture):
    act = get_activity(("foreground", "fu"))
    method = list(methods)[0]
    lca = LCA({act: 1}, method)
    lca.lci()
    df = get_labeled_inventory(lca)

    rows = [
        {
            "name": "bad",
            "type": "emission",
            "database": "biosphere",
            "code": "bad",
            "id": 1,
        },
        {
            "name": "worse",
            "type": "emission",
            "database": "biosphere",
            "code": "worse",
            "id": 2,
        },
    ]
    columns = [
        {"database": "background", "code": "first", "id": 3},
        {"database": "background", "code": "second", "id": 4},
        {
            "name": "functional unit",
            "tag field": "functional unit",
            "secondary tag": "X",
            "database": "foreground",
            "code": "fu",
            "id": 5,
        },
        {
            "tag field": "A",
            "secondary tag": "X",
            "database": "foreground",
            "code": "i",
            "id": 6,
        },
        {
            "tag field": "C",
            "secondary tag": "X",
            "database": "foreground",
            "code": "ii",
            "id": 7,
        },
        {"database": "foreground", "code": "iii", "id": 8},
        {
            "tag field": "C",
            "secondary tag": "Y",
            "database": "foreground",
            "code": "iv",
            "id": 9,
        },
    ]
    data = [
        [30.0, 0.0, 0.0, 5.0, 16.0, 27.0, 0.0],
        [0.0, 48.0, 0.0, 6.0, 14.0, 0.0, 44.0],
    ]
    expected = pd.DataFrame(
        data=data,
        index=pd.MultiIndex.from_frame(pd.DataFrame(rows)),
        columns=pd.MultiIndex.from_frame(pd.DataFrame(columns)),
    )
    assert_frame_equal(df, expected)
