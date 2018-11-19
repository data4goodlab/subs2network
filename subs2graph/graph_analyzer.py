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


def analyze_movies():
    p = "../temp/top1000/movies/"
    res = []
    for movie in os.listdir(p):
        d = {}
        path = os.path.join(p, movie)
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


def analyze_directors():
    p = "../temp/directors/"
    for director in os.listdir(p):
        res = []
        json_path = os.path.join(p, director, "json")
        graphs = []
        for g_pth in os.listdir(json_path):
            g_pth = os.path.join(json_path, g_pth)
            if g_pth:
                try:
                    with open(g_pth) as f:
                        g = json_graph.node_link_graph(json.load(f))
                        d = extract_graph_features(g)
                        d.update({"rating": g.graph["imdb_rating"], "year": g.graph["movie_year"],
                                  "name": g.graph["movie_name"]})
                        graphs.append(g)
                    res.append(d)
                except:
                    pass
        if graphs:
            joined_grpah = nx.compose_all(graphs)
            d = extract_graph_features(joined_grpah)
            d["name"] = "combined"
            res.append(d)
            pd.DataFrame(res).to_csv(f"../temp/output/{director}.csv")


def extract_graph_features(g):
    d = {}
    d.update(get_edge_number(g))
    d.update(get_node_number(g))
    d.update(average_closeness_centrality(g))
    d.update(average_betweenness_centrality(g))
    # d.update(average_eigenvector_centrality(g))
    d.update(average_graph_degree(g))
    d.update(average_graph_weight(g))
    d.update(average_clustering(g))
    d.update(graph_clique_number(g))
    return d


from tqdm import tqdm


def create_pdf():
    from PIL import Image

    # imagelist is the list with all image filenames
    p = "../temp/top1000/movies/"
    res = []
    for i, movie in enumerate(tqdm(os.listdir(p), total=len(os.listdir(p)))):

        path = os.path.join(p, movie)
        image = glob.glob(os.path.join(path, f"graphs/*({'[0-9]'*4}).png"))
        if image:
            res.append(Image.open(image[0]).convert("RGB"))
        # if i> 100:
        #     break

    res[0].save("test2.pdf", "PDF", resolution=100.0, save_all=True, append_images=res[1:])


# analyze_directors()
create_pdf()
