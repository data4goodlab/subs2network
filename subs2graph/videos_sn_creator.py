from subs2graph.video_datasets_creator import VideoDatasetsCreator
from imdb import IMDb
from subs2graph.consts import EPISODE_NAME, EPISODE_ID, EPISODE_RATING, EPISODE_NUMBER, ROLES_GRAPH, SEASON_NUMBER, \
    ACTORS_GRAPH, TEMP_PATH, IMDB_RATING_URL, IMDB_TITLES_URL,\
    MOVIE_YEAR, MAX_YEAR, SERIES_NAME, VIDEO_NAME, SRC_ID, DST_ID, WEIGHT, IMDB_RATING
from subs2graph.subtitle_fetcher import SubtitleFetcher
from subs2graph.subtitle_analyzer import SubtitleAnalyzer
from subs2graph.video_sn_analyzer import VideoSnAnalyzer
from collections import Counter
import matplotlib.pyplot as plt
import os
import logging
from subs2graph.exceptions import SubtitleNotFound
import networkx as nx
import json
from networkx.readwrite import json_graph
from subs2graph.utils import get_movie_obj, get_episode_obj, get_lazy_episode_obj
from turicreate import SFrame
from subs2graph.utils import download_file
logging.basicConfig(level=logging.INFO)


def get_series_graphs(series_name, imdb_id, seasons_set, episodes_set, subtitles_path,
                      use_top_k_roles=None, timeelaps_seconds=60, graph_type=ROLES_GRAPH, min_weight=2):
    series_details_dict = VideoDatasetsCreator.get_series_episodes_details(imdb_id, series_name, subtitles_path)
    seasons = set(series_details_dict.keys()) & seasons_set
    for seasons_number in seasons:
        for episode_number in episodes_set:
            try:
                episode = series_details_dict[seasons_number][episode_number]
            except KeyError:
                continue

            episode_name = episode[EPISODE_NAME]
            episode_rating = episode[EPISODE_RATING]
            name = _get_episode_name(series_name, seasons_number, episode_number)

            try:
                yield get_episode_graph(name, series_name, seasons_number, episode_number,
                                        episode_name, episode_rating, subtitles_path=subtitles_path,
                                        use_top_k_roles=use_top_k_roles, timeelaps_seconds=timeelaps_seconds,
                                        graph_type=graph_type, min_weight=min_weight, imdb_id=imdb_id)
            except SubtitleNotFound:
                logging.warning("Could not fetch %s subtitles" % episode_name)
                continue


def get_person_movies_graphs(actor_name, subtitles_path, types, movies_number=None,
                             use_top_k_roles=None, timeelaps_seconds=60, graph_type=ACTORS_GRAPH,
                             min_weight=2):
    graphs_list = []
    for m_id, title, year in get_person_movies(actor_name, types):
        if year > MAX_YEAR:
            continue
        if movies_number is not None and len(graphs_list) >= movies_number:
            break
        movie_name = f"{title.replace('.','').replace('/','')} ({year})"
        try:
            g = get_movie_graph(movie_name, title, year, m_id, subtitles_path, use_top_k_roles=use_top_k_roles,
                                timeelaps_seconds=timeelaps_seconds, graph_type=graph_type,
                                min_weight=min_weight)
            graphs_list.append(g)
        except (SubtitleNotFound, AttributeError):
            logging.warning("Could not fetch %s subtitles" % movie_name)
            continue

    return graphs_list


def save_graphs_features(graphs_list, features_path, remove_unintresting_features, sep="\t"):
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
        all_keys -= set(get_unintresting_features_names(features_dicts_list))

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
    with open(features_path, "w") as f:
        f.write("\n".join(csv_lines))


def save_graphs_to_csv(graphs_list, csvs_path, sep="\t"):
    for g in graphs_list:
        csv_path = f"{csvs_path}/{g.graph[VIDEO_NAME]}.csv"

        if SERIES_NAME in g.graph:
            save_episode_graph_to_csv(g, g.graph[SERIES_NAME], g.graph[SEASON_NUMBER], g.graph[EPISODE_NUMBER],
                                      g.graph[IMDB_RATING],
                                      csv_path, add_headers=True, sep=sep)
        else:
            save_movie_graph_to_csv(g, g.graph[VIDEO_NAME], g.graph[IMDB_RATING], csv_path, add_headers=True,
                                    sep=sep)


def save_graphs_to_json(graphs_list, output_dir):
    for g in graphs_list:
        data = json_graph.node_link_data(g)
        csv_path = f"{output_dir}/{g.graph[VIDEO_NAME]}.json"
        with open(csv_path, 'w') as fp:
            json.dump(data, fp)


def draw_graphs(graphs_list, figures_path, output_format="png"):
    for g in graphs_list:
        draw_outpath = f"{figures_path}/{g.graph[VIDEO_NAME]}.{output_format}"
        draw_graph(g, draw_outpath)


def get_movie_graph(name, title, year, imdb_id, subtitles_path, use_top_k_roles=None, timeelaps_seconds=60,
                    graph_type=ROLES_GRAPH, min_weight=2, rating=None):
    va = _get_movie_video_sn_analyzer(name, title, year, imdb_id, subtitles_path, use_top_k_roles,
                                      timeelaps_seconds, rating)
    g = va.construct_social_network_graph(graph_type, min_weight)
    g.graph[VIDEO_NAME] = name
    g.graph[MOVIE_YEAR] = year
    g.graph[IMDB_RATING] = va.video_rating
    return g


def get_episode_graph(name, series_name, season_number, episode_number, episode_name, imdb_rating,
                      subtitles_path, imdb_id, use_top_k_roles=None, timeelaps_seconds=60,
                      graph_type=ROLES_GRAPH, min_weight=2):
    va = _get_series_episode_video_sn_analyzer(name, series_name, season_number, episode_number, episode_name,
                                               subtitles_path, use_top_k_roles, timeelaps_seconds, imdb_id, imdb_rating)

    g = va.construct_social_network_graph(graph_type, min_weight)
    g.graph[IMDB_RATING] = imdb_rating
    g.graph[VIDEO_NAME] = name
    g.graph[SERIES_NAME] = series_name
    g.graph[SEASON_NUMBER] = season_number
    g.graph[EPISODE_NUMBER] = episode_number
    return g


def _get_movie_video_sn_analyzer(name, title, year, imdb_id, subtitles_path, use_top_k_roles,
                                 timeelaps_seconds, rating=None):
    movie = get_movie_obj(name, title, year, imdb_id)
    return _fetch_and_analyze_subtitle(movie, subtitles_path, use_top_k_roles, timeelaps_seconds, rating)


def _get_series_episode_video_sn_analyzer(name, series_name, season_number, episode_number, episode_name,
                                          subtitle_path, use_top_k_roles, timeelaps_seconds, imdb_id, imdb_rating):
    episode = get_episode_obj(name, series_name, season_number, episode_number, episode_name, imdb_id)
    sf = SubtitleFetcher(episode)
    d = sf.fetch_subtitle(subtitle_path)
    return analyze_subtitle(name, d, use_top_k_roles, timeelaps_seconds, imdb_rating)


def analyze_subtitle(name, subs_dict, use_top_k_roles, timeelaps_seconds, imdb_rating=None):
    sa = SubtitleAnalyzer(subs_dict, use_top_k_roles=use_top_k_roles)
    e = sa.get_subtitles_entities_links(timelaps_seconds=timeelaps_seconds)
    if imdb_rating is None:
        imdb_rating = sa.imdb_rating
    return VideoSnAnalyzer(name, e, imdb_rating)


def _fetch_and_analyze_subtitle(video_obj, subtitle_path, use_top_k_roles, timeelaps_seconds, imdb_rating=None):
    sf = SubtitleFetcher(video_obj)
    d = sf.fetch_subtitle(subtitle_path)
    sa = SubtitleAnalyzer(d, use_top_k_roles=use_top_k_roles)
    e = sa.get_subtitles_entities_links(timelaps_seconds=timeelaps_seconds)
    if imdb_rating is None:
        imdb_rating = sa.imdb_rating
    return VideoSnAnalyzer(video_obj.name, e, imdb_rating)


def draw_graph(g, outpath, graph_layout=nx.spring_layout):
    pos = graph_layout(g)
    plt.figure(num=None, figsize=(15, 15), dpi=150)
    plt.axis('off')
    edge_labels = dict([((u, v,), d['weight'])
                        for u, v, d in g.edges(data=True)])

    nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels)

    nx.draw(g, pos, node_size=500, edge_cmap=plt.cm.Reds, with_labels=True)
    plt.savefig(outpath)
    plt.close()


def get_person_movies(person_name, types=["actor"]):
    im = IMDb()
    p = im.search_person(person_name)[0]
    m_list = im.get_person_filmography(p.getID())
    person_filmography = dict(item for m in m_list['data']['filmography'] for item in m.items())
    for t in types:
        m_list = person_filmography[t]
        for m in m_list:
            m_id = m.getID()
            year = m.get('year')
            title = m.get('title')
            if year:
                yield m_id, title, year


def _get_episode_name(series_name, season_number, episode_number):
    n = series_name
    n += "S"
    if season_number < 10:
        n += "0"
    n += str(season_number)
    n += "E"
    if episode_number < 10:
        n += "0"
    n += str(episode_number)
    return n


def save_episode_graph_to_csv(g, series_name, season_num, episode_num, rating, outpath, add_headers=False,
                              sep=";", append_to_file=False):
    headers = [SERIES_NAME, SEASON_NUMBER, EPISODE_NUMBER, SRC_ID, DST_ID, WEIGHT, IMDB_RATING]
    csv_lines = []
    if add_headers:
        csv_lines.append(sep.join(headers))
    for v, u in g.edges():
        r = [series_name, str(season_num), str(episode_num), v, u, str(g.adj[v][u][WEIGHT]),
             str(rating)]
        csv_lines.append(sep.join(r))
    if append_to_file:
        with open(outpath, "a") as f:
            f.write("\n".join(csv_lines))
    else:
        with open(outpath, "w") as f:
            f.write("\n".join(csv_lines))


def save_movie_graph_to_csv(g, movie_name, rating, outpath, add_headers=False, sep=";", append_to_file=False):
    headers = [VIDEO_NAME, SRC_ID, DST_ID, WEIGHT, IMDB_RATING]
    csv_lines = []
    if add_headers:
        csv_lines.append(sep.join(headers))
    for v, u in g.edges():
        r = [movie_name, v, u, str(g.adj[v][u][WEIGHT]), str(rating)]
        csv_lines.append(sep.join(r))
    if append_to_file:
        with open(outpath, "a") as f:
            f.write("\n".join(csv_lines))
    else:
        with open(outpath, "w") as f:
            f.write("\n".join(csv_lines))


def get_unintresting_features_names(features_dicts, min_freq=5):
    features_names = []

    for d in features_dicts:
        features_names += d.keys()
    c = Counter(features_names)
    return [k for k in c.keys() if c[k] < min_freq]


def create_dirs(t, name):
    os.makedirs(f"../temp/{t}/{name}", exist_ok=True)
    os.makedirs(f"../temp/{t}/{name}/csv", exist_ok=True)
    os.makedirs(f"../temp/{t}/{name}/json", exist_ok=True)
    os.makedirs(f"../temp/{t}/{name}/graphs", exist_ok=True)
    os.makedirs(f"../temp/{t}/{name}/subtitles", exist_ok=True)


def test_get_series(name, s_id, seasons_set, episodes_set):
    create_dirs("series", name)
    graphs = []
    for g in get_series_graphs(name, s_id, seasons_set, episodes_set, f"../temp/series/{name}/subtitles"):
        save_output([g], "series", name)
        graphs.append(g)
    save_graphs_features(graphs, f"../temp/""/{name}/{name} features.tsv", True)
    joined_grpah = nx.compose_all(graphs)
    joined_grpah.graph[VIDEO_NAME] = name
    joined_grpah.graph["movie_year"] = MAX_YEAR
    save_output([joined_grpah], "series", name)


def test_get_actor_movies(name):
    create_dirs("actors", name)
    graphs = get_person_movies_graphs(name, f"../temp/actors/{name}/subtitles", ["actor"], movies_number=None)

    save_output(graphs, "actors", name)


def test_get_director_movies(name):
    create_dirs("directors", name)
    graphs = get_person_movies_graphs(name, f"../temp/directors/{name}/subtitles", ["director"], movies_number=None)

    save_output(graphs, "directors", name)


def save_output(graphs, type, name):
    save_graphs_to_csv(graphs, f"../temp/{type}/{name}/csv")
    draw_graphs(graphs, f"../temp/{type}/{name}/graphs")
    save_graphs_to_json(graphs, f"../temp/{type}/{name}/json")


def save_graphs_outputs(graphs, name):
    save_graphs_features(graphs, f"../temp/actors/{name}/{name} features.tsv", True)
    save_graphs_to_csv(graphs, f"../temp/actors/{name}/csv")
    draw_graphs(graphs, f"../temp/actors/{name}/graphs")


def test_get_movie(movie_title, year, imdb_id, additional_data=None):
    create_dirs("movies", movie_title)
    rating = None
    if additional_data:
        rating = additional_data["averageRating"]

    graphs = [get_movie_graph(f"{movie_title} ({year})", movie_title, year, imdb_id,
                              f"../temp/movies/{movie_title}/subtitles", use_top_k_roles=None,
                              min_weight=5, rating=rating)]

    with open(f"../temp/movies/{movie_title}/{movie_title}_roles.json", 'w') as fp:
        json.dump(json.dumps(additional_data), fp)

    save_output(graphs, "movies", movie_title)

    graphs = [get_movie_graph(f"{movie_title} ({year})", movie_title, year, imdb_id,
                              f"../temp/movies/{movie_title}/subtitles", use_top_k_roles=None,
                              min_weight=5, rating=rating, graph_type=ACTORS_GRAPH)]

    save_output(graphs, "movies", f"{movie_title}_actors")



def get_movies_data():
    # https: // datasets.imdbws.com / title.ratings.tsv.gz
    download_file(IMDB_RATING_URL, f"{TEMP_PATH}/title.ratings.tsv.gz", True)
    rating = SFrame.read_csv(f"{TEMP_PATH}/title.ratings.tsv.gz", delimiter="\t")
    rating = rating[rating["numVotes"] > 100000].sort("averageRating", ascending=False)
    # https: // datadbws.com / name.basics.tsv.gz
    download_file(IMDB_TITLES_URL, f"{TEMP_PATH}/title.basics.tsv.gz", False)
    title = SFrame.read_csv(f"{TEMP_PATH}/title.basics.tsv.gz", delimiter="\t")
    sf = title.join(rating)
    sf = sf[sf["titleType"] == "movie"]
    # title = title[title["numVotes"] > 100000].sort("averageRating", ascending=False)
    return sf.sort("averageRating", ascending=False)


def get_best_movies():
    movies = get_movies_data().head(1000)
    for m in movies:
        try:
            if not os.path.exists(f"../temp/movies/{m['primaryTitle']}/{m['primaryTitle']} features.tsv"):
                test_get_movie(m["primaryTitle"], m["startYear"], m["tconst"].strip("t"), m)
        except SubtitleNotFound:
            pass

if __name__ == "__main__":
    get_best_movies()
    # test_get_movie("The Dark Knight",2008, "0468569")
    # test_get_series("Friends", "0108778", set(range(1, 11)), set(range(1, 30)))
    # test_get_director_movies("Quentin Tarantino")
    # test_get_actor_movies("Brendan Fraser")
    # v = VideosSnCreator()
    # name = "Modern Family"
    # v.save_series_graphs(name, "95011" ,set(range(1,7)), set(range(1,25)),"/temp/series/%s/subtitles" % name,
    # "../temp/series/%s/csv" % name, draw_graph_path="../temp/series/%s/graphs" % name)
