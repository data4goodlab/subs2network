import json
import logging
import os
import shutil
import sys

import networkx as nx
import requests
from networkx.readwrite import json_graph
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Content
from subliminal import video
from tqdm import tqdm
import glob
from subs2graph.consts import DOWNLOAD_PATH
from turicreate import SFrame

def send_email(send_to, subject, mail_content):
    try:
        sg = SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
        # make a message object
        from_email = Email("dimakagan15@gmail.com")
        to_email = Email(send_to)
        content = Content("text/plain", mail_content)
        mail = Mail(from_email, subject, to_email, content)
        sg.client.mail.send.post(request_body=mail.get())
    except:
        return False
    return True


def add_prefix_to_dict_keys(d, prefix, sep="-"):
    h = {}
    if type(d) is dict:
        d = d.items()
    for k, v in d:
        h[prefix + sep + k] = v
    return h


def get_movie_obj(name, title, year, imdb_id):
    """
    Returns a subliminal movie object according to the movie's details
    :param name: movie's name
    :param title: the movie's title
    :param year: the year the movie was created
    :param imdb_id: the movie's IMDB id
    :return: video.Movie object
    :rtype: video.Movie
    """
    logging.info("Fetching Subtitle For Movie:%s | Year: %s | IMDB ID: %s " % (title, year, imdb_id))
    return video.Movie(name=name, title=title, year=year, imdb_id=imdb_id)


def get_episode_obj(video_name, series, season_num, episode_num, episode_name, imdb_id):
    """
    Returns a subliminal TV episode object according to the episode's details
    :param imdb_id:
    :param video_name: the episode name, which usually consists of the series name and episode details
    :param series: the episode's series name
    :param season_num: the episode's season number
    :param episode_num: the episode number
    :param episode_name: the episode title
    :return: video.Episode object
    :rtype: video.Episode
    """
    logging.info("Fetching Subtitle Series:%s | Season: %s | Episode Number: %s | Name: %s" % (
        series, season_num, episode_num, episode_name))
    return video.Episode(video_name, series, season_num, episode_num, title=episode_name, series_imdb_id=imdb_id)


def get_lazy_episode_obj(video_name, series, season_num, episode_num, episode_name, imdb_id):
    """
    Returns a subliminal TV episode object according to the episode's details
    :param imdb_id:
    :param video_name: the episode name, which usually consists of the series name and episode details
    :param series: the episode's series name
    :param season_num: the episode's season number
    :param episode_num: the episode number
    :param episode_name: the episode title
    :return: video.Episode object
    :rtype: video.Episode
    """
    yield get_episode_obj(video_name, series, season_num, episode_num, episode_name, imdb_id)


def download_file(url, output_path, exist_overwrite, min_size=0, verbose=True):
    # Todo handle requests.exceptions.ConnectionError
    if exist_overwrite or not os.path.exists(output_path):
        r = requests.get(url, stream=True)
        total_size = int(r.headers.get('content-length', 0))
        size_read = 0
        if total_size - min_size > 0:
            with tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                disable=not verbose
            ) as pbar:
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                            size_read = min(total_size, size_read + 1024)
                            pbar.update(len(chunk))


def to_iterable(item):
    if item is None:  # include all nodes via iterator
        item = []
    elif not hasattr(item, "__iter__") or isinstance(item, str):  # if vertices is a single node
        item = [item]  # ?iter()
    return item


def delete_movies_results(p):
    for movie in os.listdir(p):
        path = os.path.join(p, movie)
        if glob.glob(os.path.join(path, f"subtitles/*.srt")):
            try:
                os.remove(glob.glob(os.path.join(path, f"subtitles/{movie}*roles.pkl"))[0])
                os.remove(os.path.join(path, f"{movie}.json"))
            except FileNotFoundError:
                pass
        shutil.rmtree(os.path.join(path, "json"), ignore_errors=True)
        shutil.rmtree(os.path.join(path, "graphs"), ignore_errors=True)
        shutil.rmtree(os.path.join(path, "csv"), ignore_errors=True)


#f"{DOWNLOAD_PATH}/movies/*/subtitles/*.srt"
def move_files(src_regex, dst):
    for movie in glob.glob(src_regex):
        shutil.copyfile(movie, os.path.join(dst, os.path.basename(movie)))


def convert_json_to_gfx(json_path_iter):
    for json_path in json_path_iter:
        with open(json_path) as f:
            g = json_graph.node_link_graph(json.load(f))
            nx.write_graphml(g, f"{json_path.split('.')[0]}.graphml")


def combine_json_graphs(json_path_iter):
    graphs = []
    for json_path in json_path_iter:
        with open(json_path) as f:
            graphs.append(json_graph.node_link_graph(json.load(f)))
    joined_graph = nx.compose_all(graphs)
    nx.write_graphml(joined_graph, f"joined_graph.graphml")


def combine_distinct_json_graphs(json_path_iter):
    graphs = []
    c = 0
    sf = SFrame.read_json('starwars.json')
    for json_path in json_path_iter:
        with open(json_path) as f:
            g = json_graph.node_link_graph(json.load(f))
            for v in g.nodes:
                g.node[v]["year"] = str(g.graph["movie_year"])
                try:
                    g.node[v]["image_url"] = sf[sf["title"] == v]["base_images"][0]['desktop']['ratio_1x1']
                except IndexError:
                    g.node[v]["image_url"] = ""
            g = nx.convert_node_labels_to_integers(g, first_label=c, label_attribute="name")
            c += len(g.nodes)
            graphs.append(g)
    joined_graph = nx.compose_all(graphs)
    nx.write_graphml(joined_graph, f"joined_graph.graphml")

# starw = glob.glob("/Users/dimakagan/Projects/subs2graph/output/star/d3/*.json")
# combine_distinct_json_graphs(starw)
