import glob
import os
from networkx.readwrite import json_graph
import json
import networkx as nx
import pandas as pd
from subs2graph.utils import add_prefix_to_dict_keys


def average_graph_weight(g):
    stats = pd.Series(list(nx.get_edge_attributes(g, "weight").values())).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "weight")


def average_graph_degree(g):
    stats = pd.Series([d for n, d in nx.degree(g, g.nodes())]).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "degree")


def average_closeness_centrality(g):
    stats = pd.Series(list(nx.closeness_centrality(g).values())).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "closeness")


def average_eigenvector_centrality(g):
    stats = pd.Series(list(nx.eigenvector_centrality(g).values())).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "closeness")


def average_betweenness_centrality(g):
    stats = pd.Series(list(nx.betweenness_centrality(g).values())).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "closeness")


def average_clustering(g):
    return {"average_clustering": nx.average_clustering(g)}


def graph_clique_number(g):
    return {"clique_number": nx.graph_clique_number(g)}


def average_degree_connectivity(g):
    return {"average_degree_connectivity": nx.average_degree_connectivity(g)}


def get_edge_number(g):
    return {"edge_number": len(g.edges)}


def get_node_number(g):
    return {"node_number": len(g.node)}


p = "../temp/top1000/movies/"
res = []
for movie in os.listdir(p):
    d = {}
    path = os.path.join(p, movie)
    os.path.join(path, f"{movie}.json")
    g_pth = glob.glob(os.path.join(path, f"json/*({'[0-9]'*4}).json"))
    if g_pth:
        try:
            with open(g_pth[0]) as f:
                g = json_graph.node_link_graph(json.load(f))
                d.update(get_edge_number(g))
                d.update(get_node_number(g))
                d.update(average_closeness_centrality(g))
                d.update(average_betweenness_centrality(g))
                d.update(average_eigenvector_centrality(g))
                d.update(average_graph_degree(g))
                d.update(average_graph_weight(g))
                d.update(average_clustering(g))
                d.update(graph_clique_number(g))
            with open(os.path.join(path, f"{movie}.json")) as f:
                movie_info = json.load(f)
                d.update(json.loads(movie_info))
            res.append(d)
        except:
            pass
pd.DataFrame(res).to_csv("features.csv")
# max avg, stdv, min eigenvector
# closeness_centrality

# if glob.glob(os.path.join(path, f"subtitles/{movie}*roles.pkl")):
#     try:
#         os.remove(glob.glob(os.path.join(path, f"subtitles/{movie}*roles.pkl"))[0])
#         os.remove(os.path.join(path, f"{movie}.json"))
#     except FileNotFoundError:
#         pass
