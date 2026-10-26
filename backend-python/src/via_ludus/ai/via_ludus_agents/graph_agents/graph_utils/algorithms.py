from itertools import combinations

import networkx as nx
from networkx.algorithms.connectivity import minimum_st_node_cut

from .graph import Endpoint


def minimum_endpoint_cut(graph):
	return minimum_st_node_cut(
		graph,
		Endpoint.SOURCE,
		Endpoint.TARGET,
	)


def all_minimum_endpoint_cuts(graph):
	k = nx.node_connectivity(
		graph,
		Endpoint.SOURCE,
		Endpoint.TARGET,
	)

	nodes = set(graph) - {
		Endpoint.SOURCE,
		Endpoint.TARGET,
	}

	for cut in combinations(nodes, k):
		cut = set(cut)

		reduced_graph = graph.copy()
		reduced_graph.remove_nodes_from(cut)

		if not nx.has_path(
			reduced_graph,
			Endpoint.SOURCE,
			Endpoint.TARGET,
		):
			yield cut

