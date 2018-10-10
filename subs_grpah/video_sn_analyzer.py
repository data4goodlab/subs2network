import networkx  as nx
from subs_grpah.consts import ROLES_GRAPH, ACTORS_GRAPH, IMDB_RATING, VIDEO_NAME, MOVIE_YEAR
import numpy as np
from subs_grpah.utils import add_prefix_to_dict_keys
import os
import logging
from subs_grpah.subtitle_fetcher import SubtitleFetcher
from subs_grpah.subtitle_analyzer import SubtitleAnalyzer

class VideoSnAnalyzer(object):
    def __init__(self, video_name, entities_links_dict, video_rating):
        self._entities_dict = entities_links_dict
        self._video_name = video_name
        self._video_rating = video_rating

    def _temp_func(self, n):
        if type(n[1]) == str:
            return  n[1]
        else:
            return n[1].get("name")
    def construct_social_network_graph(self, graph_type=ROLES_GRAPH, min_weight=2):
        if graph_type == ROLES_GRAPH:
            entity_func = self._temp_func#lambda n: n[1].get("name")
        elif graph_type == ACTORS_GRAPH:
            entity_func = lambda n: n[0].get("name")  # Create actors graph
        else:
            raise Exception("Unsupported graph type %s" % graph_type)

        g = nx.Graph()

        for e, w in self._entities_dict.iteritems():
            if w < min_weight:
                continue
            g.add_edge(entity_func(e[0]), entity_func(e[1]), weight=w)
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
            for e in g.edges():
                d["%s_%s_weight" % (e[0], e[1])] = g.edge[e[0]][e[1]]["weight"]
        edge_weights = nx.get_edge_attributes(g, "weight")
        d["average_edge_weight"] = np.average(edge_weights.values())
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
                w.append(g.edge[u][v]["weight"])
            d[u] = np.average(w)
        return d


    @property
    def video_rating(self):
        return self._video_rating


if __name__ == "__main__":


    video_name = "The Godfather"
    movie = SubtitleFetcher.get_movie_obj(video_name, "The Godfather", 1972, "0068646")
    sf = SubtitleFetcher(movie)
    d = sf.fetch_subtitle("/home/graphlab/temp")
    sa = SubtitleAnalyzer(d, use_top_k_roles=10)
    e = sa.get_subtitles_entities_links(60)
    va = VideoSnAnalyzer(video_name, e)
    g = va.construct_social_network_graph(lambda n: n[1].get("name"))
    va.draw_graph(g, "The GodFather", None, None, "/home/graphlab/temp/%s Roles.png" % video_name)
    g = va.construct_social_network_graph(lambda n: n[0].get("name"))
    va.draw_graph(g, "The GodFather", None, None, "/home/graphlab/temp/%s Players.png" % video_name)
    print(nx.info(g))
    print(va.get_features_dict(g))
