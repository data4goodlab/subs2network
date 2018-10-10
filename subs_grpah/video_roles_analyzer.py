from imdb import IMDb
from imdb.utils import RolesList
from consts import *
import re
import stop_words
import logging


class VideoRolesAnalyzer(object):
    """
    Identifies roles in text using roles' information from IMDB
    """

    def __init__(self, imdb_id, use_top_k_roles=None, ignore_roles_names=[]):
        """
        Construct VideoRolesAnalyzer object which can get text and identify the characters names in the text
        :param imdb_id: imdb
        :param remove_roles_names: list of roles names to ignore when analyzing the roles dict.
        """

        self._roles_dict = {}
        self._imdb = IMDb()
        self._imdb_id = imdb_id
        self._imdb_movie = self._imdb.get_movie(self._imdb_id)
        self._stop_words_english = set(stop_words.get_stop_words("english"))
        self._ignore_roles = set([n.lower() for n in ignore_roles_names])
        self._init_roles_dict(use_top_k_roles)
        #self._roles_dict["batman"] = [("Christian Bale", "Batman")]


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
                    if remove_possessives and len(re_possessive.findall(role[IMDB_NAME])) >0:
                        logging.info("Skipping role with possessive name - %s" % role[IMDB_NAME] )
                        continue
                    if role[IMDB_NAME].lower() not in self._ignore_roles:
                        self._add_role_to_roles_dict(p, role)
            else:
                if p.currentRole is None or IMDB_NAME not in p.currentRole.keys():
                    logging.warning("Could not find current role for %s" % str(p))
                else:
                    role = p.currentRole
                    if remove_possessives and len(re_possessive.findall(role[IMDB_NAME])) >0:
                        logging.info("Skipping role with possessive name - %s" % role[IMDB_NAME] )
                        continue
                    if role[IMDB_NAME].lower() not in self._ignore_roles:
                        self._add_role_to_roles_dict(p, role)


    def _add_role_to_roles_dict(self, person, role):
        role_name = role[IMDB_NAME]
        n = unicode(role_name).strip().lower().replace('"', '')
        re_white_space = re.compile(r"\s+")
        re_apost_name = re.compile(r"^'(.*?)'$")

        if re_apost_name.match(n):
            n = re_apost_name.findall(n)[0]
        for name_part in re_white_space.split(n):
            if name_part in self._stop_words_english or len(name_part) < MIN_NAME_SIZE:
                continue

            if name_part not in self._roles_dict:
                self._roles_dict[name_part] = set()
            self._roles_dict[name_part].add((person, role))

    def find_roles_names_in_text(self, txt):
        """
        Find matched roles in the input text
        :param txt: input text
        :return: set of matched roles in the text
        """
        txt = txt.strip().lower()
        s = "(%s)" % "|".join([r"\b%s\b" % r for r in self._roles_dict.keys()])

        matched_roles = set()
        for r in re.findall(s, txt):
            if r not in self._roles_dict or len(self._roles_dict[r]) > 1:
                print "Warning: Skipping role %s -- several roles options" % r
                continue
            matched_roles.add(list(self._roles_dict[r])[0])
        return matched_roles

    def rating(self):
        """
        Return the video IMDB rating
        :return: Video's IMDB rating
        """
        return self._imdb_movie.data["rating"]


if __name__ == "__main__":
    vde = VideoRolesAnalyzer(636289)
    print vde.find_roles_names_in_text("Sayid. l'm on it, Sayid sawyer.")









