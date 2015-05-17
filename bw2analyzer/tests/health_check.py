# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from .fixtures import lci_fixture, method_fixture
from ..health_check import DatabaseHealthCheck
from bw2data import Database, Method
from bw2data.tests import BW2DataTest


class DHCMock(DatabaseHealthCheck):
    def make_graphs(self, foo):
        return 1, 1, 1, 1


class HealthCheckTestCase(BW2DataTest):
    def test_health_check(self):
        db = Database("a")
        db.write(lci_fixture)
        method = Method(('method',))
        method.register()
        method.write(method_fixture)
        dhc = DHCMock("a").check()
