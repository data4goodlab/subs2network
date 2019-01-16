from subs2graph.video_roles_analyzer import VideoRolesAnalyzer
import pysrt
from collections import Counter, defaultdict
from subs2graph.consts import IMDB_ID, SUBTITLE_PATH, ROLES_PATH, IMDB_NAME, STANFORD_NLP_JAR, STANFORD_NLP_MODEL
import logging
from subs2graph.subtitle_fetcher import SubtitleFetcher
from nltk.tag import StanfordNERTagger
from nltk.tokenize import word_tokenize
from subs2graph.exceptions import SubtitleNotFound
import spacy
import unicodedata, re
from itertools import chain
from subs2graph.utils import get_movie_obj
import networkx as nx


class RemoveControlChars(object):

    def __init__(self):
        all_chars = (chr(i) for i in range(0x110000))
        control_chars = ''.join(c for c in all_chars if unicodedata.category(c) == 'Cc')
        # or equivalently and much more efficiently
        control_chars = ''.join(map(chr, chain(range(0, 32), range(127, 160))))
        self.control_char_re = re.compile('[%s]' % re.escape(control_chars))

    def remove_control_chars(self, s):
        return self.control_char_re.sub('', s)


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
        self._roles = defaultdict(lambda: {"role": None, "first": 0, "last": 0})
        self._interactions = {}
        if ignore_roles_names is None:
            ignore_roles_names = set()
        imdb_id = subtitle_info_dict[IMDB_ID]
        self._video_role_analyzer = VideoRolesAnalyzer(imdb_id.strip('t'), use_top_k_roles, ignore_roles_names,
                                                       subtitle_info_dict[ROLES_PATH])

        subtitle_srt_path = subtitle_info_dict[SUBTITLE_PATH]

        self._subs_entities_timeline_dict = self.create_video_roles_timeline(subtitle_srt_path)

    def create_video_roles_timeline(self, subtitle_path):
        if subtitle_path is None:
            raise SubtitleNotFound(f"Could not find video's subtitle in path: {subtitle_path}")
        subs = pysrt.open(subtitle_path)
        subs_entities_timeline_dict = {}

        re_brackets_split = re.compile("(\[.*?\]|.*?\:|^\(.*?\)$)")
        # (\[(.* ?)\] | (.* ?)\: | ^ \((.* ?)\)$)
        cc = RemoveControlChars()
        subs_clean = [cc.remove_control_chars(s.text.strip('-\\\/').replace("\n", " ")) for s in subs]
        subs_clean = [re.sub('<[^<]+?>', '', s) for s in subs_clean]
        brackets = [re_brackets_split.findall(s) for s in subs_clean]
        subs_text = [word_tokenize(s) for s in subs_clean]
        st = StanfordNERTagger(STANFORD_NLP_MODEL,
                               encoding='utf-8', path_to_jar=STANFORD_NLP_JAR)

        nlp = spacy.load('en_core_web_sm', disable=['parser', 'tagger', 'textcat'])
        entities_spacy = [[(ent.text, ent.label_) for ent in nlp(s).ents] for s in subs_clean]

        entities_nltk = st.tag_sents(subs_text)
        # role_counter = Counter()
        # for e in entities:
        #     role_counter += self._video_role_analyzer.count_apperence_in_text(e)
        for s, e_n, e_s, b in zip(subs, entities_nltk, entities_spacy, brackets):
            roles = self._video_role_analyzer.find_roles_names_in_text_ner(e_n, e_s)
            for item in b:
                roles.update(self._video_role_analyzer.find_roles_names_in_text(item))
            # role_counter.update(roles)
            if len(roles) > 0:
                t = s.start.seconds + s.start.minutes * 60
                subs_entities_timeline_dict[t] = roles
        logging.debug(str(subs_entities_timeline_dict))
        return subs_entities_timeline_dict

    def get_subtitles_entities_links(self, timelaps_seconds):

        timeline = sorted(self._subs_entities_timeline_dict.items(), key=lambda x: x[0])
        edges_counter = Counter()
        graphs = [nx.Graph(), nx.Graph()]
        for i, item in enumerate(timeline):
            t1, entities1 = item
            self.update_appearances(graphs, entities1, t1)
            if len(entities1) > 1:
                edges = self._get_edges(entities1, entities1)
                edges_counter.update(edges)
                self.update_interaction(graphs, edges, t1, edges_counter)
            for t2, entities2 in timeline[i + 1:]:
                if t2 - t1 < timelaps_seconds:
                    edges = self._get_edges(entities1, entities2)
                    edges_counter.update(edges)
                    self.update_appearances(graphs, entities1, t1)
                    self.update_appearances(graphs, entities2, t2)
                    edges_counter.update(self._get_edges(entities1, entities1))
                    self.update_interaction(graphs, edges, t2, edges_counter)

                else:
                    break
        return graphs

    @staticmethod
    def update_appearances(graphs, roles, t):
        for i, g in enumerate(graphs):
            for role in roles:
                r = role[i][IMDB_NAME]
                if r in g.node:
                    g.node[r]["last"] = t
                else:
                    g.add_node(r, **{"first": t, "last": t})

    @staticmethod
    def update_interaction(graphs, roles, t, weights):
        for i, g in enumerate(graphs):
            for role in roles:
                v, u = role[0][i][IMDB_NAME], role[1][i][IMDB_NAME]
                weight = weights[role]
                if (v, u) in g.edges:
                    g.adj[v][u]["last"] = t
                    g.adj[v][u]["weight"] += 1
                else:
                    g.add_edge(v, u, **{"first": t, "last": t, "weight": 1})

    def _get_edges(self, l1, l2):
        edges = []
        for v1 in l1:
            for v2 in l2:
                if str(v1[1]) == str(v2[1]):
                    continue
                if v1 > v2:
                    v1, v2 = v2, v1
                edges.append((v1, v2))
        return edges

    @property
    def imdb_rating(self):
        return self._video_role_analyzer.rating()


if __name__ == "__main__":
    movie = get_movie_obj("The Godfather", "The Godfather", 1972, "0068646")
    sf = SubtitleFetcher(movie)
    d = sf.fetch_subtitle("../temp")
    sa = SubtitleAnalyzer(d)
    G = sa.get_subtitles_entities_links(60)
