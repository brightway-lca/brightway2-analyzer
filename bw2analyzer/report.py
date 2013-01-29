# -*- coding: utf-8 -*-
from __future__ import division
from . import ContributionAnalysis
from brightway2 import JsonWrapper, methods, config
from bw2calc import ParallelMonteCarlo, LCA
from scipy.stats import gaussian_kde
import numpy as np
import os
import uuid


class SerializedLCAReport(object):
    """A complete LCA report (i.e. LCA score, Monte Carlo uncertainty analysis, contribution analysis) that can be serialized to a defined standard."""
    version = 1

    def __init__(self, activity, method, iterations=10000, cpus=None,
            outliers=0.025):
        self.activity = activity
        self.method = method
        self.iterations = iterations
        self.cpus = cpus
        self.outliers = outliers
        self.uuid = uuid.uuid4().hex

    def calculate(self):
        lca = LCA(self.activity, self.method)
        lca.lci()
        lca.lcia()
        rt, rb = lca.reverse_dict()

        ca = ContributionAnalysis()
        hinton = ca.hinton_matrix(lca)
        treemap = ca.d3_treemap(lca.characterized_inventory.data, rb, rt)
        herfindahl = ca.herfindahl_index(
            lca.characterized_inventory.data, lca.score)
        concentration = ca.concentration_ratio(
            lca.characterized_inventory.data, lca.score)

        self.report = {
            "activity": [(ca.get_name(k), "%.2g" % v, ca.db_names[k[0]][k][
                "unit"]) for k, v in self.activity.iteritems()],
            "method": {
                "name": ": ".join(self.method),
                "unit": methods[self.method]["unit"]
                },
            "score": float(lca.score),
            "contribution": {
                "hinton": hinton,
                "treemap": treemap,
                "herfindahl": herfindahl,
                "concentration": concentration
                },
            "monte carlo": self.get_monte_carlo(),
            "version": self.version,
            "uuid": self.uuid
            }

    def get_monte_carlo(self):
        mc_data = np.array(ParallelMonteCarlo(
            self.activity,
            self.method,
            iterations=self.iterations,
            cpus=self.cpus
            ).calculate())
        mc_data.sort()
        # Filter outliers
        offset = int(self.outliers * mc_data.shape[0])
        lower = mc_data[int(0.025 * self.iterations)]
        upper = mc_data[int(0.975 * self.iterations)]
        mc_data = mc_data[offset:-offset]
        num_bins = max(
            100,
            min(20, int(np.sqrt(self.iterations)))
            )
        # Gaussian KDE to smooth fit
        kde = gaussian_kde(mc_data)
        kde_xs = np.linspace(mc_data.min(), mc_data.max(), 500)
        kde_ys = kde.evaluate(kde_xs)
        # Histogram
        hist_ys, hist_xs = np.histogram(mc_data, bins=num_bins, density=True)
        hist_xs = np.repeat(hist_xs, 2)
        hist_ys = np.hstack((
            np.array(0),
            np.repeat(hist_ys, 2),
            np.array(0),
            ))
        return {
            "smoothed": zip(kde_xs.tolist(), kde_ys.tolist()),
            "histogram": zip(hist_xs.tolist(), hist_ys.tolist()),
            "statistics": {
                "median": float(np.median(mc_data)),
                "mean": float(np.mean(mc_data)),
                "interval": [float(lower), float(upper)],
                }
            }

    def write(self):
        dirpath = config.request_dir("reports")
        filepath = os.path.join(dirpath, "report.%s.json" % self.uuid)
        JsonWrapper.dump(self.report, filepath)
