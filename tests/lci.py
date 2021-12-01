from .tagged import tagged_fixture
from bw2data import get_activity, methods
from bw2calc import LCA
from bw2analyzer.lci import get_labeled_inventory
import pytest
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal


def test_labeled_inventory_before_lci(tagged_fixture):
    act = get_activity(("foreground", "fu"))
    method = list(methods)[0]
    lca = LCA({act: 1}, method)
    with pytest.raises(AssertionError) as e_info:
        get_labeled_inventory(lca)


def test_labeled_inventory_wide_format(tagged_fixture):
    act = get_activity(("foreground", "fu"))
    method = list(methods)[0]
    lca = LCA({act: 1}, method)
    lca.lci()
    df = get_labeled_inventory(lca, wide_format=True, usecols="all")

    assert isinstance(df, pd.DataFrame)

    rows = [
        {
            "id": 1,
            "name": "bad",
            "type": "emission",
            "database": "biosphere",
            "code": "bad",
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
        {"id": 3, "database": "background", "code": "first"},
        {"database": "background", "code": "second", "id": 4},
        {
            "id": 5,
            "name": "functional unit",
            "tag field": "functional unit",
            "secondary tag": "X",
            "database": "foreground",
            "code": "fu",
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
    expected = (
        pd.DataFrame(
            data=data,
            index=pd.MultiIndex.from_frame(pd.DataFrame(rows)),
            columns=pd.MultiIndex.from_frame(pd.DataFrame(columns)),
        )
        .reorder_levels(df.index.names, axis="index")  # allow different level orders
        .reorder_levels(df.columns.names, axis="columns")
    )
    assert_frame_equal(df, expected)


def test_labeled_inventory_long_format(tagged_fixture):
    act = get_activity(("foreground", "fu"))
    method = list(methods)[0]
    lca = LCA({act: 1}, method)
    lca.lci()
    se = get_labeled_inventory(lca, wide_format=False, usecols="all")

    index = [
        {
            "source_id": 1,
            "source_code": "bad",
            "source_database": "biosphere",
            "source_name": "bad",
            "source_type": "emission",
            "target_id": 3,
            "target_code": "first",
            "target_database": "background",
        },
        {
            "source_id": 1,
            "source_code": "bad",
            "source_database": "biosphere",
            "source_name": "bad",
            "source_type": "emission",
            "target_id": 4,
            "target_code": "second",
            "target_database": "background",
        },
        {
            "source_id": 1,
            "source_code": "bad",
            "source_database": "biosphere",
            "source_name": "bad",
            "source_type": "emission",
            "target_id": 6,
            "target_code": "i",
            "target_database": "foreground",
            "target_secondary tag": "X",
            "target_tag field": "A",
        },
        {
            "source_id": 1,
            "source_code": "bad",
            "source_database": "biosphere",
            "source_name": "bad",
            "source_type": "emission",
            "target_id": 6,
            "target_code": "i",
            "target_database": "foreground",
            "target_secondary tag": "X",
            "target_tag field": "A",
        },
        {
            "source_id": 2,
            "source_code": "worse",
            "source_database": "biosphere",
            "source_name": "worse",
            "source_type": "emission",
            "target_id": 7,
            "target_code": "ii",
            "target_database": "foreground",
            "target_secondary tag": "X",
            "target_tag field": "C",
        },
        {
            "source_id": 2,
            "source_code": "worse",
            "source_database": "biosphere",
            "source_name": "worse",
            "source_type": "emission",
            "target_id": 7,
            "target_code": "ii",
            "target_database": "foreground",
            "target_secondary tag": "X",
            "target_tag field": "C",
        },
        {
            "source_id": 2,
            "source_code": "worse",
            "source_database": "biosphere",
            "source_name": "worse",
            "source_type": "emission",
            "target_id": 8,
            "target_code": "iii",
            "target_database": "foreground",
        },
        {
            "source_id": 2,
            "source_code": "worse",
            "source_database": "biosphere",
            "source_name": "worse",
            "source_type": "emission",
            "target_id": 9,
            "target_code": "iv",
            "target_database": "foreground",
            "target_secondary tag": "Y",
            "target_tag field": "C",
        },
    ]
    data = [27., 16.,  5., 30., 44., 14.,  6., 48.]
    expected = (
        pd.Series(
            data=data,
            index=pd.MultiIndex.from_frame(pd.DataFrame(index)),
            name='value',
        )
    )
    assert_series_equal(se, expected)
