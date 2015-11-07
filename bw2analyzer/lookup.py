# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from bw2data import Database, Method
from bw2calc import LCA


class ParameterFinder(object):
    """Convenience class to find data about particular parameters, i.e. technosphere and biosphere exchanges and characterization factors."""
    def __init__(self, lca):
        assert isinstance(lca, LCA), "Must provide ``LCA`` object as input"
        self.lca = lca
        self.ra, self.rp, self.rb = self.lca.reverse_dict()

    def find_technosphere(self, row, col):
        inp = self.rp[row]
        inp_data = Database(inp[0]).load()[inp]
        outp = self.ra[col]
        outp_data = Database(outp[0]).load()[outp]
        try:
            exc = [x for x in outp_data.get("exchanges", []) if x['input'] == inp][0]
        except IndexError:
            raise ValueError("Can't find this exchange")
        return {
            'input': {
                'key': inp,
                'data': inp_data
            },
            'output': {
                'key': outp,
                'data': outp_data
            },
            'exchange': exc
        }

    def find_biosphere(self, row, col):
        inp = self.rb[row]
        inp_data = Database(inp[0]).load()[inp]
        outp = self.ra[col]
        outp_data = Database(outp[0]).load()[outp]
        try:
            exc = [x for x in outp_data.get("exchanges", []) if x['input'] == inp][0]
        except IndexError:
            raise ValueError("Can't find this exchange")
        return {
            'input': {
                'key': inp,
                'data': inp_data
            },
            'output': {
                'key': outp,
                'data': outp_data
            },
            'exchange': exc
        }

    def find_characterization(self, row):
        # Doesn't work for regionalized LCIA methods
        flow = self.rb[row]
        flow_data = Database(flow[0]).load()[flow]
        method = Method(self.lca.method)
        try:
            cf = [x for x in method.load() if x[0] == flow][0][1]
        except:
            raise ValueError("Can't find this CF")
        return {
            'flow': {
                'key': flow,
                'data': flow_data
            },
            'cf': cf
        }
