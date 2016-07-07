# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from .page_rank import PageRank
from bw2calc import LCA
from bw2data import Database, projects
from bw2data.utils import safe_filename
from stats_arrays import *
import numpy as np
import os
try:
    from .matrix_grapher import SparseMatrixGrapher
except ImportError:
    import warnings
    warnings.warn(u"Must have matplotlib installed for sparse matrix graph")
    SparseMatrixGrapher = None


class DatabaseHealthCheck(object):
    def __init__(self, database):
        self.db = Database(database)
        self.db.filters = {'type': 'process'}

    def check(self, graphs_dir=None):
        tg, tfn, bg, bfn = self.make_graphs(graphs_dir)
        aggregated = self.aggregated_processes()
        return {
            'tg': tg,
            'tfn': tfn,
            'bg': bg,
            'bfn': bfn,
            'pr': self.page_rank(),
            'ue': self.unique_exchanges(),
            'uncertainty': self.uncertainty_check(),
            'sp': aggregated['system_processes'],
            'me': aggregated['many_exchanges'],
            'nsp': self.no_self_production(),
            'mo': self.multioutput_processes(),
            'ob': self.ouroboros(),
        }

    def make_graphs(self, graphs_dir=None):
        if not SparseMatrixGrapher:
            return "", "", "", ""
        lca = LCA({self.db.random(): 1})
        lca.lci()
        tech_filename = safe_filename(self.db.name) + u".technosphere.png"
        tech_filepath = os.path.join(
            graphs_dir or projects.output_dir,
            tech_filename
        )
        SparseMatrixGrapher(lca.technosphere_matrix).graph(tech_filepath, dpi=600)
        bio_filename = safe_filename(self.db.name) + u".biosphere.png"
        bio_filepath = os.path.join(
            graphs_dir or projects.output_dir,
            bio_filename
        )
        SparseMatrixGrapher(lca.biosphere_matrix).graph(bio_filepath, dpi=600)
        return tech_filepath, tech_filename, bio_filepath, bio_filename

    def page_rank(self):
        return PageRank(self.db).calculate()

    def unique_exchanges(self):
        data = self.db.load()
        exchanges = [
            (exc[u'input'], exc[u'amount'], exc[u"type"])
            for ds in data.values()
            for exc in ds.get(u'exchanges', [])
            if exc[u'type'] in {u'biosphere', u'technosphere'}
        ]
        bio_exchanges = [obj for obj in exchanges if obj[2] == u"biosphere"]
        tech_exchanges = [obj for obj in exchanges if obj[2] == u"technosphere"]
        return len(tech_exchanges), len(set(tech_exchanges)), \
            len(bio_exchanges), len(set(bio_exchanges))

    def uncertainty_check(self):
        # TODO: Also report no (None) uncertainty
        data = self.db.load()
        results = {obj.id: {'total': 0, 'bad': 0} for obj in uncertainty_choices}
        for ds in data.values():
            for exc in ds.get(u'exchanges', []):
                ut = exc.get(u'uncertainty type')
                if ut is None:
                    continue
                results[ut]['total'] += 1
                if ut == LognormalUncertainty.id:
                    right_amount = np.allclose(np.log(np.abs(exc[u'amount'])), exc[u'loc'], rtol=1e-3)
                    if not exc.get("scale") or not right_amount:
                        results[ut]['bad'] += 1
                elif ut == NormalUncertainty.id:
                    if not exc.get(u"scale") or abs(exc[u'amount']) != exc[u'loc']:
                        results[ut]['bad'] += 1
                elif ut in {TriangularUncertainty.id, UniformUncertainty.id}:
                    if exc['minimum'] >= exc['maximum']:
                        results[ut]['bad'] += 1
        return results

    def multioutput_processes(self):
        num_production_exchanges = [
            (key, len([
                exc for exc in ds.get(u"exchanges")
                if exc[u"type"] == u"production"
                and exc[u"input"] != key
            ])) for key, ds in self.db.load().items()]
        return [obj for obj in num_production_exchanges if obj[1]]

    def aggregated_processes(self, cutoff=500):
        num_exchanges = {key: {
                u"technosphere": len([
                    exc for exc in value.get(u"exchanges", [])
                    if exc[u"type"] == u"technosphere"
                ]),
                u"biosphere": len([
                    exc for exc in value.get(u"exchanges", [])
                    if exc[u"type"] == u"biosphere"
                ]),
                } for key, value in self.db.load().items()
                if value.get(u"type", u"process") == u"process"
        }
        system_processes = [
            (key, value[u"biosphere"])
            for key, value in num_exchanges.items()
            if value[u"technosphere"] == 0 and value[u"biosphere"] > cutoff
        ]
        many_exchanges = [
            (key, value[u"technosphere"])
            for key, value in num_exchanges.items()
            if value[u"technosphere"] > cutoff
        ]
        return {
            'system_processes': system_processes,
            'many_exchanges': many_exchanges
        }

    def no_self_production(self):
        self_production = lambda a, b: not a or b in a
        return {
            key for key, value in self.db.load().items()
            if value.get(u"type", u"process") == u"process"
            and not self_production({
                exc[u"input"] for exc in value.get(u"exchanges", [])
                if exc[u"type"] == u"production"
            }, key)
        }

    def ouroboros(self):
        """Find processes that consume their own reference products as inputs. Not necessarily an error, but should be examined carefully (see `Two potential points of confusion in LCA math <http://chris.mutel.org/too-confusing.html>`__).

        Returns:
            A set of database keys.

        """
        return {
            key for key, value in self.db.load().items()
            if any(
                exc for exc in value.get(u"exchanges", [])
                if exc[u"input"] == key
                and exc[u"type"] == u"technosphere"
            )
        }
