# encoding: utf-8
from brightway2 import *


class DatabaseExplorer(object):
    def __init__(self, name):
        self.db = Database(name)

    def uses_this_process(self, key):
        data = db.load()
        return [k for k in data if key in [e["input"] for e in \
            data[k]["exchanges"]]]
