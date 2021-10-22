import os

import numpy as np
from bw2calc import LCA
from bw2data import Database, projects
from stats_arrays import (
    LognormalUncertainty,
    NormalUncertainty,
    TriangularUncertainty,
    UniformUncertainty,
    uncertainty_choices,
)

from .matrix_grapher import SparseMatrixGrapher
from .page_rank import PageRank


class DatabaseHealthCheck:
    def __init__(self, database):
        self.db = Database(database)
        self.db.filters = {"type": "process"}

    def check(self, graphs_dir=None):
        tg, tfn, bg, bfn = self.make_graphs(graphs_dir)
        aggregated = self.aggregated_processes()
        return {
            "tg": tg,
            "tfn": tfn,
            "bg": bg,
            "bfn": bfn,
            "pr": self.page_rank(),
            "ue": self.unique_exchanges(),
            "uncertainty": self.uncertainty_check(),
            "sp": aggregated["system_processes"],
            "me": aggregated["many_exchanges"],
            "nsp": self.no_self_production(),
            "mo": self.multioutput_processes(),
            "ob": {},
        }

    def make_graphs(self, graphs_dir=None):
        lca = LCA({self.db.random(): 1})
        lca.lci()
        tech_filename = self.db.filename + ".technosphere.png"
        tech_filepath = os.path.join(graphs_dir or projects.output_dir, tech_filename)
        SparseMatrixGrapher(lca.technosphere_matrix).graph(tech_filepath, dpi=600)
        bio_filename = self.db.filename + ".biosphere.png"
        bio_filepath = os.path.join(graphs_dir or projects.output_dir, bio_filename)
        SparseMatrixGrapher(lca.biosphere_matrix).graph(bio_filepath, dpi=600)
        return tech_filepath, tech_filename, bio_filepath, bio_filename

    def page_rank(self):
        return PageRank(self.db).calculate()

    def unique_exchanges(self):
        data = self.db.load()
        exchanges = [
            (exc["input"], exc["amount"], exc["type"])
            for ds in data.values()
            for exc in ds.get("exchanges", [])
            if exc["type"] in {"biosphere", "technosphere"}
        ]
        bio_exchanges = [obj for obj in exchanges if obj[2] == "biosphere"]
        tech_exchanges = [obj for obj in exchanges if obj[2] == "technosphere"]
        return (
            len(tech_exchanges),
            len(set(tech_exchanges)),
            len(bio_exchanges),
            len(set(bio_exchanges)),
        )

    def uncertainty_check(self):
        # TODO: Also report no (None) uncertainty
        data = self.db.load()
        results = {obj.id: {"total": 0, "bad": 0} for obj in uncertainty_choices}
        for ds in data.values():
            for exc in ds.get("exchanges", []):
                ut = exc.get("uncertainty type")
                if ut is None:
                    continue
                results[ut]["total"] += 1
                if ut == LognormalUncertainty.id:
                    right_amount = np.allclose(
                        np.log(np.abs(exc["amount"])), exc["loc"], rtol=1e-3
                    )
                    if not exc.get("scale") or not right_amount:
                        results[ut]["bad"] += 1
                elif ut == NormalUncertainty.id:
                    if not exc.get("scale") or abs(exc["amount"]) != exc["loc"]:
                        results[ut]["bad"] += 1
                elif ut in {TriangularUncertainty.id, UniformUncertainty.id}:
                    if exc["minimum"] >= exc["maximum"]:
                        results[ut]["bad"] += 1
        return results

    def multioutput_processes(self):
        num_production_exchanges = [
            (
                key,
                len(
                    [
                        exc
                        for exc in ds.get("exchanges")
                        if exc["type"] == "production" and exc["input"] != key
                    ]
                ),
            )
            for key, ds in self.db.load().items()
        ]
        return [obj for obj in num_production_exchanges if obj[1]]

    def aggregated_processes(self, cutoff=500):
        num_exchanges = {
            key: {
                "technosphere": len(
                    [
                        exc
                        for exc in value.get("exchanges", [])
                        if exc["type"] == "technosphere"
                    ]
                ),
                "biosphere": len(
                    [
                        exc
                        for exc in value.get("exchanges", [])
                        if exc["type"] == "biosphere"
                    ]
                ),
            }
            for key, value in self.db.load().items()
            if value.get("type", "process") == "process"
        }
        system_processes = [
            (key, value["biosphere"])
            for key, value in num_exchanges.items()
            if value["technosphere"] == 0 and value["biosphere"] > cutoff
        ]
        many_exchanges = [
            (key, value["technosphere"])
            for key, value in num_exchanges.items()
            if value["technosphere"] > cutoff
        ]
        return {"system_processes": system_processes, "many_exchanges": many_exchanges}

    def no_self_production(self):
        def self_production(ds):
            return any(
                exc.input == exc.output
                for exc in ds.get("exchanges", [])
                if exc["type"] in ("production", "generic production")
            )

        return {
            ds.key
            for ds in self.db
            if ds.get("type", "process") == "process" and not self_production(ds)
        }

    # def ouroboros(self):
    #     """Find processes that consume their own reference products as inputs. Not necessarily an error, but should be examined carefully (see `Two potential points of confusion in LCA math <http://chris.mutel.org/too-confusing.html>`__).

    #     Returns:
    #         A set of database keys.

    #     """
    #     return {
    #         key
    #         for key, value in self.db.load().items()
    #         if any(
    #             exc
    #             for exc in value.get("exchanges", [])
    #             if exc["input"] == key and exc["type"] == "technosphere"
    #         )
    #     }
