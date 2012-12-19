# encoding: utf-8
from __future__ import division
from brightway2 import Database
import numpy as np


class ContributionAnalysis(object):
    def __init__(self):
        self.db_names = {}

    def sort_array(self, data, limit=25, limit_type="number", total=None):
        """Common sorting function for all top methods."""
        total = total or np.abs(data).sum()
        if limit_type not in ("number", "percent"):
            raise ValueError("limit_type must be either 'percent' or 'index'.")
        if limit_type == "percent":
            if 0 <= limit >= 1:
                raise ValueError("Percentage limits must be between 0 and 1.")
            limit = (data > (total * limit)).sum()

        results = np.hstack((data.reshape((-1, 1)),
            np.arange(data.shape[0]).reshape((-1, 1))))
        return results[np.argsort(np.abs(data))[::-1]][:limit, :]

    def top_coo_matrix(self, matrix, rows=5, cols=5):
        """Return ``rows`` by ``cols`` top processes and emissions."""
        t = np.argsort(np.abs(np.array(matrix.sum(axis=0)).ravel())
            )[:-rows - 1:-1]
        b = np.argsort(np.abs(np.array(matrix.sum(axis=1)).ravel())
            )[:-cols - 1:-1]
        r = []
        for row, x in enumerate(b):
            for col, y in enumerate(t):
                if matrix[x, y] > 0:
                    r.append((row, col, float(matrix[x, y])))
        return r, b, t

    def hinton_matrix(self, lca, rows=5, cols=5):
        coo, b, t = self.top_coo_matrix(lca.characterized_inventory.data,
            rows=rows, cols=cols)
        rt, rb = lca.reverse_dict()
        flows = [self.get_name(rb[x]) for x in b]
        activities = [self.get_name(rt[x]) for x in t]
        return {"results": coo, "total": lca.score, "xlabels": activities,
            "ylabels": flows}

    def annotate(self, sorted_data, rev_mapping):
        """Reverse the mapping from database ids to array indices"""
        return [(row[0], rev_mapping[row[1]]) for row in sorted_data]

    def top_processes(self, matrix, **kwargs):
        """Return an array of [value, index] technosphere processes."""
        return self.sort_array(np.array(matrix.sum(axis=0)).ravel(), **kwargs)

    def top_emissions(self, matrix, **kwargs):
        """Return an array of [value, index] biosphere emissions."""
        return self.sort_array(np.array(matrix.sum(axis=1)).ravel(), **kwargs)

    def annotated_top_processes(self, lca, **kwargs):
        rt, rb = lca.reverse_dict()
        return [(score, self.get_name(rt[index])) for score, index in \
            self.top_processes(lca.characterized_inventory.data)]

    def annotated_top_emissions(self, lca, **kwargs):
        rt, rb = lca.reverse_dict()
        return [(score, self.get_name(rb[index])) for score, index in \
            self.top_emissions(lca.characterized_inventory.data)]

    def get_name(self, name):
        if name[0] not in self.db_names:
            self.db_names[name[0]] = Database(name[0]).load()
        return self.db_names[name[0]][name]["name"]

    def gini_coefficient(self, matrix, total, limit=100):
        """Calculate the Gini coefficient for the top ``limit`` contributing processes.

        This is a measure of the relative importance of the top-scoring processes compared to other important processes."""
        raise NotImplemented
        data = self.top_processes(matrix, limit=limit)[::-1, 0]
        expected = np.arange(1, limit + 1) / total

    def concentration_ratio(self, matrix, total, limit=4):
        """A measure of the concentration of LCA scores in the highest contributing processes.

        The `concentration ration <http://en.wikipedia.org/wiki/Concentration_ratio>`_ ranges from 0 to 1, and is commonly calculated for 4 or 8 firms (processes)."""
        return float(self.top_processes(matrix, limit=limit)[:, 0].sum() \
            / total)

    def herfindahl_index(self, matrix, total, limit=50):
        """Another measure of the concentration of LCA scores in the highest contributing processes.

        The normalized `Herfindahl index <http://en.wikipedia.org/wiki/Herfindahl_index>`_ ranges from 0 to 1, with 1 being representing a single process accounting for the complete LCA score."""
        return float(((self.top_processes(matrix, limit=limit)[::-1, 0] \
            / total) ** 2).sum() - 1 / limit) / (1 - 1 / limit)

    def d3_treemap(self, matrix, rev_bio, rev_techno, limit=0.025,
            limit_type="percent"):
        """
Construct treemap input data structure for LCA result. Output like:

    {
    "name": "LCA result",
    "children": [{
        "name": process 1,
        "children": [
            {"name": emission 1, "size": score},
            {"name": emission 2, "size": score},
            ],
        }]
    }

        """
        total = np.abs(matrix).sum()
        processes = self.top_processes(matrix, limit=limit,
            limit_type=limit_type)
        data = {"name": "LCA result", "children": [], "size": total}
        for dummy, tech_index in processes:
            name = self.get_name(rev_techno[tech_index])
            this_score = np.abs(matrix[:, tech_index].toarray().ravel()).sum()
            children = []
            for score, bio_index in self.sort_array(matrix[:, tech_index
                    ].toarray().ravel(), limit=limit, limit_type=limit_type,
                    total=total):
                children.append({"name": self.get_name(rev_bio[bio_index]),
                    "size": float(abs(matrix[bio_index, tech_index]))})
            children_score = sum([x["size"] for x in children])
            if children_score < (0.95 * this_score):
                children.append({"name": "Others", "size":
                    this_score - children_score})
            data["children"].append({
                "name": name,
                "size": this_score,
                # "children": children
                })
        return data

    # def top_emissions_for_process(self, process, **kwargs):
    #     if hasattr(process, "id"):
    #         process = process.id
    #     if not hasattr(self.dicts, 'reverse'):
    #         self.construct_reverse_dicts()
    #     return self._top(array(self.weighted_biosphere[:,process].todense( 
    #         )).ravel(), self.dicts.reverse.biosphere, **kwargs)

    # def top_processes_for_emission(self, biosphere_flow, **kwargs):
    #     if hasattr(biosphere_flow, "id"):
    #         biosphere_flow = biosphere_flow.id
    #     if not hasattr(self.dicts, 'reverse'):
    #         self.construct_reverse_dicts()
    #     return self._top(array(self.weighted_biosphere[biosphere_flow,: 
    #         ].todense()).ravel(), self.dicts.reverse.technosphere, **kwargs)

    # def top_processes_for_emission_inventory(self, emission, **kwargs):
    #     """Get the most important inventory processes for an emission"""
    #     if hasattr(emission, "id"):
    #         emission = emission.id
    #     if not hasattr(self.dicts, 'reverse'):
    #         self.construct_reverse_dicts()
    #     return self._top(array(self.calculated_biosphere[emission,:].todense( 
    #         )).ravel(), self.dicts.reverse.technosphere, **kwargs)
