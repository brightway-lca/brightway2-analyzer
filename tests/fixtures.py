lci_fixture = {
    ("a", "flow"): {"name": "flow", "type": "biosphere"},
    ("a", "1"): {
        "name": "process 1",
        "exchanges": [{"input": ("a", "flow"), "type": "biosphere", "amount": 2}],
    },
    ("a", "2"): {
        "name": "process 2",
        "exchanges": [
            {"input": ("a", "flow"), "type": "biosphere", "amount": 1},
            {"input": ("a", "1"), "type": "technosphere", "amount": 1},
        ],
    },
}

recursive_fixture = {
    ("a", "flow"): {"name": "flow", "type": "biosphere"},
    ("a", "1"): {
        "name": "process 1",
        "unit": "b",
        "location": "c",
        "exchanges": [
            {"input": ("a", "flow"), "type": "biosphere", "amount": 2},
            {"input": ("a", "2"), "type": "technosphere", "amount": 0.8},

            ],
    },
    ("a", "2"): {
        "name": "process 2",
        "unit": "b",
        "location": "c",
        "exchanges": [
            {"input": ("a", "flow"), "type": "biosphere", "amount": 0.5},
            {"input": ("a", "3"), "type": "technosphere", "amount": 0.6},
        ],
    },
    ("a", "3"): {
        "name": "process 3",
        "unit": "b",
        "location": "c",
        "exchanges": [
            {"input": ("a", "4"), "type": "technosphere", "amount": 10},
            {"input": ("a", "5"), "type": "technosphere", "amount": 0.1},
        ],
    },
    ("a", "4"): {
        "name": "process 4",
        "unit": "b",
        "location": "c",
        "exchanges": [
            {"input": ("a", "flow"), "type": "biosphere", "amount": 0.005},
        ],
    },
    ("a", "5"): {
        "name": "process 5",
        "unit": "b",
        "location": "c",
        "exchanges": [
            {"input": ("a", "flow"), "type": "biosphere", "amount": 50},
            {"input": ("a", "1"), "type": "technosphere", "amount": 0.05},
        ],
    },
}


comparisons_fixture = {
    ("c", "flow"): {"name": "flow", "type": "biosphere"},
    ("c", "1"): {
        "name": "process 1",
        "exchanges": [{"input": ("c", "flow"), "type": "biosphere", "amount": 2}],
    },
    ("c", "2"): {
        "name": "process 2",
        "exchanges": [
            {"input": ("a", "flow"), "type": "biosphere", "amount": 1},
            {"input": ("a", "1"), "type": "technosphere", "amount": 1},
        ],
    },
}

method_fixture = [(("a", "flow"), 1), (("c", "flow"), 1)]
