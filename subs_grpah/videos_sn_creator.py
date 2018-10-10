from video_datasets_creator import VideoDatasetsCreator
from imdb import IMDb
from consts import *
import networkx as nx
from subtitle_fetcher import SubtitleFetcher
from subtitle_analyzer import SubtitleAnalyzer
from video_sn_analyzer import VideoSnAnalyzer
from collections import Counter
import matplotlib.pyplot as plt
import os
import logging

logging.basicConfig(level=logging.INFO)

class VideosSnCreator(object):

    def get_series_graphs(self, series_name, thetvdb_id, seasons_set, episodes_set, subtitles_path,
                           use_top_k_roles=None, timeelaps_seconds=60, graph_type=ROLES_GRAPH, min_weight=2):
        graphs_list = []
        series_details_dict = VideoDatasetsCreator.get_series_episodes_details(thetvdb_id, series_name)
        for k in series_details_dict.keys():
            episode_number = int(series_details_dict[k][EPISODE_NUMBER])
            seasons_number = int(series_details_dict[k][SEASON_NUMBER])
            name = self._get_episode_name(series_name, seasons_number, episode_number)
            if seasons_number not in seasons_set or episode_number not in episodes_set:
                continue
            try:
                g = self.get_episode_graph(name, series_name, seasons_number, episode_number,
                                           series_details_dict[k][EPISODE_NAME],
                                           series_details_dict[k][EPISODE_ID], subtitles_path=subtitles_path,
                                           use_top_k_roles=use_top_k_roles, timeelaps_seconds=timeelaps_seconds,
                                           graph_type=graph_type, min_weight=min_weight)
                graphs_list.append(g)
            except:
                logging.warning("Could not fetch %s subtitles" % name)
                continue

        return graphs_list
    def get_actor_movies_graphs(self, actor_name, subtitles_path,
                           movies_number=None, use_top_k_roles=None, timeelaps_seconds=60, graph_type=ACTORS_GRAPH, min_weight=2, ):
        graphs_list = []
        for id, title, year in self.get_actor_movies(actor_name):
            if year > MAX_YEAR:
                continue
            if movies_number is not None and len(graphs_list) >= movies_number:
                break
            movie_name = "%s (%s)" % (title, year)
            try:
                g = self.get_movie_graph(movie_name, title,year,id, subtitles_path,use_top_k_roles=use_top_k_roles,
                                 timeelaps_seconds=timeelaps_seconds,graph_type=graph_type,min_weight=min_weight)
                graphs_list.append(g)
            except:
                logging.warning("Could not fetch %s subtitles" % movie_name)
                continue

        return graphs_list


    def save_graphs_features(self, graphs_list, features_path, remove_unintresting_features, sep="\t"):
        features_dicts_list = []
        for g in graphs_list:
            d = VideoSnAnalyzer.get_features_dict(g, True)
            if d is None:
                continue
            features_dicts_list.append(d)
        all_keys = set()
        for d in features_dicts_list:
            all_keys |= set(d.keys())

        if remove_unintresting_features:
            all_keys -= set(self.get_unintresting_features_names(features_dicts_list))

        all_keys = list(all_keys)
        csv_lines = [sep.join(all_keys)]
        for d in features_dicts_list:
            l = []
            for k in all_keys:
                if k in d:
                    l.append(str(d[k]))
                else:
                    l.append("0")
            csv_lines.append(sep.join(l))
        file(features_path,"w").write("\n".join(csv_lines).encode("utf8"))



    def save_graphs_to_csv(self, graphs_list, csvs_path, sep="\t"):
        for g in graphs_list:
            csv_path = "%s/%s.csv" % (csvs_path, g.graph[VIDEO_NAME])

            if SERIES_NAME in g.graph:
                self.save_episode_graph_to_csv(g, g.graph[SERIES_NAME], g.graph[SEASON_NUMBER], g.graph[EPISODE_NUMBER], g.graph[IMDB_RATING],
                                               csv_path, add_headers=True,sep=sep)
            else:
                self.save_movie_graph_to_csv(g, g.graph[VIDEO_NAME], g.graph[IMDB_RATING], csv_path, add_headers=True, sep=sep)
    def draw_graphs(self, graphs_list, figures_path, format="png"):
        for g in graphs_list:
            draw_outpath = "%s/%s.%s" % (figures_path, g.graph[VIDEO_NAME], format)
            self.draw_graph(g, draw_outpath)


    def get_movie_graph(self, name, title, year, imdb_id, subtitles_path, use_top_k_roles=None, timeelaps_seconds=60,
                        graph_type=ROLES_GRAPH, min_weight=2):
        va = self._get_movie_video_sn_analyzer(name, title, year, imdb_id, subtitles_path, use_top_k_roles,
                                               timeelaps_seconds)
        g = va.construct_social_network_graph(graph_type, min_weight)
        g.graph[VIDEO_NAME] = name
        g.graph[MOVIE_YEAR] = year
        g.graph[IMDB_RATING] = va.video_rating
        return g

    def get_episode_graph(self, name, series_name, season_number, episode_number, episode_name, tvdb_id, subtitles_path,
                          use_top_k_roles=None, timeelaps_seconds=60,
                          graph_type=ROLES_GRAPH, min_weight=2):
        va = self._get_series_episode_video_sn_analyzer(name, series_name, season_number, episode_number, episode_name,
                                                        tvdb_id, subtitles_path, use_top_k_roles, timeelaps_seconds)
        g = va.construct_social_network_graph(graph_type, min_weight)
        g.graph[IMDB_RATING] = va.video_rating
        g.graph[VIDEO_NAME] = name
        g.graph[SERIES_NAME] = series_name
        g.graph[SEASON_NUMBER] = season_number
        g.graph[EPISODE_NUMBER] = episode_number
        return g


    def _get_movie_video_sn_analyzer(self, name, title, year, imdb_id, subtitles_path, use_top_k_roles,
                                     timeelaps_seconds):
        movie = SubtitleFetcher.get_movie_obj(name, title, year, imdb_id)
        return self._fetch_and_analyze_subtitle(movie, subtitles_path, use_top_k_roles, timeelaps_seconds)


    def _get_series_episode_video_sn_analyzer(self, name, series_name, season_number, episode_number, episode_name,
                                              tvdb_id, subtitles_path, use_top_k_roles, timeelaps_seconds):
        episode = SubtitleFetcher.get_episode_obj(name, series_name, season_number, episode_number, episode_name,
                                                  tvdb_id)
        return self._fetch_and_analyze_subtitle(episode, subtitles_path, use_top_k_roles, timeelaps_seconds)

    def _fetch_and_analyze_subtitle(self, video_obj, subtitle_path, use_top_k_roles, timeelaps_seconds):
        sf = SubtitleFetcher(video_obj)
        d = sf.fetch_subtitle(subtitle_path)
        sa = SubtitleAnalyzer(d, use_top_k_roles=use_top_k_roles)
        e = sa.get_subtitles_entities_links(timelaps_seconds=timeelaps_seconds)
        va = VideoSnAnalyzer(video_obj.name, e, sa.imdb_rating)
        return va


    def draw_graph(self, g, outpath, graph_layout=nx.graphviz_layout):

        pos = graph_layout(g)
        plt.figure(num=None, figsize=(15, 15), dpi=150)
        plt.axis('off')
        edge_labels = dict([((u, v,), d['weight'])
                            for u, v, d in g.edges(data=True)])

        nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels)

        nx.draw(g, pos, node_size=500, edge_cmap=plt.cm.Reds, with_labels=True)
        plt.savefig(outpath)
        plt.close()


    def get_actor_movies(self, actor_name):
        im = IMDb()
        p = im.search_person(actor_name)[0]

        movies_list = []
        m_list = im.get_person_filmography(p.getID())['data']['actor']
        for m in m_list:
            id = m.getID()
            year = m.get('year')
            title = m.get('title')
            movies_list.append((id, title, year))
        return movies_list

    def save_movie_graph_to_csv(self, g, movie_name, rating, outpath, add_headers=False, sep=";", append_to_file=True):
        headers = [VIDEO_NAME, SRC_ID, DST_ID, WEIGHT, IMDB_RATING]
        csv_lines = []
        if add_headers:
            csv_lines.append(sep.join(headers))
        for e in g.edges():
            r = [movie_name, e[0], e[1], str(g.edge[e[0]][e[1]][WEIGHT]), str(rating)]
            csv_lines.append(sep.join(r))
        if append_to_file:
            file(outpath, "a").write("\n".join(csv_lines).encode("utf8"))
        else:
            file(outpath, "w").write("\n".join(csv_lines).encode("utf8"))

    def _get_episode_name(self, series_name, season_number, episode_number):
        n = series_name
        n += "S"
        if season_number < 10:
            n+= "0"
        n += str(season_number)
        n+= "E"
        if episode_number < 10:
            n+= "0"
        n += str(episode_number)
        return n


    def save_episode_graph_to_csv(self, g, series_name, season_num, episode_num, rating, outpath, add_headers=False,
                                  sep=";", append_to_file=True):
        headers = [SERIES_NAME, SEASON_NUMBER, EPISODE_NUMBER, SRC_ID, DST_ID, WEIGHT, IMDB_RATING]
        csv_lines = []
        if add_headers:
            csv_lines.append(sep.join(headers))
        for e in g.edges():
            r = [series_name, str(season_num), str(episode_num), e[0], e[1], str(g.edge[e[0]][e[1]][WEIGHT]),
                 str(rating)]
            csv_lines.append(sep.join(r))
        if append_to_file:
            file(outpath, "a").write("\n".join(csv_lines).encode("utf8"))
        else:
            file(outpath, "w").write("\n".join(csv_lines).encode("utf8"))

    def get_unintresting_features_names(self, features_dicts):
        features_names = []

        for d in features_dicts:
            features_names += d.keys()
        c = Counter(features_names)
        return [k for k in c.keys() if c[k] < 5]

def create_dirs(t, name):
    try:
        os.mkdir("/home/graphlab/%s/%s" % (t,name))
        os.mkdir("/home/graphlab/%s/%s/csv" % (t,name))
        os.mkdir("/home/graphlab/%s/%s/graphs" % (t,name))
        os.mkdir("/home/graphlab/%s/%s/subtitles" % (t,name))
    except:
        pass

def test_get_series(name, id, seasons_set, episodes_set):
    create_dirs("series", name)
    v = VideosSnCreator()
    graphs = v.get_series_graphs(name,id,seasons_set,episodes_set,
                        "/home/graphlab/series/%s/subtitles" % name)
    v.save_graphs_to_csv(graphs, "/home/graphlab/series/%s/csv" % name )
    v.draw_graphs(graphs, "/home/graphlab/series/%s/graphs" % name)
    v.save_graphs_features(graphs, "/home/graphlab/series/%s/%s features.tsv" % (name,name), True )

def test_get_actor_movies(name):
    create_dirs("actors", name)
    v = VideosSnCreator()
    graphs = v.get_actor_movies_graphs(name,"/home/graphlab/actors/%s/subtitles" % name,  movies_number=None, use_top_k_roles=20)
    v.save_graphs_features(graphs, "/home/graphlab/actors/%s/%s features.tsv" % (name,name), True )
    v.save_graphs_to_csv(graphs, "/home/graphlab/actors/%s/csv" % name )
    v.draw_graphs(graphs, "/home/graphlab/actors/%s/graphs" % name)


def test_get_movie(movie_title, year, imdb_id):
    create_dirs("movies", movie_title)
    v = VideosSnCreator()
    graphs = [v.get_movie_graph("%s (%s)" % (movie_title, year),movie_title, year, imdb_id, "/home/graphlab/movies/%s/subtitles" % ( movie_title), use_top_k_roles=None, min_weight=5 )]
    v.save_graphs_features(graphs, "/home/graphlab/movies/%s features.tsv" % ( movie_title), True )
    v.save_graphs_to_csv(graphs, "/home/graphlab/movies/%s/csv" % movie_title )
    v.draw_graphs(graphs, "/home/graphlab/movies/%s/graphs" % movie_title )

if __name__ == "__main__":
    #test_get_movie("The Dark Knight",2008, "0468569")
    #test_get_series("The Simpsons", "71663",set(range(20,22)), set(range(1,25)))
    test_get_actor_movies("Tom Cruise")
    #v = VideosSnCreator()
    #name = "Modern Family"
    #v.save_series_graphs(name, "95011" ,set(range(1,7)), set(range(1,25)),"/home/graphlab/series/%s/subtitles" % name,
                         #"/home/graphlab/series/%s/csv" % name, draw_graph_path="/home/graphlab/series/%s/graphs" % name)



