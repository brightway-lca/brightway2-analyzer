# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from .fixtures import lci_fixture
from ..matrix_grapher import SparseMatrixGrapher
from bw2calc import LCA
from bw2data import Database
from bw2data.tests import BW2DataTest


class MatrixGrapherTestCase(BW2DataTest):
    def get_lca(self):
        db = Database("a")
        db.write(lci_fixture)
        lca = LCA({("a", "2"): 1})
        lca.lci()
        return lca

    def test_graph_no_file(self):
        lca = self.get_lca()
        SparseMatrixGrapher(lca.technosphere_matrix).graph(width=2, height=2)

    def test_graph(self):
        lca = self.get_lca()
        SparseMatrixGrapher(lca.technosphere_matrix).graph("foo", width=2, height=2)

    def test_ordered_graph_no_file(self):
        lca = self.get_lca()
        SparseMatrixGrapher(lca.technosphere_matrix).ordered_graph(width=2, height=2)

    def test_ordered_graph(self):
        lca = self.get_lca()
        SparseMatrixGrapher(lca.technosphere_matrix).ordered_graph("foo", width=2, height=2)
