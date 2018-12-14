import os
from subs2graph.consts import IMDB_ID, VIDEO_NAME, SUBTITLE_PATH, ROLES_PATH, TEMP_PATH
from subliminal import video, download_best_subtitles, save_subtitles, region, subtitle
import babelfish
import logging
import pickle
from subs2graph.exceptions import SubtitleNotFound
from guessit.api import GuessitException
from subs2graph.utils import get_movie_obj

import types


class SubtitleFetcher(object):
    region.configure('dogpile.cache.dbm', arguments={'filename': f'{TEMP_PATH}/cachefile.dbm'})

    """
    Responsible for fetching the subtitle information including metadata from the open subtitles websites or from
    analyzed local files
    """

    def __init__(self, video_obj, lang=babelfish.Language("eng")):
        """
        Class constructor which recieve as input a video object of a movie or TV series episode and the language of the
        video
        :param video_obj: video object that contains a movie's or TV series episode's details
        :param lang: the language of the video as babelfish object
        :return: None
        """
        self._video_obj = video_obj
        self._lang = lang

    def load_video_obj(self):
        if isinstance(self._video_obj, types.GeneratorType):
            self._video_obj = next(self._video_obj)

    def fetch_subtitle(self, path):
        """
        Fetch the subtilte using subliminal or from local file
        :param path: the file path to save the subtitle or to load the subtitle details from
        :return:
        :rtype: dict
        """

        p = path + os.path.sep + self.get_video_string() + ".pkl"
        if not os.path.isfile(p):
            self.load_video_obj()
            logging.debug("Fetching  %s's best matched subtitle" % self.get_video_string())
            # This download the best subtitle as SRT file to the current directory
            try:
                subtitle = download_best_subtitles({self._video_obj}, {self._lang},
                                                   hearing_impaired=True)
                subtitle = subtitle[self._video_obj]
            except GuessitException:
                subtitle = []
            if not subtitle:
                raise SubtitleNotFound
            save_subtitles(self._video_obj, subtitle, encoding='utf-8', directory=path)
            self._save_subtitle_info_dict(path)
        logging.debug("Loading %s metadata from %s" % (self.get_video_string(), p))
        with open(p, "rb") as f:
            # os.chdir(owd)
            return pickle.load(f)  # test if the subtitle object is loadable

    def _get_subtitle_srt_path(self, search_path):
        """
        Trys to find video's subtitle in the search path
        :param search_path: path for searching the video's subtitle
        :return: path to the video's subtitles or None
        :rtype: str
        """
        if self.is_episode:
            for p in os.listdir(search_path):
                for e in self.episode_details_strings():
                    if e.lower() in p.lower() and ".srt" in p.lower():
                        return search_path + os.path.sep + p
        elif self.is_movie:
            movie_name = self._video_obj.name.lower()
            for p in os.listdir(search_path):
                if movie_name in p.lower() and ".srt" in p.lower():
                    return search_path + os.path.sep + p
        return None

    def _save_subtitle_info_dict(self, path):
        """
        save subtitle's metadata as a dict object to a file using pickle
        :param subtitle_obj: dict with the subtitle's metadata that include the video's name, IMDB score, and
            downloaded subtitle's path
        :param path: the path to save the subtitle's metadata dict using cPcikle
        """

        p = path + os.path.sep + self.get_video_string() + ".pkl"
        roles_path = path + os.path.sep + self.get_video_string() + "roles.pkl"
        try:
            d = {VIDEO_NAME: self._video_obj.name, IMDB_ID: self._video_obj.imdb_id,
                 SUBTITLE_PATH: self._get_subtitle_srt_path(path), ROLES_PATH: roles_path}
        except AttributeError:
            d = {VIDEO_NAME: self._video_obj.name, IMDB_ID: self._video_obj.series_imdb_id,
                 SUBTITLE_PATH: self._get_subtitle_srt_path(path), ROLES_PATH: roles_path}

        logging.debug(f"Saving {self.get_video_string()}'s metadata to {p}")
        with open(p, "wb") as f:
            pickle.dump(d, f)

    def get_video_string(self):
        """
        Return the video's representing name name
        :return: string with the video's representing name
        :rtype: str
        """
        if self.is_episode:
            return f"{self._video_obj.series} {self.episode_details_strings()[1]}"
        if self.is_movie:
            return self._video_obj.name
        raise Exception("Unsuportted video type")

    def episode_details_strings(self):
        """
        In many case the downloaded subtitle file may contain various versions of the episodes season's & episode's names.
         This function return a list with most common episode's & season's name
        :return: list of strings with the most common season & episode names
        :rtype: list of [str]
        """
        episode_name_list = []

        if self.is_episode:
            episode_name_list.append("S0%sE0%s" % (self._video_obj.season, self._video_obj.episode))
            episode_name_list.append("S%sE%s" % (self._video_obj.season, self._video_obj.episode))
            e = ""
            if self._video_obj.season < 10:
                e += "S0%s" % self._video_obj.season
            else:
                e += "S%s" % self._video_obj.season
            if self._video_obj.episode < 10:
                e += "E0%s" % self._video_obj.episode
            else:
                e += "E%s" % self._video_obj.episode
            episode_name_list.append(e)
            e = "S0%s" % self._video_obj.season
            if self._video_obj.episode < 10:
                e += "E0%s" % self._video_obj.episode
            else:
                e += "E%s" % self._video_obj.episode
            episode_name_list.append(e)
        return episode_name_list

    @property
    def is_episode(self):
        """
        Is video TV series episode?
        :return: True if the video is TV series episode or False otherwise
        :rtype: bool
        """
        return type(self._video_obj) is video.Episode

    @property
    def is_movie(self):
        """
        Is movie object?
        :return: True if the video is a movie or false otherwise
        :rtype: bool
        """
        return type(self._video_obj) is video.Movie

    @staticmethod
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


if __name__ == "__main__":
    movie = get_movie_obj("Kill Bill: Vol 2", "Kill Bill: Vol. 2", 2004, "0378194")
    sf = SubtitleFetcher(movie)
    sf.fetch_subtitle("../temp")
