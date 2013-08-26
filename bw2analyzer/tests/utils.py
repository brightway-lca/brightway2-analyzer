from bw2data.tests import BW2DataTest
from bw2data import Database, Method
from ..utils import group_by_emissions


class GroupingTest(BW2DataTest):
    def test_grouping_together(self):
        biosphere_data = {
            ("biosphere", 1): {
                'categories': ['this'],
                'exchanges': [],
                'name': 'some bad stuff',
                'type': 'emission',
                'unit': 'kg'
                },
            ("biosphere", 2): {
                'categories': ['that'],
                'exchanges': [],
                'name': 'some bad stuff',
                'type': 'emission',
                'unit': 'kg'
                },
        }

        biosphere = Database("biosphere")
        biosphere.register("Tests", [], len(biosphere_data))
        biosphere.write(biosphere_data)

        method = Method(("test", "LCIA", "method"))
        method.register("points", "w00t", 2)
        method.write([
            (("biosphere", 1), 1.0, "GLO"),
            (("biosphere", 2), 1.0, "GLO")
        ])

        answer = {
            ('some bad stuff', 'kilogram'): [1.0, 1.0]
        }
        self.assertEquals(group_by_emissions(method), answer)

    def test_grouping_separate_name(self):
        biosphere_data = {
            ("biosphere", 1): {
                'categories': ['this'],
                'exchanges': [],
                'name': 'some bad stuff',
                'type': 'emission',
                'unit': 'kg'
                },
            ("biosphere", 2): {
                'categories': ['that'],
                'exchanges': [],
                'name': 'some more bad stuff',
                'type': 'emission',
                'unit': 'kg'
                },
        }

        biosphere = Database("biosphere")
        biosphere.register("Tests", [], len(biosphere_data))
        biosphere.write(biosphere_data)

        method = Method(("test", "LCIA", "method"))
        method.register("points", "w00t", 2)
        method.write([
            (("biosphere", 1), 1.0, "GLO"),
            (("biosphere", 2), 2.0, "GLO")
        ])

        answer = {
            ('some bad stuff', 'kilogram'): [1.0],
            ('some more bad stuff', 'kilogram'): [2.0]
        }
        self.assertEquals(group_by_emissions(method), answer)

    def test_grouping_separate_unit(self):
        biosphere_data = {
            ("biosphere", 1): {
                'categories': ['this'],
                'exchanges': [],
                'name': 'some bad stuff',
                'type': 'emission',
                'unit': 'kg'
                },
            ("biosphere", 2): {
                'categories': ['that'],
                'exchanges': [],
                'name': 'some bad stuff',
                'type': 'emission',
                'unit': 'tonne'
                },
        }

        biosphere = Database("biosphere")
        biosphere.register("Tests", [], len(biosphere_data))
        biosphere.write(biosphere_data)

        method = Method(("test", "LCIA", "method"))
        method.register("points", "w00t", 2)
        method.write([
            (("biosphere", 1), 1.0, "GLO"),
            (("biosphere", 2), 2.0, "GLO")
        ])

        answer = {
            ('some bad stuff', 'kilogram'): [1.0],
            ('some bad stuff', 'tonne'): [2.0]
        }
        self.assertEquals(group_by_emissions(method), answer)
