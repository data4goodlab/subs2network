from subliminal import video
import logging


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
    :param video_name: the episode name, which usually consists of the series name and episode details
    :param series: the episode's series name
    :param season_num: the episode's season number
    :param episode_num: the episode number
    :param episode_name: the episode title
    :param tvdb_id: the episode's id in TheTVDB website
    :return: video.Episode object
    :rtype: video.Episode
    """
    logging.info("Fetching Subtitle Series:%s | Season: %s | Episode Number: %s | Name: %s" % (
        series, season_num, episode_num, episode_name))
    return video.Episode(video_name, series, season_num, episode_num, title=episode_name, series_imdb_id=imdb_id)


def get_lazy_episode_obj(video_name, series, season_num, episode_num, episode_name, imdb_id):
    """
    Returns a subliminal TV episode object according to the episode's details
    :param video_name: the episode name, which usually consists of the series name and episode details
    :param series: the episode's series name
    :param season_num: the episode's season number
    :param episode_num: the episode number
    :param episode_name: the episode title
    :param tvdb_id: the episode's id in TheTVDB website
    :return: video.Episode object
    :rtype: video.Episode
    """
    yield get_episode_obj(video_name, series, season_num, episode_num, episode_name, imdb_id)
