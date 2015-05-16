# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from brightway2 import Database, databases


class DatabaseExplorer(object):
    def __init__(self, name):
        self.db = Database(name)
        self.data = self.db.load()
        for db in databases[name]["depends"]:
            self.data.update(Database(db).load())

    def uses_this_process(self, key, recursion=0):
        if recursion:
            return dict([(k, self.uses_this_process(k, recursion - 1)) for \
                k in self.data if key in [e["input"] for e in \
                self.data[k].get("exchanges", [])]])
        else:
            return [k for k in self.data if key in [e["input"] for e in \
                self.data[k].get("exchanges", [])]]

    def provides_this_process(self, key, recursion=0):
        if recursion:
            return dict([(e["input"], self.provides_this_process(e["input"], recursion - 1)) for e in self.data[key].get("exchanges", [])])
        else:
            return [(e["input"], ()) for e in self.data[key].get("exchanges", [])]
