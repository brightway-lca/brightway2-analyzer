# -*- coding: utf-8 -*
from __future__ import division
try:
    import matplotlib.pyplot as plt
except ImportError:
    raise ImportError("Must have matplotlib installed for SparseMatrixGrapher")



class SparseMatrixGrapher(object):
    def __init__(self, matrix):
        self.matrix = matrix

    def graph(self, filename=None, marker_string='c.', mew=0, ms=1, alpha=0.8,
              width=None, height=None, dpi=300):
        tm = self.matrix.tocoo()
        y, x = self.matrix.shape
        plt.figure(figsize=(width or x / 1000, height or y / 1000))
        ax = plt.axes([0, 0, 1, 1])
        # Start from top left corner, not bottom left corner
        ax.plot(tm.shape[1] - tm.col, tm.row, marker_string, mew=mew, ms=ms, alpha=alpha)
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')
        ax.xaxis.set_ticklabels([])
        ax.yaxis.set_ticklabels([])
        ax.set_ylim((0, tm.shape[0]))
        ax.set_xlim((0, tm.shape[1]))
        plt.box(False)
        if filename:
            plt.savefig(filename, dpi=300)
