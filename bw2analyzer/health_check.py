# -*- coding: utf-8 -*
from .matrix_grapher import SparseMatrixGrapher
from .page_rank import PageRank
from bw2calc import LCA
from bw2data import Database, config
from bw2data.utils import safe_filename
from stats_arrays import *
import numpy as np
import os


class DatabaseHealthCheck(object):
    def __init__(self, database):
        self.db = Database(database)

    def check(self):
        pass

    def make_graphs(self):
        lca = LCA({self.db.random(): 1})
        lca.lci()
        tech_filepath = os.path.join(
            config.request_dir("export"),
            safe_filename(self.db.name)
        ) + u".technosphere.png"
        SparseMatrixGrapher(lca.technosphere_matrix).graph(tech_filepath, dpi=600)
        bio_filepath = os.path.join(
            config.request_dir("export"),
            safe_filename(self.db.name)
        ) + u".biosphere.png"
        SparseMatrixGrapher(lca.biosphere_matrix).graph(bio_filepath, dpi=600)
        return tech_filepath, bio_filepath

    def page_rank(self):
        return PageRank(self.db).calculate()

    def unique_exchanges(self):
        data = self.db.load()
        exchanges = [
            (exc[u'input'], exc[u'amount'])
            for ds in data.values()
            for exc in ds.get(u'exchanges', [])
            if exc[u'type'] in {u'biosphere', u'technosphere'}
        ]
        return len(set(exchanges)), len(exchanges)

    def uncertainty_check(self):
        data = self.db.load()
        results = {obj.id: {'total': 0, 'bad': 0} for obj in uncertainty_choices}
        for ds in data.values():
            for exc in ds.get(u'exchanges', []):
                ut = exc.get(u'uncertainty type')
                if ut == LognormalUncertainty.id:
                    results[ut]['total'] += 1
                    right_amount = np.allclose(np.log(np.abs(exc[u'amount'])), exc[u'loc'])
                    if not exc.get("scale") or not right_amount:
                        results[ut]['bad'] += 1
                elif ut == NormalUncertainty.id:
                    results[ut]['total'] += 1
                    if not exc.get(u"scale") or abs(exc[u'amount']) != exc[u'loc']:
                        results[ut]['bad'] += 1
                        print exc
                elif ut in {TriangularUncertainty.id, UniformUncertainty.id}:
                    results[ut]['total'] += 1
                    if exc['minimum'] == exc['maximum']:
                        results[ut]['bad'] += 1
                        print exc
        return results


