import networkx  as nx
from subs2grpah.consts import ROLES_GRAPH, ACTORS_GRAPH, IMDB_RATING, VIDEO_NAME, MOVIE_YEAR
import numpy as np
from subs2grpah.utils import add_prefix_to_dict_keys
import os
import logging
from subs2grpah.subtitle_fetcher import SubtitleFetcher
from subs2grpah.subtitle_analyzer import SubtitleAnalyzer
import matplotlib.pyplot as plt
from subs2grpah.utils import get_movie_obj


class VideoSnAnalyzer(object):
    def __init__(self, video_name, entities_links_dict, video_rating=0):
        self._entities_dict = entities_links_dict
        self._video_name = video_name
        self._video_rating = video_rating

    def _temp_func(self, n):
        if type(n[1]) == str:
            return n[1]
        else:
            return n[1].get("name")

    def construct_social_network_graph(self, graph_type=ROLES_GRAPH, min_weight=2):
        if graph_type == ROLES_GRAPH:
            g = self._entities_dict[1]
        elif graph_type == ACTORS_GRAPH:
            g = self._entities_dict[0]
        else:
            raise Exception("Unsupported graph type %s" % graph_type)

        g = g.edge_subgraph([(u, v) for (u, v, d) in g.edges(data=True) if d['weight'] >= min_weight])


        g.graph[IMDB_RATING] = self.video_rating
        g.graph[VIDEO_NAME] = self._video_name
        return g

    @staticmethod
    def get_features_dict(g, calculate_edges_features=False):
        if len(g.edges()) == 0:
            return None
        d = {"edges_number": len(g.edges()), "nodes_number": len(g.nodes())}

        d.update(add_prefix_to_dict_keys(nx.degree(g, g.nodes()), "degree"))
        d.update(add_prefix_to_dict_keys(nx.closeness_centrality(g), "closeness"))
        d.update(add_prefix_to_dict_keys(nx.pagerank(g), "pagerank"))
        d.update(add_prefix_to_dict_keys(nx.betweenness_centrality(g), "betweenness"))
        d.update(add_prefix_to_dict_keys(VideoSnAnalyzer.get_nodes_average_weights(g), "avg-weight"))

        if calculate_edges_features:
            for v, u in g.edges():
                d[f"{v}_{u}_weight"] = g.adj[v][u]["weight"]
        edge_weights = nx.get_edge_attributes(g, "weight")
        d["average_edge_weight"] = np.average(list(edge_weights.values()))
        d["max_edge_weight"] = max(edge_weights.values())
        if VIDEO_NAME in g.graph:
            d[VIDEO_NAME] = g.graph[VIDEO_NAME]
        if IMDB_RATING in g.graph:
            d[IMDB_RATING] = g.graph[IMDB_RATING]
        if MOVIE_YEAR in g.graph:
            d[MOVIE_YEAR] = g.graph[MOVIE_YEAR]

        return d

    @staticmethod
    def get_nodes_average_weights(g):
        d = {}
        for u in g.nodes():
            w = []
            for v in g.neighbors(u):
                w.append(g.adj[u][v]["weight"])
            d[u] = np.average(w)
        return d

    @property
    def video_rating(self):
        return self._video_rating

    def draw_graph(self, g, outpath, graph_layout=nx.spring_layout):

        pos = graph_layout(g)
        plt.figure(num=None, figsize=(15, 15), dpi=150)
        plt.axis('off')
        edge_labels = dict([((u, v,), d['weight'])
                            for u, v, d in g.edges(data=True)])

        nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels)

        nx.draw(g, pos, node_size=500, edge_cmap=plt.cm.Reds, with_labels=True)
        plt.savefig(outpath)
        plt.close()


if __name__ == "__main__":
    video_name = "The Matrix"
    movie = get_movie_obj(video_name, "The Matrix", 1999, "0133093")
    sf = SubtitleFetcher(movie)
    d = sf.fetch_subtitle("../temp")
    sa = SubtitleAnalyzer(d, use_top_k_roles=20)
    e = sa.get_subtitles_entities_links(60)
    va = VideoSnAnalyzer(video_name, e)
    g = va.construct_social_network_graph(ROLES_GRAPH)
    va.draw_graph(g, f"../temp/{video_name} Roles.png")
    print(nx.info(g))
    g = va.construct_social_network_graph(ACTORS_GRAPH)
    va.draw_graph(g, f"../temp/{video_name} Players.png")
    print(nx.info(g))
    print(va.get_features_dict(g))
