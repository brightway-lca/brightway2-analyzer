# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division
from eight import *

import numpy as np
try:
    import matplotlib.pyplot as plt
except ImportError:
    raise ImportError("Must have matplotlib installed for SparseMatrixGrapher")
try:
    from scipy.sparse.csgraph import reverse_cuthill_mckee
except ImportError:
    reverse_cuthill_mckee = False


class SparseMatrixGrapher(object):
    def __init__(self, matrix):
        self.matrix = matrix

    def graph(self, filename=None, marker_string='c.', mew=0.5, ms=1, alpha=0.8,
              width=None, height=None, dpi=300):
        tm = self.matrix.tocoo()
        y, x = self.matrix.shape
        plt.figure(figsize=(width or x / 1000, height or y / 1000))
        ax = plt.axes([0, 0, 1, 1])
        # Start from top left corner, not bottom left corner
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')
        ax.xaxis.set_ticklabels([])
        ax.yaxis.set_ticklabels([])
        ax.plot(tm.shape[1] - tm.col, tm.row, marker_string, mew=mew, ms=ms, alpha=alpha)
        ax.set_ylim((0, tm.shape[0]))
        ax.set_xlim((0, tm.shape[1]))
        plt.box(False)
        if filename:
            plt.savefig(filename, dpi=dpi)

    def magnitude_graph(self, filename=None, dpi=600, width=None, height=None):
        def get_relative_scores(data):
            return np.abs(data) / np.max(np.abs(data))

        def get_colors(distances):
            cmap = plt.get_cmap("Dark2")
            return cmap(distances)

        def unroll(data):
            return [list(row) for row in data]

        nm = reverse_cuthill_mckee(self.matrix)
        ro = self.matrix[nm, :][:, nm]
        as_coo = ro.tocoo()
        y, x = as_coo.shape

        colors = unroll(get_colors(get_relative_scores(as_coo.data)))

        plt.figure(figsize=(width or x / 1000, height or y / 1000))
        ax = plt.axes([0,0,1,1])
        plt.scatter(list(as_coo.shape[1] - as_coo.col), list(as_coo.row),
                    s=10, c=colors, marker=".", edgecolors="None")
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')
        ax.xaxis.set_ticklabels([])
        ax.yaxis.set_ticklabels([])
        ax.set_ylim((0, self.matrix.shape[0]))
        ax.set_xlim((0, self.matrix.shape[1]))
        plt.box(False)
        if filename:
            plt.savefig(filename, dpi=dpi)

    def ordered_graph(self, filename=None, dpi=600, width=None, height=None):
        def get_distances(xs, ys):
            z = np.abs(xs - ys) / 2
            return np.sqrt(2 * z ** 2) / MAX_DIST

        def get_colors(distances):
            cmap = plt.get_cmap("Dark2")
            return cmap(distances)

        def unroll(data):
            return [list(row) for row in data]

        nm = reverse_cuthill_mckee(self.matrix)
        ro = self.matrix[nm, :][:, nm]
        as_coo = ro.tocoo()
        y, x = as_coo.shape
        MAX_DIST = np.sqrt(2 * (x / 2.) ** 2)

        colors = unroll(get_colors(get_distances(as_coo.col, as_coo.row)))

        plt.figure(figsize=(width or x / 1000, height or y / 1000))
        ax = plt.axes([0,0,1,1])
        plt.scatter(list(as_coo.shape[1] - as_coo.col), list(as_coo.row),
                    s=10, c=colors, marker=".", edgecolors="None")
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')
        ax.xaxis.set_ticklabels([])
        ax.yaxis.set_ticklabels([])
        ax.set_ylim((0, self.matrix.shape[0]))
        ax.set_xlim((0, self.matrix.shape[1]))
        plt.box(False)
        if filename:
            plt.savefig(filename, dpi=dpi)
