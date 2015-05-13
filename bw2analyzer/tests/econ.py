# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division
from eight import *

from ..econ import concentration_ratio, gini_coefficient, herfindahl_index, \
    theil_index
import numpy as np
import unittest


class EconometricsTestCase(unittest.TestCase):
    def test_concentration_ratio(self):
        x = (0.2, 0.2, 0.2, 0.2, 0.1, 0.1)
        self.assertEqual(concentration_ratio(x), 0.8)
        self.assertTrue(isinstance(concentration_ratio(x), float))

    def test_concentration_ratio_normalization(self):
        x = np.array((0.2, 0.2, 0.2, 0.2, 0.1, 0.1)) * 2
        self.assertEqual(concentration_ratio(x), 0.8)

    def test_concentration_ratio_number(self):
        x = np.array((0.2, 0.2, 0.2, 0.2, 0.1, 0.1))
        self.assertEqual(concentration_ratio(x, 2), 0.4)

    def test_herfindahl(self):
        x = np.array((1., 1., 1.), dtype=float)
        # Correct answer is 3 * (1/3) ^ 2 = 1/3
        self.assertEqual(herfindahl_index(x, False), 1 / 3)
        # Normalized it is zero (all values are the same)
        self.assertEqual(herfindahl_index(x), 0)
        x = np.array((0.8, 0.1, 0.1))
        self.assertAlmostEqual(herfindahl_index(x, False), 0.64 + 0.01 + 0.01)
        self.assertTrue(isinstance(herfindahl_index(x, False), float))

    def test_gini(self):
        x = np.array((0.2, 0.3, 0.4, 0.5, 0.6))
        # From wikipedia page
        self.assertAlmostEqual(gini_coefficient(x), 0.2)

    def test_theil(self):
        # Include negative and zero values to test filtering
        x = np.array((0., -2., 2., 6., 20.))
        average = 30 / 4
        y = np.array((2., 2., 6., 20.))
        answer = 1 / 4 * ((y / average) * np.log(y / average)).sum()
        self.assertAlmostEqual(float(answer), theil_index(x))
