# encoding: utf-8
import numpy as np
from brightway2 import Database


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

    def annotate(self, sorted_data, rev_mapping):
        """Reverse the mapping from database ids to array indices"""
        return [(row[0], rev_mapping[row[1]]) for row in sorted_data]

    def top_processes(self, matrix, **kwargs):
        """Return an array of [value, index] technosphere processes."""
        return self.sort_array(np.array(matrix.sum(axis=0)).ravel(), **kwargs)

    def top_emissions(self, matrix, **kwargs):
        """Return an array of [value, index] biosphere emissions."""
        return self.sort_array(np.array(matrix.sum(axis=1)).ravel(), **kwargs)

    def annotated_top_processes(self, matrix, rev, **kwargs):
        return [(score, self.get_name(rev[index])) for score, index in \
            self.top_processes(matrix)]

    def annotated_top_emissions(self, matrix, rev, **kwargs):
        return [(score, self.get_name(rev[index])) for score, index in \
            self.top_emissions(matrix)]

    def get_name(self, name):
        if name[0] not in self.db_names:
            self.db_names[name[0]] = Database(name[0]).load()
        return self.db_names[name[0]][name]["name"]

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
        data = {"name": "LCA result", "children": []}
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
                "children": children
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
