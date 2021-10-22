import os
import uuid

import numpy as np
import requests
from bw2calc import LCA, GraphTraversal, ParallelMonteCarlo
from bw2data import JsonWrapper, config, get_activity, methods, projects
from scipy.stats import gaussian_kde

from .contribution import ContributionAnalysis
from .econ import concentration_ratio, herfindahl_index
from .sc_graph import GTManipulator


class SerializedLCAReport:
    """A complete LCA report (i.e. LCA score, Monte Carlo uncertainty analysis, contribution analysis) that can be serialized to a defined standard."""

    version = 2

    def __init__(self, activity, method, iterations=10000, cpus=None, outliers=0.025):
        self.activity = activity
        self.method = method
        self.iterations = iterations
        self.cpus = cpus
        self.outliers = outliers
        self.uuid = uuid.uuid4().hex

    def calculate(self):
        """Calculate LCA report data"""
        lca = LCA(self.activity, self.method)
        lca.lci()
        lca.lcia()

        gt = GraphTraversal().calculate(self.activity, method=self.method)
        print("FD")
        force_directed = self.get_force_directed(gt["nodes"], gt["edges"], lca)
        print("CA")
        ca = ContributionAnalysis()
        print("hinton")
        hinton = ca.hinton_matrix(lca)
        print("treemap")
        treemap = self.get_treemap(gt["nodes"], gt["edges"], lca)
        print("herfindahl")
        herfindahl = herfindahl_index(lca.characterized_inventory.data)
        print("concentration")
        concentration = concentration_ratio(lca.characterized_inventory.data)
        print("MC:")
        monte_carlo = self.get_monte_carlo()

        activity_data = []
        for k, v in self.activity.items():
            obj = get_activity(k)
            activity_data.append((obj["name"], "%.2g" % v, obj["unit"]))

        self.report = {
            "activity": activity_data,
            "method": {
                "name": ": ".join(self.method),
                "unit": methods[self.method]["unit"],
            },
            "score": float(lca.score),
            "contribution": {
                "hinton": hinton,
                "treemap": treemap,
                "herfindahl": herfindahl,
                "concentration": concentration,
            },
            "force_directed": force_directed,
            "monte carlo": monte_carlo,
            "metadata": {
                "type": "Brightway2 serialized LCA report",
                "version": self.version,
                "uuid": self.uuid,
            },
        }

    def get_treemap(self, nodes, edges, lca, unroll_cutoff=0.01, simplify_limit=0.1):
        nodes, edges, links = GTManipulator.unroll_graph(
            nodes, edges, lca.score, cutoff=unroll_cutoff
        )
        nodes, edges = GTManipulator.simplify(
            nodes, edges, lca.score, limit=simplify_limit
        )
        return GTManipulator.d3_treemap(nodes, edges, lca)

    def get_monte_carlo(self):
        """Get Monte Carlo results"""
        print("Entered get_monte_carlo")
        if not self.iterations:
            # No Monte Carlo desired
            return None
        mc_data = ParallelMonteCarlo(
            self.activity, self.method, iterations=self.iterations, cpus=self.cpus
        ).calculate()
        print("Converting to array")
        mc_data = np.array(mc_data)
        print("Checking shape")
        if np.unique(mc_data).shape[0] == 1:
            # No uncertainty in database
            return None
        print("Finished MC .calculate(); Sorting")
        mc_data.sort()
        # Filter outliers
        print("Filter outliers")
        offset = int(self.outliers * mc_data.shape[0])
        lower = mc_data[offset]
        upper = mc_data[-offset]
        mc_data = mc_data[offset:-offset]
        num_bins = max(100, min(20, int(np.sqrt(self.iterations))))
        # Gaussian KDE to smooth fit
        print("KDE smoothing")
        kde = gaussian_kde(mc_data)
        kde_xs = np.linspace(mc_data.min(), mc_data.max(), 500)
        kde_ys = kde.evaluate(kde_xs)
        # Histogram
        print("Histogram")
        hist_ys, hist_xs = np.histogram(mc_data, bins=num_bins, density=True)
        hist_xs = np.repeat(hist_xs, 2)
        hist_ys = np.hstack(
            (
                np.array(0),
                np.repeat(hist_ys, 2),
                np.array(0),
            )
        )
        print("Finished .get_monte_carlo")
        return {
            "smoothed": zip(kde_xs.tolist(), kde_ys.tolist()),
            "histogram": zip(hist_xs.tolist(), hist_ys.tolist()),
            "statistics": {
                "median": float(np.median(mc_data)),
                "mean": float(np.mean(mc_data)),
                "interval": [float(lower), float(upper)],
            },
        }

    def get_force_directed(self, nodes, edges, lca):
        """Get graph traversal results"""
        nodes, edges = GTManipulator.simplify_naive(nodes, edges, lca.score)
        nodes = GTManipulator.add_metadata(nodes, lca)
        return GTManipulator.d3_force_directed(nodes, edges, lca.score)

    def write(self):
        """Write report data to file"""
        dirpath = projects.request_directory("reports")
        filepath = os.path.join(dirpath, "report.%s.json" % self.uuid)
        JsonWrapper.dump(self.report, filepath)

    def upload(self):
        """Upload report data if allowed"""
        if not config.p.get("upload_reports", False) or not config.p.get(
            "report_server_url", None
        ):
            raise ValueError("Report uploading not allowed")
        url = config.p["report_server_url"]
        if url[-1] != "/":
            url += "/"
        r = requests.post(
            url + "upload",
            data=JsonWrapper.dumps(self.report),
            headers={"content-type": "application/json"},
        )
        if r.status_code == 200:
            report_url = url + "report/" + self.uuid
            self.report["metadata"]["online"] = report_url
            return report_url
        else:
            return False
