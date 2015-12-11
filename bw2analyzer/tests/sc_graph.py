# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division
from eight import *

from ..sc_graph import GTManipulator
from bw2data import (
    Database,
    databases,
    geomapping,
    mapping,
    methods,
    projects,
)
from bw2data.tests import BW2DataTest
import unittest
import copy


class UnrollGraphTestCase(unittest.TestCase):
    def test_simple_chain(self):
        nodes = {
            -1: {'amount': 1, 'cum': 1, 'ind': 0},
            10: {'amount': 1, 'cum': 1, 'ind': 1},
            11: {'amount': 0.5, 'cum': 0.5, 'ind': 1},
            12: {'amount': 0.1, 'cum': 0.1, 'ind': 1},
        }
        edges = [
            {'to': -1, 'from': 10, 'amount': 1, 'exc_amount': 1, 'impact': 1},
            {'to': 10, 'from': 11, 'amount': 0.5, 'exc_amount': 0.5, 'impact': 0.5},
            {'to': 11, 'from': 12, 'amount': 0.1, 'exc_amount': 0.2, 'impact': 0.1}
        ]
        nodes, edges, count = GTManipulator.unroll_graph(nodes, edges, 1)
        ref_nodes = {
            -1: {'ind': 0, 'amount': 1, 'cum': 1},
            0: {'ind': 1, 'amount': 1, 'cum': 1, 'row': 10},
            1: {'ind': 1, 'amount': 0.5, 'cum': 0.5, 'row': 11},
            2: {'ind': 1, 'amount': 0.1, 'cum': 0.10000000000000002, 'row': 12}
        }
        ref_edges = [
            {'impact': 1, 'to': -1, 'amount': 1, 'exc_amount': 1, 'from': 0},
            {'impact': 0.5, 'to': 0, 'amount': 0.5, 'exc_amount': 0.5, 'from': 1},
            {'impact': 0.10000000000000002, 'to': 1, 'amount': 0.1, 'exc_amount': 0.2, 'from': 2}
        ]
        self.assertEqual(count, 3)
        self.assertEqual(nodes, ref_nodes)
        self.assertEqual(edges, ref_edges)

    def test_multiple_inputs(self):
        nodes = {
            -1: {'amount': 1, 'cum': 1, 'ind': 0},
            10: {'amount': 1, 'cum': 1, 'ind': 1},
            11: {'amount': 0.5, 'cum': 0.5, 'ind': 1},
            12: {'amount': 0.5, 'cum': 0.5, 'ind': 1},
        }
        edges = [
            {'to': -1, 'from': 10, 'amount': 1, 'exc_amount': 1, 'impact': 1},
            {'to': 10, 'from': 11, 'amount': 0.5, 'exc_amount': 0.5, 'impact': 0.5},
            {'to': 10, 'from': 12, 'amount': 0.5, 'exc_amount': 0.5, 'impact': 0.5}
        ]
        nodes, edges, count = GTManipulator.unroll_graph(nodes, edges, 1)
        ref_nodes = {
            -1: {'ind': 0, 'amount': 1, 'cum': 1},
            0: {'ind': 1, 'amount': 1, 'cum': 1, 'row': 10},
            1: {'ind': 1, 'amount': 0.5, 'cum': 0.5, 'row': 11},
            2: {'ind': 1, 'amount': 0.5, 'cum': 0.5, 'row': 12}
        }
        ref_edges = [
            {'impact': 1, 'to': -1, 'amount': 1, 'exc_amount': 1, 'from': 0},
            {'impact': 0.5, 'to': 0, 'amount': 0.5, 'exc_amount': 0.5, 'from': 1},
            {'impact': 0.5, 'to': 0, 'amount': 0.5, 'exc_amount': 0.5, 'from': 2}
        ]
        self.assertEqual(count, 3)
        self.assertEqual(nodes, ref_nodes)
        self.assertEqual(edges, ref_edges)

    def test_pruning(self):
        nodes = {
            -1: {'amount': 1, 'cum': 1, 'ind': 0},
            10: {'amount': 1, 'cum': 1, 'ind': 1},
            11: {'amount': 0.5, 'cum': 0.5, 'ind': 1},
            12: {'amount': 0.001, 'cum': 0.001, 'ind': 1},
        }
        edges = [
            {'to': -1, 'from': 10, 'amount': 1, 'exc_amount': 1, 'impact': 1},
            {'to': 10, 'from': 11, 'amount': 0.5, 'exc_amount': 0.5, 'impact': 0.5},
            {'to': 10, 'from': 12, 'amount': 0.001, 'exc_amount': 0.002, 'impact': 0.001}
        ]
        nodes, edges, count = GTManipulator.unroll_graph(nodes, edges, 1)
        ref_nodes = {
            -1: {'ind': 0, 'amount': 1, 'cum': 1},
            0: {'ind': 1, 'amount': 1, 'cum': 1, 'row': 10},
            1: {'ind': 1, 'amount': 0.5, 'cum': 0.5, 'row': 11},
        }
        ref_edges = [
            {'impact': 1, 'to': -1, 'amount': 1, 'exc_amount': 1, 'from': 0},
            {'impact': 0.5, 'to': 0, 'amount': 0.5, 'exc_amount': 0.5, 'from': 1},
        ]
        self.assertEqual(count, 3)
        self.assertEqual(nodes, ref_nodes)
        self.assertEqual(edges, ref_edges)

    def test_unroll_circular(self):
        nodes = {
            -1: {'amount': 1, 'cum': 1, 'ind': 0},
            10: {'amount': 1, 'cum': 1, 'ind': 1},
            11: {'amount': 1, 'cum': 1, 'ind': 1}
        }
        edges = [
            {'to': -1, 'from': 10, 'amount': 1, 'exc_amount': 1, 'impact': 1},
            {'to': 10, 'from': 11, 'amount': 1, 'exc_amount': 0.8, 'impact': 1},
            {'to': 11, 'from': 10, 'amount': 1, 'exc_amount': 0.8, 'impact': 1}
        ]
        nodes, edges, count = GTManipulator.unroll_graph(nodes, edges, 1, cutoff=0.4)
        ref_nodes = {
            -1: {'ind': 0, 'amount': 1, 'cum': 1},
            0: {'ind': 1, 'amount': 1, 'cum': 1, 'row': 10},
            1: {'ind': 1, 'amount': 0.8, 'cum': 0.8, 'row': 11},
            2: {'ind': 1, 'amount': 0.6400000000000001, 'cum': 0.6400000000000001, 'row': 10},
            3: {'ind': 1, 'amount': 0.5120000000000001, 'cum': 0.5120000000000001, 'row': 11},
            4: {'ind': 1, 'amount': 0.40960000000000013, 'cum': 0.40960000000000013, 'row': 10}
        }
        ref_edges = [
            {'impact': 1, 'to': -1, 'amount': 1, 'exc_amount': 1, 'from': 0},
            {'impact': 0.8, 'to': 0, 'amount': 0.8, 'exc_amount': 0.8, 'from': 1},
            {'impact': 0.6400000000000001, 'to': 1, 'amount': 0.6400000000000001, 'exc_amount': 0.8, 'from': 2},
            {'impact': 0.5120000000000001, 'to': 2, 'amount': 0.5120000000000001, 'exc_amount': 0.8, 'from': 3},
            {'impact': 0.40960000000000013, 'to': 3, 'amount': 0.40960000000000013, 'exc_amount': 0.8, 'from': 4}
        ]
        self.assertEqual(count, 6)
        self.assertEqual(nodes, ref_nodes)
        self.assertEqual(edges, ref_edges)

    def test_max_links(self):
        nodes = {
            -1: {'amount': 1, 'cum': 1, 'ind': 0},
            10: {'amount': 1, 'cum': 1, 'ind': 1},
            11: {'amount': 1, 'cum': 1, 'ind': 1}
        }
        edges = [
            {'to': -1, 'from': 10, 'amount': 1, 'exc_amount': 1, 'impact': 1},
            {'to': 10, 'from': 11, 'amount': 1, 'exc_amount': 0.999, 'impact': 1},
            {'to': 11, 'from': 10, 'amount': 1, 'exc_amount': 0.999, 'impact': 1}
        ]
        nodes, edges, count = GTManipulator.unroll_graph(nodes, edges, 1, max_links=100)
        self.assertEqual(count, 100)

    def test_diamond(self):
        nodes = {
            -1: {'amount': 1, 'cum': 1, 'ind': 0},
            10: {'amount': 1, 'cum': 1, 'ind': 0},
            11: {'amount': 1, 'cum': 0.2, 'ind': 0},
            12: {'amount': 1, 'cum': 0.8, 'ind': 0},
            13: {'amount': 1, 'cum': 1, 'ind': 1},
        }
        edges = [
            {'to': -1, 'from': 10, 'amount': 1, 'exc_amount': 1, 'impact': 1},
            {'to': 10, 'from': 11, 'amount': 1, 'exc_amount': 1, 'impact': 0.2},
            {'to': 10, 'from': 12, 'amount': 1, 'exc_amount': 1, 'impact': 0.8},
            {'to': 11, 'from': 13, 'amount': 0.2, 'exc_amount': 0.2, 'impact': 0.2},
            {'to': 12, 'from': 13, 'amount': 0.8, 'exc_amount': 0.8, 'impact': 0.8}
        ]
        nodes, edges, count = GTManipulator.unroll_graph(nodes, edges, 1)
        ref_nodes = {
            -1: {'ind': 0, 'amount': 1, 'cum': 1},
            0: {'ind': 0, 'amount': 1, 'cum': 1, 'row': 10},
            1: {'ind': 0, 'amount': 1, 'cum': 0.2, 'row': 11},
            2: {'ind': 0, 'amount': 1, 'cum': 0.8, 'row': 12},
            3: {'ind': 1, 'amount': 0.8, 'cum': 0.8, 'row': 13},
            4: {'ind': 1, 'amount': 0.2, 'cum': 0.2, 'row': 13}
        }
        ref_edges = [
            {'impact': 1, 'to': -1, 'amount': 1, 'exc_amount': 1, 'from': 0},
            {'impact': 0.2, 'to': 0, 'amount': 1, 'exc_amount': 1, 'from': 1},
            {'impact': 0.8, 'to': 0, 'amount': 1, 'exc_amount': 1, 'from': 2},
            {'impact': 0.8, 'to': 2, 'amount': 0.8, 'exc_amount': 0.8, 'from': 3},
            {'impact': 0.2, 'to': 1, 'amount': 0.2, 'exc_amount': 0.2, 'from': 4}
        ]
        self.assertEqual(count, 5)
        self.assertEqual(nodes, ref_nodes)
        self.assertEqual(edges, ref_edges)

    def test_circle_with_branches(self):
        pass


class MetadataTestCase(BW2DataTest):
    class LCAMock(object):
        def reverse_dict(self):
            return (
                {1: ("A", "a"), 2: ("A", "b"), 3: ("A", "c")},
                {1: ("A", "a"), 2: ("A", "b"), 3: ("A", "c")},
                {}
            )

    def extra_setup(self):
        data = {
            ("A", "a"): {
                "name": "a",
                "categories": [],
                "unit": "kilogram"
                },
            ("A", "b"): {
                "name": "b",
                "categories": [],
                "unit": "kilogram"
                },
            ("A", "c"): {
                "name": "c",
                "categories": [],
                "unit": "kilogram"
                }
        }
        d = Database("A")
        d.register(name="Tests", depends=[])
        d.write(data)
        self.assertEqual(len(databases), 1)

    def test_setup_clean(self):
        self.assertEqual(list(databases), ["A"])
        self.assertEqual(list(methods), [])
        self.assertEqual(len(mapping), 3)
        self.assertEqual(len(geomapping), 1)  # GLO
        self.assertTrue("GLO" in geomapping)
        self.assertEqual(len(projects), 1)  # Default project
        self.assertTrue("default" in projects)

    def test_without_row(self):
        nodes = {1: {}, 3: {}}
        old_nodes = copy.deepcopy(nodes)
        new_nodes = GTManipulator.add_metadata(nodes, self.LCAMock())
        self.assertEqual(old_nodes, nodes)
        self.assertEqual(
            new_nodes,
            {
                1: {'categories': [], 'unit': 'kilogram', 'key': ('A', 'a'), 'name': 'a'},
                3: {'categories': [], 'unit': 'kilogram', 'key': ('A', 'c'), 'name': 'c'}
            })

    def test_with_functional_unit(self):
        nodes = {-1: {}, 1: {}, 3: {}}
        old_nodes = copy.deepcopy(nodes)
        new_nodes = GTManipulator.add_metadata(nodes, self.LCAMock())
        self.assertEqual(old_nodes, nodes)
        self.assertEqual(
            new_nodes,
            {
                -1: {'name': "Functional unit", 'unit': "unit", 'categories': ["Functional unit"]},
                1: {'categories': [], 'unit': 'kilogram', 'key': ('A', 'a'), 'name': 'a'},
                3: {'categories': [], 'unit': 'kilogram', 'key': ('A', 'c'), 'name': 'c'}
            })

    def test_with_row(self):
        nodes = {1000: {'row': 1}, 3000: {'row': 3}}
        old_nodes = copy.deepcopy(nodes)
        new_nodes = GTManipulator.add_metadata(nodes, self.LCAMock())
        self.assertEqual(old_nodes, nodes)
        self.assertEqual(
            new_nodes,
            {
                1000: {'categories': [], 'unit': 'kilogram', 'key': ('A', 'a'), 'name': 'a', 'row': 1},
                3000: {'categories': [], 'unit': 'kilogram', 'key': ('A', 'c'), 'name': 'c', 'row': 3}
            })


class SimplifyTestCase(unittest.TestCase):
    def test_nodes_dont_change(self):
        nodes = {
            1: {'amount': 1, 'ind': 1},
            2: {'amount': 2, 'ind': 0.0001},
            3: {'amount': 4, 'ind': 1},
        }
        old_nodes = copy.deepcopy(nodes)
        edges = [
            {'to': 1, 'from': 2, 'amount': 3, 'exc_amount': 2, 'impact': 4},
            {'to': 2, 'from': 3, 'amount': 3, 'exc_amount': 2, 'impact': 5},
        ]
        GTManipulator.simplify(nodes, edges, 2, 0.1)
        self.assertEqual(old_nodes, nodes)

    def test_linear(self):
        """Test supply chain graph like this:

            o
            |    o
            x => |
            |    o
            o

        """
        nodes = {
            1: {'amount': 1, 'ind': 1},
            2: {'amount': 2, 'ind': 0.0001},
            3: {'amount': 4, 'ind': 1},
        }
        edges = [
            {'to': 1, 'from': 2, 'amount': 3, 'exc_amount': 2, 'impact': 4},
            {'to': 2, 'from': 3, 'amount': 3, 'exc_amount': 2, 'impact': 5},
        ]
        new_nodes, new_edges = GTManipulator.simplify(nodes, edges, 2, 0.1)
        self.assertEqual(
            new_nodes,
            {key: value for key, value in nodes.items() if key in (1, 3)}
        )
        self.assertEqual(
            list(new_edges),
            [{'to': 1, 'from': 3, 'amount': 3, 'exc_amount': 4, 'impact': 5}]
        )

    def test_y(self):
        """Test supply chain graph like this:

            o   o     o   o
             \ /       \ /
              x   =>    o
              |
              o

        """
        nodes = {
            1: {'amount': 1, 'ind': 1},
            2: {'amount': 4, 'ind': 2},
            3: {'amount': 1, 'ind': 0.001},
            4: {'amount': 2, 'ind': 1.5},
        }
        edges = [
            {'to': 1, 'from': 3, 'amount': 0.2, 'exc_amount': 0.2, 'impact': 1},
            {'to': 2, 'from': 3, 'amount': 0.8, 'exc_amount': 0.2, 'impact': 2},
            {'to': 3, 'from': 4, 'amount': 2, 'exc_amount': 2, 'impact': 3},
        ]
        new_nodes, new_edges = GTManipulator.simplify(nodes, edges, 9, 0.1)
        expected_nodes = {key: value for key, value in nodes.items()
            if key in (1, 2, 4)}
        self.assertEqual(expected_nodes, new_nodes)
        expected_edges = [
            {'to': 2, 'from': 4, 'amount': 1.6, 'exc_amount': 0.4, 'impact': 2},
            {'to': 1, 'from': 4, 'amount': 0.4, 'exc_amount': 0.4, 'impact': 1},
        ]
        self.assertEqual(expected_edges, list(new_edges))

    def test_no_self_edge(self):
        """Test that collapsed edges from a -> a are deleted."""
        nodes = {
            1: {'amount': 1, 'ind': 1},
            2: {'amount': 4, 'ind': 2},
            3: {'amount': 1, 'ind': 0.001},
            4: {'amount': 2, 'ind': 1.5},
        }
        edges = [
            {'to': 1, 'from': 3, 'amount': 0.2, 'exc_amount': 0.2, 'impact': 1},
            {'to': 2, 'from': 3, 'amount': 0.8, 'exc_amount': 0.2, 'impact': 2},
            {'to': 3, 'from': 4, 'amount': 2, 'exc_amount': 2, 'impact': 3},
        ]
        new_nodes, new_edges = GTManipulator.simplify(nodes, edges, 9, 0.1)
        expected_nodes = {key: value for key, value in nodes.items()
            if key in (1, 2, 4)}
        self.assertEqual(expected_nodes, new_nodes)
        expected_edges = [
            {'to': 2, 'from': 4, 'amount': 1.6, 'exc_amount': 0.4, 'impact': 2},
            {'to': 1, 'from': 4, 'amount': 0.4, 'exc_amount': 0.4, 'impact': 1},
        ]
        self.assertEqual(expected_edges, list(new_edges))

    def test_diamond(self):
        """Test supply chain graph like this:

              o
             / \      o
            x   x =>  |
             \ /      o
              o

        """
        nodes = {
            1: {'amount': 1, 'ind': 1},
            2: {'amount': 2, 'ind': 0},
            3: {'amount': 3, 'ind': 0},
            4: {'amount': 5, 'ind': 1},
        }
        edges = [
            {'to': 1, 'from': 2, 'amount': 2, 'exc_amount': 1, 'impact': 2},
            {'to': 1, 'from': 3, 'amount': 3, 'exc_amount': 1, 'impact': 3},
            {'to': 2, 'from': 4, 'amount': 2, 'exc_amount': 1, 'impact': 2},
            {'to': 3, 'from': 4, 'amount': 3, 'exc_amount': 1, 'impact': 3},
        ]
        new_nodes, new_edges = GTManipulator.simplify(nodes, edges, 5, 0.1)
        expected_nodes = {key: value for key, value in nodes.items()
            if key in (1, 4)}
        self.assertEqual(expected_nodes, new_nodes)
        expected_edges = [
            {'to': 1, 'from': 4, 'amount': 5, 'exc_amount': 2, 'impact': 5}
        ]
        self.assertEqual(expected_edges, list(new_edges))

    def test_x(self):
        """Test supply chain graph like this:

            o   o
             \ /      o  o
              x   =>  |\/|
             / \      |/\|
            o   o     o  o
        """
        nodes = {
            1: {'amount': 1, 'ind': 1},
            2: {'amount': 1, 'ind': 1},
            3: {'amount': 3, 'ind': 0},
            4: {'amount': 9, 'ind': 3},
            5: {'amount': 12, 'ind': 2},
        }
        edges = [
            {'to': 1, 'from': 3, 'amount': 1, 'exc_amount': 1, 'impact': 17},
            {'to': 2, 'from': 3, 'amount': 2, 'exc_amount': 2, 'impact': 34},
            {'to': 3, 'from': 4, 'amount': 9, 'exc_amount': 3, 'impact': 27},
            {'to': 3, 'from': 5, 'amount': 12, 'exc_amount': 4, 'impact': 24},
        ]
        new_nodes, new_edges = GTManipulator.simplify(nodes, edges, 53, 0.01)
        expected_nodes = {key: value for key, value in nodes.items()
            if key in (1, 2, 4, 5)}
        self.assertEqual(expected_nodes, new_nodes)
        expected_edges = [
            {'to': 1, 'from': 4, 'amount': 3, 'exc_amount': 3, 'impact': 9},
            {'to': 1, 'from': 5, 'amount': 4, 'exc_amount': 4, 'impact': 8},
            {'to': 2, 'from': 5, 'amount': 8, 'exc_amount': 8, 'impact': 16},
            {'to': 2, 'from': 4, 'amount': 6, 'exc_amount': 6, 'impact': 18},
        ]
        self.assertEqual(
            sorted(expected_edges, key = lambda x: (x['to'], x['from'])),
            sorted(new_edges, key = lambda x: (x['to'], x['from']))
        )
