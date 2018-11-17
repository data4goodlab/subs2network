import glob
import os
from networkx.readwrite import json_graph
import json
import networkx as nx
import pandas as pd
from subs2graph.utils import add_prefix_to_dict_keys


def average_graph_weight(g):
    stats =  pd.Series(list(nx.get_edge_attributes(g, "weight").values())).describe()
    del stats["count"]
    add_prefix_to_dict_keys(stats.to_dict(), "weight")


def average_graph_degree(g):
    stats = pd.Series([d for n, d in nx.degree(g, g.nodes())]).describe()
    del stats["count"]
    add_prefix_to_dict_keys(stats.to_dict(), "degree")


def average_clustering(g):
    return {"average_clustering": nx.average_clustering(g)}


p = "../temp/top1000/movies/"
for movie in os.listdir(p):
    path = os.path.join(p, movie)
    os.path.join(path, f"{movie}.json")
    g_pth = glob.glob(os.path.join(path, f"json/*({'[0-9]'*4}).json"))
    g_data = pd.DataFrame()
    if g_pth:
        with open(g_pth[0]) as f:
            g = json_graph.node_link_graph(json.load(f))
            average_graph_degree(g)
            average_graph_weight(g)
            print(average_clustering(g))

            # average_clustering
            # max_clique
            # graph_number_of_cliques
            # graph_clique_number
            # average_clustering
            # max avg, stdv, min eigenvector
            # closeness_centrality

    # if glob.glob(os.path.join(path, f"subtitles/{movie}*roles.pkl")):
    #     try:
    #         os.remove(glob.glob(os.path.join(path, f"subtitles/{movie}*roles.pkl"))[0])
    #         os.remove(os.path.join(path, f"{movie}.json"))
    #     except FileNotFoundError:
    #         pass
