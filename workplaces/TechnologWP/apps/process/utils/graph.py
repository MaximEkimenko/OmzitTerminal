import logging

import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd


def draw_graph(data: pd.DataFrame):
    try:
        G = nx.DiGraph(directed=True)
        nodes = data['id'].to_list()
        G.add_nodes_from(nodes)
        for node in nodes:
            next_nodes = data[data['id'] == node].iloc[0, 21]
            for next_node in next_nodes:
                G.add_edge(node, next_node)
        pos = nx.planar_layout(G)
        options = {
            'node_color': 'yellow',
            'node_size': 200,
            'width': 1,
            'arrowstyle': '-|>',
            'arrowsize': 18,
            'font_size': 10,
        }
        nx.draw(G, pos, with_labels=True, **options)
        plt.show()
    except Exception as ex:
        logging.exception(ex)
