from imdb import IMDb
from imdb.utils import RolesList
from subs2grpah.consts import IMDB_NAME, IMDB_CAST, MIN_NAME_SIZE
import re
import stop_words
import logging
from itertools import permutations, combinations
from fuzzywuzzy import fuzz
from nltk.tag import StanfordNERTagger
from nltk.tokenize import word_tokenize
# from nltk import  ne_chunk
# from nltk.tag import pos_tag
from nltk.corpus import words
from nltk.corpus import names
from collections import defaultdict, Counter


# import spacy


class VideoRolesAnalyzer(object):
    """
    Identifies roles in text using roles' information from IMDB
    """

    def __init__(self, imdb_id, use_top_k_roles=None, ignore_roles_names=None):
        """
        Construct VideoRolesAnalyzer object which can get text and identify the characters names in the text
        :param imdb_id: imdb
        :param remove_roles_names: list of roles names to ignore when analyzing the roles dict.
        """

        if ignore_roles_names is None:
            ignore_roles_names = []
        self._roles_dict = defaultdict(set)
        self._imdb = IMDb()
        self._imdb_id = imdb_id
        self._imdb_movie = self._imdb.get_movie(self._imdb_id)
        self._stop_words_english = set(stop_words.get_stop_words("english")) - set([n.lower() for n in names.words()])
        self._ignore_roles = set([n.lower() for n in ignore_roles_names])
        self._use_top_k_roles = {}
        self._init_roles_dict(use_top_k_roles)
        self._st = StanfordNERTagger(
            '/home/dima/Documents/subs2graph/ner/classifiers/english.all.3class.distsim.crf.ser.gz',
            encoding='utf-8', path_to_jar="/home/dima/Documents/subs2graph/ner/stanford-ner.jar")
        # self._nlp = spacy.load('en_core_web_sm')

        # self._roles_dict["batman"] = [("Christian Bale", "Batman")]

    def _init_roles_dict(self, use_top_k_roles, remove_possessives=True):
        """
        Initialize roles dict where each of the dict's key is represent a part of a unique role name and each value is
        a tuple of matching (Person, Role)
        :param use_top_k_roles: only use the top K IMDB roles
        :param remove_possessives: remove roles name which contains possessives, such as Andy's Wife
        :return:
        """
        re_possessive = re.compile("(\w+\'s\s+\w+)")
        cast_list = self._imdb_movie[IMDB_CAST]
        if use_top_k_roles is not None:
            cast_list = cast_list[:use_top_k_roles]
        for p in cast_list:
            if type(p.currentRole) is RolesList:
                for role in p.currentRole:
                    if remove_possessives and len(re_possessive.findall(role[IMDB_NAME])) > 0:
                        logging.info("Skipping role with possessive name - %s" % role[IMDB_NAME])
                        continue
                    if role[IMDB_NAME].lower() not in self._ignore_roles:
                        self._add_role_to_roles_dict(p, role)
            else:
                if p.currentRole is None or IMDB_NAME not in p.currentRole.keys():
                    logging.warning("Could not find current role for %s" % str(p))
                else:
                    role = p.currentRole
                    if remove_possessives and len(re_possessive.findall(role[IMDB_NAME])) > 0:
                        logging.info("Skipping role with possessive name - %s" % role[IMDB_NAME])
                        continue
                    if role[IMDB_NAME].lower() not in self._ignore_roles:
                        self._add_role_to_roles_dict(p, role)

    def _add_role_to_roles_dict(self, person, role):
        role_name = role[IMDB_NAME]
        n = str(role_name).strip().lower().replace('"', '')
        re_white_space = re.compile(r"\s+")
        re_apost_name = re.compile(r"^'(.*?)'$")

        if re_apost_name.match(n):
            n = re_apost_name.findall(n)[0]
        # words_set = set(words.words()) - set([n.lower() for n in names.words()])
        parts = re_white_space.split(n)
        for name_part in parts:
            if name_part in self._stop_words_english or len(name_part) < MIN_NAME_SIZE:
                break
            # if name_part in words_set and len(parts) > 1:
            #     break

            # if name_part not in self._roles_dict:
            #     self._roles_dict[name_part] = set()
            self._roles_dict[name_part].add((person, role))

    def find_roles_names_in_text(self, txt):
        """
        Find matched roles in the input text
        :param txt: input text
        :return: set of matched roles in the text
        """
        txt_raw = str(txt)
        txt = txt.strip().lower().replace("\n", " ")
        s = "(%s)" % "|".join([fr"\b{r}\b" for r in self._roles_dict.keys()])

        matched_roles = set()
        roles_in_text = set(re.findall(s, txt))

        for r in roles_in_text:
            if r not in self._roles_dict:
                print(f"Warning: Skipping role {r} -- several roles options")
                continue
            if len(self._roles_dict[r]) == 1:
                matched_roles.add(list(self._roles_dict[r])[0])
                continue
            for actor, role in self._roles_dict[r]:
                if r == role[IMDB_NAME].lower():
                    matched_roles.add((actor, role))
                    continue
            for fr in combinations(roles_in_text, 2):
                for actor, role in self._roles_dict[r]:
                    if fuzz.token_set_ratio(role[IMDB_NAME], fr) > 95:
                        matched_roles.add((actor, role))
                        break
        return matched_roles

    def find_roles_names_in_text_ner(self, stanford_ner, spacy_ner):
        """
        Find matched roles in the input text
        :param txt: input text
        :return: set of matched roles in the text
        """
        stanford_res = self.find_roles_names_in_text_stanford_ner(stanford_ner)
        spacy_res = self.find_roles_names_in_text_spacy_ner(spacy_ner)
        return stanford_res.union(spacy_res)

    def find_roles_names_in_text_spacy_ner(self, classified_text):
        """
        Find matched roles in the input text
        :param txt: input text
        :return: set of matched roles in the text
        """
        matched_roles = set()

        for p, ent_type in classified_text:
            if ent_type == "PERSON":
                p = p.lower().split()
                for r in p:
                    if r not in self._roles_dict:
                        print(f"Warning: Skipping role {r} -- not in imdb")
                        continue
                    if len(self._roles_dict[r]) == 1:
                        matched_roles.add(list(self._roles_dict[r])[0])
                        continue
                    for actor, role in self._roles_dict[r]:
                        if r == role[IMDB_NAME].lower():
                            matched_roles.add((actor, role))
                            continue
                    for fr in combinations(p, 2):
                        for actor, role in self._roles_dict[r]:
                            if fuzz.token_set_ratio(role[IMDB_NAME], fr) > 95:
                                matched_roles.add((actor, role))
                                break

        return matched_roles

    def find_roles_names_in_text_stanford_ner(self, classified_text):
        """
        Find matched roles in the input text
        :param txt: input text
        :return: set of matched roles in the text
        """
        matched_roles = set()
        prev_person = []

        for r, ent_type in classified_text:
            if ent_type == "PERSON":
                r = r.lower()
                prev_person.append(r)

                if r not in self._roles_dict:
                    print(f"Warning: Skipping role {r} -- not in imdb")
                    continue
                if len(self._roles_dict[r]) == 1:
                    matched_roles.add(list(self._roles_dict[r])[0])
                    continue
                for actor, role in self._roles_dict[r]:
                    if r == role[IMDB_NAME].lower():
                        matched_roles.add((actor, role))
                        continue
                for fr in combinations(prev_person, 2):
                    for actor, role in self._roles_dict[r]:
                        if fuzz.token_set_ratio(role[IMDB_NAME], fr) > 95:
                            matched_roles.add((actor, role))
                            break
            else:
                prev_person = []
        return matched_roles

    def count_apperence_in_text(self, classified_text):
        """
        Find matched roles in the input text
        :param txt: input text
        :return: set of matched roles in the text
        """
        prev_person = []
        role_counter = Counter()
        for r, ent_type in classified_text:
            if ent_type == "PERSON":
                r = r.lower()
                prev_person.append(r)

                if r not in self._roles_dict:
                    continue
                if len(self._roles_dict[r]) == 1:
                    role_counter[list(self._roles_dict[r])[0][1][IMDB_NAME]] += 1
                    continue
                for actor, role in self._roles_dict[r]:
                    if r == role[IMDB_NAME].lower():
                        role_counter[role[IMDB_NAME]] += 1
                        continue
                for fr in combinations(prev_person, 2):
                    for actor, role in self._roles_dict[r]:
                        if fuzz.token_set_ratio(role[IMDB_NAME], fr) > 95:
                            role_counter[role[IMDB_NAME]] += 1
                            break
            else:
                prev_person = []
        return role_counter

    def rating(self):
        """
        Return the video IMDB rating
        :return: Video's IMDB rating
        """
        return self._imdb_movie.data["rating"]


if __name__ == "__main__":
    vde = VideoRolesAnalyzer(636289)
    print(vde.find_roles_names_in_text("Sayid. l'm on it, Sayid sawyer."))
