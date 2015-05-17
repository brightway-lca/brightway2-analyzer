# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from ..utils import group_by_emissions
from bw2data import Database, Method
from bw2data.tests import BW2DataTest


class GroupingTestCase(BW2DataTest):
    def test_grouping_together(self):
        biosphere_data = {
            ("biosphere", "1"): {
                'categories': ['air', 'this'],
                'exchanges': [],
                'name': 'some bad stuff',
                'type': 'emission',
                'unit': 'kg'
                },
            ("biosphere", "2"): {
                'categories': ['air', 'that'],
                'exchanges': [],
                'name': 'some bad stuff',
                'type': 'emission',
                'unit': 'kg'
                },
        }

        biosphere = Database("biosphere")
        biosphere.register(name="Tests", depends=[])
        biosphere.write(biosphere_data)

        method = Method(("test", "LCIA", "method"))
        method.register(unit="points")
        method.write([
            (("biosphere", "1"), 1.0, "GLO"),
            (("biosphere", "2"), 1.0, "GLO")
        ])

        answer = {
            ('some bad stuff', 'air', 'kg'): [1.0, 1.0]
        }
        self.assertEqual(group_by_emissions(method), answer)

    def test_grouping_separate_name(self):
        biosphere_data = {
            ("biosphere", "1"): {
                'categories': ['s', 'this'],
                'exchanges': [],
                'name': 'some bad stuff',
                'type': 'emission',
                'unit': 'kg'
                },
            ("biosphere", "2"): {
                'categories': ['s', 'that'],
                'exchanges': [],
                'name': 'some more bad stuff',
                'type': 'emission',
                'unit': 'kg'
                },
        }

        biosphere = Database("biosphere")
        biosphere.register(name="Tests", depends=[])
        biosphere.write(biosphere_data)

        method = Method(("test", "LCIA", "method"))
        method.register(unit="points")
        method.write([
            (("biosphere", "1"), 1.0, "GLO"),
            (("biosphere", "2"), 2.0, "GLO")
        ])

        answer = {
            ('some bad stuff', 's', 'kg'): [1.0],
            ('some more bad stuff', 's', 'kg'): [2.0]
        }
        self.assertEqual(group_by_emissions(method), answer)

    def test_grouping_separate_unit(self):
        biosphere_data = {
            ("biosphere", "1"): {
                'categories': ['foo', 'this'],
                'exchanges': [],
                'name': 'some bad stuff',
                'type': 'emission',
                'unit': 'kg'
                },
            ("biosphere", "2"): {
                'categories': ['foo', 'that'],
                'exchanges': [],
                'name': 'some bad stuff',
                'type': 'emission',
                'unit': 'tonne'
                },
        }

        biosphere = Database("biosphere")
        biosphere.register(name="Tests", depends=[])
        biosphere.write(biosphere_data)

        method = Method(("test", "LCIA", "method"))
        method.register(unit="points")
        method.write([
            (("biosphere", "1"), 1.0, "GLO"),
            (("biosphere", "2"), 2.0, "GLO")
        ])

        answer = {
            ('some bad stuff', 'foo', 'kg'): [1.0],
            ('some bad stuff', 'foo', 'tonne'): [2.0]
        }
        self.assertEqual(group_by_emissions(method), answer)
