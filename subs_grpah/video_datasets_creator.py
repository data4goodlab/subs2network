from xml.dom.minidom import parseString
import urllib2
from consts import *
from subtitle_analyzer import SubtitleAnalyzer
import time
import logging
import os

class VideoDatasetsCreator(object):
    """
    Creates datasets with meta data infroamtion about a target TV series or a movie
    """

    def __init__(self, series_csv_path=None, subtitles_save_path="/home/graphlab/temp/subtitles"):
        self._subtitles_save_path = subtitles_save_path
        if series_csv_path is not None:
            self._series_data_sframe = SFrame.read_csv(series_csv_path, delimiter=';', header=True,
                                                       column_type_hints={EPISODE_NUMBER: int,
                                                                          SEASON_NUMBER: int,
                                                                          SERIES_ID: int})

    @staticmethod
    def get_series_episodes_details(id, series_name):
        """
        Returns TV series episodes' details from TheTVDB website
        :param id: series id in TheTVDB
        :param series_name: series name
        :return: dict with episodes information
        """
        logging.info("Retreving series data of %s" % id)
        xml_path = "%s/%s.xml" % (TEMP_PATH, id)
        if os.path.isfile(xml_path):
            s = file(xml_path).read()
        else:
            u = urllib2.urlopen(THE_TVDB_URL % id, timeout=90)
            s = u.read()
            file(xml_path, "w").write(s)
        doc = parseString(s)
        episodes_dict = {}
        attributes_names_list = [EPISODE_ID, EPISODE_NAME, EPISODE_NUMBER, EPISODE_RATING, DVD_EPISODE,
                                 EPISODE_GUEST_STARTS, SERIES_ID, SEASON_ID, SEASON_NUMBER, DVD_SEASON]
        for e in doc.getElementsByTagName("Episode"):
            id = "%s_%s" % (VideoDatasetsCreator._get_value_by_tagname(e, SEASON_ID),
                            VideoDatasetsCreator._get_value_by_tagname(e, EPISODE_ID))
            if id in episodes_dict:
                raise Exception("episode already parsed %s" % id)

            episodes_dict[id] = {SERIES_NAME: series_name}

            for a in attributes_names_list:
                v = VideoDatasetsCreator._get_value_by_tagname(e, a)
                episodes_dict[id][a] = ""
                if v is not None:
                    episodes_dict[id][a] = v
        return episodes_dict

    @staticmethod
    def _get_value_by_tagname(node, tag_name):
        try:
            return node.getElementsByTagName(tag_name)[0].childNodes[0].data.replace(";", " ").replace("\n", "")
        except:
            logging.warning("Faild to get data of %s" % tag_name)
            return None

    def create_series_data_csv(self, series_id, series_name, outpath):
        """
        Creates CSV with the series episodes details
        :param series_id: series TheTVDB id
        :param series_name: series name
        :param outpath: the output path of to save the series details
        :return: save the series details into CSV
        """
        episodes_dict = self.get_series_episodes_details(series_id, series_name)
        headers = [SERIES_NAME, SERIES_ID, SEASON_ID, SEASON_NUMBER, EPISODE_ID, EPISODE_NUMBER, EPISODE_NAME,
                   DVD_SEASON, DVD_EPISODE, EPISODE_GUEST_STARTS]
        csv = [";".join(headers)]
        for e_id in episodes_dict.keys():
            csv.append(";".join([unicode(episodes_dict[e_id][a]) for a in headers]))
        txt = "\n".join(csv).encode("utf8")
        file(outpath, "a").write(txt)


if __name__ == "__main__":
    pass
    # create_series_dataset(176941, "Sherlock", "/home/graphlab/Series/sherlock.csv")
    #for i in range(1,4):
    #create_series_links_dataset(176941, i, None, 60, "/home/graphlab/Series/sherlock.csv", sn_outpath="/home/graphlab/Series/sherlock_sn.csv", subtitles_save_path="/home/graphlab/subtitles/Sherlock")
    #movie_name = "The Lion King"
    #create_movie_links_dataset(movie_name, movie_name, 1994, "0110357", 60,  "/home/graphlab/subtitles/movies", "/home/graphlab/movies/%s.sn.csv" % movie_name)
    #cretate_actor_links_dataset("Kevin Bacon", 60, "/home/graphlab/actors/Kevin Bacon/subtitles", "/home/graphlab/actors/Kevin Bacon/graphs")
