import pandas as pd
from bw2data import get_activity
from bw2calc import LCA


def get_labeled_inventory(lca: LCA) -> pd.DataFrame:
    """
    Take an LCA's inventory matrix and labels its rows (biosphere) and columns (technosphere) with activity metadata.

    Args:
        * *lca* (bw2calc.LCA): LCA object whose life cycle inventory has been calculated previously.

    Returns:
        pd.DataFrame with activity information as row and column MultiIndices.
    """

    assert hasattr(
        lca, "inventory"
    ), "Must calculate life cycle inventory first. Please call lci()."

    rows = [
        get_activity(lca.dicts.biosphere.reversed[i]).as_dict()
        for i in range(lca.inventory.shape[0])
    ]
    columns = [
        get_activity(lca.dicts.activity.reversed[i]).as_dict()
        for i in range(lca.inventory.shape[1])
    ]

    return pd.DataFrame(
        data=lca.inventory.todense(),
        index=pd.MultiIndex.from_frame(pd.DataFrame(rows)),
        columns=pd.MultiIndex.from_frame(pd.DataFrame(columns)),
    )
