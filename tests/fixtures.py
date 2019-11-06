# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division
from eight import *

lci_fixture = {
    ("a", "flow"): {
        'name': 'flow',
        'type': 'biosphere'
    },
    ("a", "1"): {
        'name': 'process 1',
        'exchanges': [{
            'input': ("a", "flow"),
            'type': 'biosphere',
            'amount': 2
        }]
    },
    ("a", "2"): {
        'name': 'process 2',
        'exchanges': [{
            'input': ("a", "flow"),
            'type': 'biosphere',
            'amount': 1
        }, {
            'input': ("a", "1"),
            'type': 'technosphere',
            'amount': 1
        }]
    }
}

method_fixture = [(("a", "flow"), 1)]
