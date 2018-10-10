import os
from consts import *
import subliminal
from subliminal import video
import babelfish
import logging
import cPickle


class SubtitleFetcher(object):
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


    def fetch_subtitle(self, path):
        """
        Fetch the subtilte using subliminal or from local file
        :param path: the file path to save the subtitle or to load the subtitle details from
        :return:
        :rtype: dict
        """
        os.chdir(path)
        p = path + os.path.sep + self.get_video_string() + ".pkl"
        if not os.path.isfile(p):
            logging.debug("Fetching  %s's best matched subtitle" % self.get_video_string())
            # This download the best subtitle as SRT file to the current directory
            subtitle = subliminal.download_best_subtitles(set([self._video_obj]), set([self._lang],),
                                                          hearing_impaired=False).values()[0][0]
            self._save_subtitle_info_dict(subtitle, path)
        logging.debug("Loading %s metadata from %s" % (self.get_video_string(), p))
        return cPickle.load(file(p, "rb"))  # test if the subtitle object is loadable

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

    def _save_subtitle_info_dict(self, subtitle_obj, path):
        """
        save subtitle's metadata as a dict object to a file using cPickle
        :param subtitle_obj: dict with the subtitle's metadata that include the video's name, IMDB score, and
            downloaded subtitle's path
        :param path: the path to save the subtitle's metadata dict using cPcikle
        """

        p = path + os.path.sep + self.get_video_string() + ".pkl"
        d = {VIDEO_NAME: subtitle_obj.movie_name, IMDB_ID: subtitle_obj.movie_imdb_id,
             SUBTITLE_PATH: self._get_subtitle_srt_path(path)}
        logging.debug("Saving %s's metadata to %s" % (self.get_video_string(), p))
        cPickle.dump(d, file(p, "wb"))

    def get_video_string(self):
        """
        Return the video's representing name name
        :return: string with the video's representing name
        :rtype: str
        """
        if self.is_episode:
            return "%s %s" % (self._video_obj.series, self.episode_details_strings()[1])
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
        l = []

        if self.is_episode:
            l.append("S0%sE0%s" % (self._video_obj.season, self._video_obj.episode))
            l.append("S%sE%s" % (self._video_obj.season, self._video_obj.episode))
            e = ""
            if self._video_obj.season < 10:
                e += "S0%s" % self._video_obj.season
            else:
                e += "S%s" % self._video_obj.season
            if self._video_obj.episode < 10:
                e += "E0%s" % self._video_obj.episode
            else:
                e += "E%s" % self._video_obj.episode
            l.append(e)
            e = "S0%s" % self._video_obj.season
            if self._video_obj.episode < 10:
                e += "E0%s" % self._video_obj.episode
            else:
                e += "E%s" % self._video_obj.episode
            l.append(e)
        return l

    @property
    def is_episode(self):
        """
        Is video TV series episode?
        :return: True if the video is TV series episode or False otherwise
        :rtype: bool
        """
        return (type(self._video_obj) is video.Episode)

    @property
    def is_movie(self):
        """
        Is movie object?
        :return: True if the video is a movie or false otherwise
        :rtype: bool
        """
        return (type(self._video_obj) is video.Movie)

    @staticmethod
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
        logging.info("Fetching Subtitle For Movie:%s | Year: %s | IMDB ID: %s " % ( title, year, imdb_id))
        return video.Movie(name=name, title=title, year=year, imdb_id=imdb_id)

    @staticmethod
    def get_episode_obj(video_name, series, season_num, episode_num, episode_name, tvdb_id):
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
        logging.info("Fetching Subtitle Series:%s | Season: %s | Episode Number: %s | Name: %s, |ID: %s " % (
        series, season_num, episode_num, episode_name, tvdb_id))
        return video.Episode(video_name, series, season_num, episode_num, title=episode_name, tvdb_id=tvdb_id)


if __name__ == "__main__":
    movie = SubtitleFetcher.get_movie_obj("The Godfather", "The Godfather", 1972, "0068646")
    sf = SubtitleFetcher(movie)
    sf.fetch_subtitle("/home/graphlab/temp")