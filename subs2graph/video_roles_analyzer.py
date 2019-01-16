from imdb import IMDb
from imdb.utils import RolesList
from subs2graph.consts import IMDB_NAME, IMDB_CAST, MIN_NAME_SIZE, TEMP_PATH
import re
import stop_words
import logging
from itertools import permutations, combinations
from fuzzywuzzy import fuzz
from collections import defaultdict, Counter
import os
import pickle

from subs2graph.exceptions import CastNotFound
from subs2graph.utils import to_iterable
from nltk.corpus import names
import spacy

# import spacy


class VideoRolesAnalyzer(object):
    """
    Identifies roles in text using roles' information from IMDB
    """

    def __init__(self, imdb_id, use_top_k_roles=None, ignore_roles_names=None, roles_path=None):
        """
        Construct VideoRolesAnalyzer object which can get text and identify the characters names in the text
        :param imdb_id: imdb
        :param remove_roles_names: list of roles names to ignore when analyzing the roles dict.
        """

        self._roles_dict = defaultdict(set)
        self._roles_path = None
        if roles_path is not None:
            self._roles_path = roles_path
        if self._roles_path is None or not os.path.exists(self._roles_path):
            self._imdb_movie = IMDb().get_movie(imdb_id)
        self._stop_words_english = set(stop_words.get_stop_words("english")) - set([n.lower() for n in names.words()])
        self._use_top_k_roles = {}
        self._ignore_roles_names = set(ignore_roles_names)
        self._init_roles_dict(use_top_k_roles)

    def _init_roles_dict(self, use_top_k_roles, remove_possessives=True):
        """
        Initialize roles dict where each of the dict's key is represent a part of a unique role name and each value is
        a tuple of matching (Person, Role)
        :param use_top_k_roles: only use the top K IMDB roles
        :param remove_possessives: remove roles name which contains possessives, such as Andy's Wife
        :return:
        """
        if not os.path.exists(self._roles_path):
            nlp = spacy.load('en_core_web_sm')

            re_possessive = re.compile("(\w+\'s\s+\w+|\w+s\'\s+\w+)")
            try:
                cast_list = self._imdb_movie[IMDB_CAST]
            except KeyError:
                raise CastNotFound
            if use_top_k_roles is not None:
                cast_list = cast_list[:use_top_k_roles]

            for p in cast_list:
                for role in to_iterable(p.currentRole):

                    if role.notes == '(uncredited)':
                        break
                    if role is None or IMDB_NAME not in role.keys():
                        logging.warning("Could not find current role for %s" % str(p))
                    else:
                        if remove_possessives and len(re_possessive.findall(role[IMDB_NAME])) > 0:
                            logging.info("Skipping role with possessive name - %s" % role[IMDB_NAME])
                            continue
                        doc = nlp(role[IMDB_NAME])
                        adj = False
                        for token in doc:
                            if token.pos_ == "ADJ":
                                adj = True
                        if not adj:
                            self._add_role_to_roles_dict(p, role)
            with open(self._roles_path, "wb") as f:
                pickle.dump(self._roles_dict, f)
        else:
            with open(self._roles_path, "rb") as f:
                self._roles_dict = pickle.load(f)

    def _add_role_to_roles_dict(self, person, role):
        role_name = role[IMDB_NAME]
        if role_name in self._ignore_roles_names:
            return
        n = str(role_name).strip().lower().replace('"', '')
        re_white_space = re.compile(r"\b([\w-].*?)\b")
        re_apost_name = re.compile(r"^'(.*?)'$")
        # re_split = re.compile(r"([\w-].*?)")

        if re_apost_name.match(n):
            n = re_apost_name.findall(n)[0]
        # words_set = set(words.words()) - set([n.lower() for n in names.words()])
        parts = re_white_space.findall(n)

        for name_part in parts:

            if name_part == "himself" or name_part == "herself":
                self._add_role_to_roles_dict(person, person)
                continue

            if name_part in self._stop_words_english or len(name_part) < MIN_NAME_SIZE:
                continue

            if name_part.title() in self._ignore_roles_names:
                continue

            for part in name_part.split("-"):
                if part not in self._stop_words_english or len(part) > MIN_NAME_SIZE:
                    self._roles_dict[part].add((person, role))

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
        matched_roles = set()
        if not txt:
            return matched_roles

        txt = txt.strip().lower()
        s = "(%s)" % "|".join([fr"\b{r}\b" for r in self._roles_dict.keys()])

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
            if ent_type in {"PERSON", "ORG"}:
                p = p.lower().split()
                for r in p:
                    if r not in self._roles_dict:
                        logging.warning(f"Skipping role {r} -- not in imdb")
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
            if ent_type in {"PERSON", "ORG"}:
                r = r.lower()
                prev_person.append(r)

                if r not in self._roles_dict:
                    logging.warning(f"Skipping role {r} -- not in imdb")
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
    vde = VideoRolesAnalyzer(7959026)
    print(vde.find_roles_names_in_text("Sayid. l'm on it, Sayid sawyer."))
