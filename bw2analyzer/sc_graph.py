import copy
import itertools
from heapq import heappop, heappush

from bw2data import config, get_activity


def tupify(o):
    """Transform edge from dict to tuples. Multiply impact by -1 because sort by min, not max"""
    return (-1 * o["impact"], o["from"], o["to"], o["amount"], o["exc_amount"])


class GTManipulator:
    """Manipulate ``GraphTraversal`` results."""

    @staticmethod
    def unroll_graph(nodes, edges, score, cutoff=0.005, max_links=2500):
        """Unroll a ``GraphTraversal`` result, allowing the same activity to appear in the graph multiple times."""
        input_nodes, input_edges = copy.deepcopy(nodes), copy.deepcopy(edges)
        counter = itertools.count()
        edges_dict = {}
        heap, edges, links, cutoff_score = [], [], 0, cutoff * score
        nodes = {-1: copy.deepcopy(input_nodes[-1])}

        for edge in input_edges:
            edges_dict.setdefault(edge["to"], []).append(edge)

        for edge in edges_dict[-1]:
            heappush(heap, tupify(edge))
            links += 1

        while heap and links < max_links:
            score, from_, to, cum_amount, exc_amount = heappop(heap)

            if (-1 * score) < cutoff_score:
                continue

            # ``from_`` is old-style indexing, ``to`` is new-style indexing
            from_node = input_nodes[from_]
            to_node = nodes[to]
            new_amount = exc_amount * to_node["amount"]

            node_id = next(counter)
            # Only node that doesn't have a ``row`` attribute is the
            # functional unit, which by definition has no outgoing links
            nodes[node_id] = {
                "amount": new_amount,
                "row": from_,
                "cum": from_node["cum"] * new_amount / from_node["amount"],
                "ind": from_node["ind"],
            }
            edges.append(
                {
                    "to": to,
                    "from": node_id,
                    "amount": new_amount,
                    "exc_amount": exc_amount,
                    "impact": nodes[node_id]["cum"],
                }
            )

            frommer = lambda x: x["from"]
            # Include all edges for now; ignore minor ones when popping heap
            for edge in sorted(edges_dict.get(from_, []), key=frommer):
                from_edge_node = input_nodes[from_]
                heappush(
                    heap,
                    tupify(
                        {
                            "amount": new_amount * edge["exc_amount"],
                            "from": edge["from"],
                            "to": node_id,
                            "exc_amount": edge["exc_amount"],
                            "impact": from_edge_node["cum"]
                            / from_edge_node["amount"]
                            * new_amount
                            * edge["exc_amount"],
                        }
                    ),
                )
                links += 1
        return nodes, edges, links

    @staticmethod
    def add_metadata(nodes, lca):
        """Add metadata to nodes, like name, unit, and category."""
        new_nodes = {}
        for key, value in nodes.items():
            new_value = copy.deepcopy(value)
            if key == -1:
                new_value.update(
                    {
                        "name": "Functional unit",
                        "unit": "unit",
                        "categories": ["Functional unit"],
                    }
                )
            else:
                if "row" in value:
                    index = value["row"]
                else:
                    index = key
                code = lca.dicts.activity.reversed[index]
                ds = get_activity(code)
                new_value.update(
                    {
                        "name": ds.get("name", "Unknown"),
                        "categories": ds.get("categories", []),
                        "unit": ds.get("unit", "Unknown"),
                        "key": code,
                    }
                )
            new_nodes[key] = new_value
        return new_nodes

    @staticmethod
    def d3_force_directed(nodes, edges, score):
        """Reformat to D3 style, which is a list of nodes, and edge ids are node list indices."""
        # Sort node ids by highest cumulative score first
        node_ids = [x[1] for x in sorted([(v["cum"], k) for k, v in nodes.items()])]
        new_nodes = [nodes[i] for i in node_ids]
        lookup = dict([(key, index) for index, key in enumerate(node_ids)])
        new_edges = [
            {
                "source": lookup[e["to"]],
                "target": lookup[e["from"]],
                "amount": e["impact"],
            }
            for e in edges
        ]
        return {"edges": new_edges, "nodes": new_nodes, "total": score}

    @staticmethod
    def simplify(nodes, edges, score, limit=0.005):
        """Simplify supply chain to include only nodes which individually contribute ``limit * score``.

        Only removes and combines edges; doesn't check to make sure amounts add up correctly."""
        if isinstance(limit, int) and limit > 1:
            nodes_to_delete = sorted(
                [(value["amount"] * value["ind"], key) for key, value in nodes.items()],
                reverse=True,
            )[limit:]
        else:
            nodes_to_delete = [
                key
                for key, value in nodes.items()
                if key != -1 and (value["amount"] * value["ind"]) < (score * limit)
            ]
        edges_dict = {(edge["to"], edge["from"]): edge for edge in copy.deepcopy(edges)}
        for node in nodes_to_delete:
            p_edges = [key for key in edges_dict if key[1] == node]
            c_edges = [key for key in edges_dict if key[0] == node]
            total_amount = sum([edges_dict[k]["amount"] for k in p_edges])
            total_impact = sum([edges_dict[k]["impact"] for k in p_edges])
            for p_key, c_key in itertools.product(p_edges, c_edges):
                key = (p_key[0], c_key[1])
                if p_key[0] == c_key[1]:
                    continue
                p_edge = edges_dict[p_key]
                c_edge = edges_dict[c_key]
                e_amount = c_edge["amount"] * p_edge["amount"] / total_amount
                e_impact = c_edge["impact"] * p_edge["impact"] / total_impact
                e_eamount = p_edge["exc_amount"] * c_edge["exc_amount"]
                if key in edges_dict:
                    edges_dict[key]["amount"] += e_amount
                    edges_dict[key]["exc_amount"] += e_eamount
                    edges_dict[key]["impact"] += e_impact
                else:
                    edges_dict[key] = {
                        "to": p_edge["to"],
                        "from": c_edge["from"],
                        "amount": e_amount,
                        "exc_amount": e_eamount,
                        "impact": e_impact,
                    }
            # Remove obsolete edges
            for key in p_edges:
                del edges_dict[key]
            for key in c_edges:
                del edges_dict[key]
        nodes = {
            key: value
            for key, value in nodes.items()
            if key not in set(nodes_to_delete)
        }
        return nodes, edges_dict.values()

    @staticmethod
    def simplify_naive(nodes, edges, score, limit=0.0025):
        """Naive simplification which simplifies removes links below an LCA score cutoff. Orphan nodes are also deleted."""
        edges = [e for e in edges if e["impact"] >= (score * limit)]
        good_nodes = set([e["from"] for e in edges]).union(
            set([e["to"] for e in edges])
        )
        nodes = dict([(k, v) for k, v in nodes.items() if k in good_nodes])
        return nodes, edges

    @staticmethod
    def d3_treemap(nodes, edges, lca, add_biosphere=False):
        """Add node data by traversing the graph; assign different metadata to leaf nodes."""
        ra, rp, rb = lca.reverse_dict()

        child_nodes = lambda node, edges: [e["from"] for e in edges if e["to"] == node]

        counter = itertools.count(1)

        def format_node(node_key, node_data, ra):
            if node_key == -1:
                return {
                    "name": "Functional unit",
                    "unit": "unit",
                    "location": config.global_location,
                    "categories": "",
                    "id": next(counter),
                    "amount": 1.0,
                }

            if "row" in node_data:
                node_key = node_data["row"]
            key = ra[node_key]
            ds = get_activity(key)
            return {
                "name": ds.get("name", "Unknown"),
                "unit": ds.get("unit", "Unknown"),
                "location": ds.get("location", "Unknown"),
                "categories": ", ".join(ds.get("categories", [])),
                "id": next(counter),
                "amount": node_data["amount"],
            }

        def format_child_node(node_key, node_data, ra, add_biosphere):
            ds = format_node(node_key, node_data, ra)
            ds["size"] = node_data["cum"]
            ds["variance"] = 0.5
            return ds

        def process_node(node):
            cn = child_nodes(node, edges)
            if cn:
                ds = format_node(node, nodes[node], ra)
                ds["children"] = [process_node(o) for o in cn]
                return ds
            else:
                return format_child_node(node, nodes[node], ra, False)

        return process_node(-1)
