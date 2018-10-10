from subs_grpah.video_roles_analyzer import VideoRolesAnalyzer
import pysrt
from collections import Counter
from subs_grpah.consts import IMDB_ID, SUBTITLE_PATH
import logging
from subs_grpah.subtitle_fetcher import SubtitleFetcher


class SubtitleAnalyzer(object):
    """
    Fetch and analyze subtitle of a movie and use it to construct the conncetion between the movie various roles
    """

    def __init__(self, subtitle_info_dict, use_top_k_roles=None, ignore_roles_names=None):
        """
        Construct the SubtitleAnalyzer and create the video's role time line based
        :param subtitle_info_dict: dict with the video metadata created by the SubtitleFetcher class
        :param use_top_k_roles: use only the top K roles when constructing the movie? (None - to use all roles)
        :param ignore_roles_names: list of roles name to ignore

        """

        if ignore_roles_names is None:
            ignore_roles_names = []
        imdb_id = subtitle_info_dict[IMDB_ID]
        self._video_role_analyzer = VideoRolesAnalyzer(imdb_id, use_top_k_roles, ignore_roles_names)

        subtitle_srt_path = subtitle_info_dict[SUBTITLE_PATH]
        self._subs_entities_timeline_dict = self.create_video_roles_timeline(subtitle_srt_path)

    def create_video_roles_timeline(self, subtitle_path):
        if subtitle_path is None:
            raise Exception("Could not find video's subtitle in path" % subtitle_path)
        subs = pysrt.open(subtitle_path)
        subs_entities_timeline_dict = {}
        for s in subs:
            roles = self._video_role_analyzer.find_roles_names_in_text(s.text)
            if len(roles) > 0:
                t = s.start.seconds + s.start.minutes * 60
                subs_entities_timeline_dict[t] = roles
        logging.debug(str(subs_entities_timeline_dict))
        return subs_entities_timeline_dict

    def get_subtitles_entities_links(self, timelaps_seconds):
        secs = self._subs_entities_timeline_dict.keys()
        secs.sort()
        edges = []
        for i in range(len(secs)):
            entities1 = self._subs_entities_timeline_dict[secs[i]]
            if len(entities1) > 1:
                edges += self._get_edges(entities1, entities1)
            for j in range(i + 1, len(secs)):
                if secs[j] - secs[i] < timelaps_seconds:
                    entities2 = self._subs_entities_timeline_dict[secs[j]]
                    edges += self._get_edges(entities1, entities2)
        return Counter(edges)

    def _get_edges(self, l1, l2):
        edges = []
        for v1 in l1:
            for v2 in l2:
                if v1 == v2:
                    continue
                if v1 > v2:
                    v1, v2 = v2, v1
                edges.append((v1, v2))
        return edges

    @property
    def imdb_rating(self):
        return self._video_role_analyzer.rating()


if __name__ == "__main__":
    movie = SubtitleFetcher.get_movie_obj("The Godfather", "The Godfather", 1972, "0068646")
    sf = SubtitleFetcher(movie)
    d = sf.fetch_subtitle("/home/graphlab/temp")
    sa = SubtitleAnalyzer(d)
    print(sa.get_subtitles_entities_links(60))
