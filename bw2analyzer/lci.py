import pandas as pd
from bw2data import Database, get_activity
from bw2calc import LCA
from typing import List, Union, Optional


def _load_database_metadata(
    lca: LCA, cols: Optional[Union[List[str], str]] = None
) -> pd.DataFrame:
    # get functional unit database
    root_db = get_activity(list(lca.demand.keys())[0])["database"]
    # get dependent databases
    dependent = list(Database(root_db).find_graph_dependents())
    databases = pd.unique([root_db] + dependent)
    # for all databases: load metadata and store in one dataframe
    df = pd.DataFrame()
    for db in databases:
        df = df.append(pd.DataFrame(Database(db)), ignore_index=True)
    # drop unwanted columns
    if cols is None:
        cols = [
            "id",
            "name",
            "location",
            "reference product",
            "type",
            "unit",
            "database",
            "categories",
        ]
    elif cols == "all":
        cols = df.columns.tolist()
    existing_cols = [c for c in cols if c in df]
    df = df[existing_cols]
    df = df.set_index("id")
    return df


def get_labeled_inventory(
    lca: LCA,
    wide_format: bool = True,
    usecols: Optional[Union[List[str], str]] = None,
) -> Union[pd.DataFrame, pd.Series]:
    """
    Take an LCA's inventory matrix and labels its rows (biosphere) and columns (technosphere) with activity metadata.

    Args:
        * *lca* (bw2calc.LCA): LCA object whose life cycle inventory has been calculated previously.
        * *wide_format* (bool): Whether to return the labeled inventory table in wide format or narrow format (for an example see https://en.wikipedia.org/wiki/Wide_and_narrow_data).
        * *usecols* (None, 'all' or list of column names): Which metadata fields to include in the indices. None means default.

    Returns:
        If wide_format == True: pd.DataFrame with biosphere data as row index and technosphere data as column index.
        If wide_format == False: pd.Series with biosphere (source) and technosphere (target) data as the index.
    """

    assert hasattr(
        lca, "inventory"
    ), "Must calculate life cycle inventory first. Please call lci()."

    # get activity metadata
    meta = _load_database_metadata(lca, usecols)

    if wide_format:

        # map local matrix indices to global database ids
        rows_global = lca.dicts.biosphere.reversed.values()
        cols_global = lca.dicts.activity.reversed.values()

        # associate metadata, drop columns which are empty
        row_meta = (
            pd.DataFrame(index=rows_global, data=rows_global, columns=["id"])
            .join(meta, how="left")
            .dropna(how="all", axis=1)
        )
        col_meta = (
            pd.DataFrame(index=cols_global, data=cols_global, columns=["id"])
            .join(meta, how="left")
            .dropna(how="all", axis=1)
        )

        # make dataframe with appropriate row and column indices
        df = pd.DataFrame(
            data=lca.inventory.todense(),
            index=pd.MultiIndex.from_frame(row_meta),
            columns=pd.MultiIndex.from_frame(col_meta),
        )
        return df
    # return dataframe in long format
    else:
        rows, cols = lca.inventory.nonzero()

        # map local matrix indices to global database ids
        rows_global = [lca.dicts.biosphere.reversed[r] for r in rows]
        cols_global = [lca.dicts.activity.reversed[c] for c in cols]

        # filter metadata
        row_meta = (
            pd.DataFrame(index=rows_global, data=rows_global, columns=["id"])
            .join(meta, how="left")
            .reset_index(drop=True)
        )
        col_meta = (
            pd.DataFrame(index=cols_global, data=cols_global, columns=["id"])
            .join(meta, how="left")
            .reset_index(drop=True)
        )

        # rename columns to avoid duplicate names for row and col
        row_meta.columns = ["source_" + c for c in row_meta.columns]
        col_meta.columns = ["target_" + c for c in col_meta.columns]

        # combine row and column metadata, drop columns which are empty
        index = pd.concat([row_meta, col_meta], axis=1).dropna(how="all", axis=1)
        se = pd.Series(
            index=pd.MultiIndex.from_frame(index),
            data=lca.inventory.data,
            name="value",
        )
        return se
