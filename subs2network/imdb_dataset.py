import turicreate.aggregate as agg
from turicreate import SFrame

from subs2network.consts import IMDB_RATING_URL, OUTPUT_PATH, IMDB_CREW_URL, IMDB_TITLES_URL, IMDB_PRINCIPALS_URL, DATA_PATH
from subs2network.utils import download_file


def get_gender(profession):
    if "actor" in profession:
        return "M"
    if "actress" in profession:
        return "F"
    raise IndexError


class IMDbDatasets(object):

    def __init__(self, verbose=False):
        self._rating = None
        self._crew = None
        self._title = None
        self._actors = None
        self._actors_movies = None
        self._first_name_gender = None
        self._actors_gender = None
        self._all_actors = None
        self._verbose = verbose

    def get_movie_rating(self, imdb_id):
        try:
            return self.rating[self.rating["tconst"] == f"tt{imdb_id}"]["averageRating"][0]
        except IndexError:
            return None

    def get_actor_gender(self, actor):
        try:
            return self.actors_gender[actor]
        except KeyError:
            try:
                first_name = actor.split(" ")[0].lower()
                return self.first_name_gender[first_name]["Gender"][:1]
            except KeyError:
                return "U"

    @property
    def actors_gender(self):
        if self._actors_gender is None:
            self._actors_gender = self.all_actors[["primaryName", "gender"]].unstack(["primaryName", "gender"])[0][
                "Dict of primaryName_gender"]
        return self._actors_gender

    def add_actor_gender(self, actor):
        try:
            return get_gender(actor["primaryProfession"])
        except IndexError:
            try:
                return self.get_gender_by_name(actor["primaryName"])
            except IndexError:
                return "U"

    def get_gender_by_name(self, actor):
        try:
            first_name = actor.split(" ")[0].lower()
            return self.first_name_gender[first_name]["Gender"][0]
        except KeyError:
            return None
        except IndexError:
            return None

    def get_actor_movies(self, actor):
        try:
            return self.actors_movies[self.actors_movies["nconst"] == actor]
        except IndexError:
            return None

    @property
    def popular_actors(self):
        if self._actors is None:
            download_file(IMDB_PRINCIPALS_URL, f"{OUTPUT_PATH}/title.principals.tsv.gz", False)
            self._actors = SFrame.read_csv(f"{OUTPUT_PATH}/title.principals.tsv.gz", delimiter="\t", na_values=["\\N"],
                                           verbose=self._verbose)
            self._actors = self._actors.filter_by(["actor", "actress"], "category")["tconst", "nconst"]

            self._actors = self._actors.join(
                self.rating[(self.rating["titleType"] == "movie") & (self.rating["numVotes"] > 1000)])
            self._actors = self._actors.groupby("nconst", operations={'averageRating': agg.AVG("averageRating"),
                                                                      'count': agg.COUNT()})
            self._actors = self._actors.sort("averageRating", ascending=False)
            names = SFrame.read_csv(f"{OUTPUT_PATH}/name.basics.tsv.gz", delimiter="\t")

            self._actors = self._actors.join(names)
            self._actors["gender"] = self._actors.apply(lambda p: self.add_actor_gender(p))

        return self._actors

    @property
    def actors_movies(self):
        if self._actors_movies is None:
            download_file(IMDB_PRINCIPALS_URL, f"{OUTPUT_PATH}/title.principals.tsv.gz", False)
            self._actors_movies = SFrame.read_csv(f"{OUTPUT_PATH}/title.principals.tsv.gz", delimiter="\t",
                                                  na_values=["\\N"], verbose=self._verbose)
            self._actors_movies = self._actors_movies.filter_by(["actor", "actress"], "category")[
                "tconst", "nconst", "characters"]
            self._actors_movies = self._actors_movies.join(self.title[self.title["titleType"] == "movie"])
            self._actors_movies = self._actors_movies.join(self.all_actors)
        return self._actors_movies

    @property
    def all_actors(self):
        if self._all_actors is None:
            self._all_actors = SFrame.read_csv(f"{OUTPUT_PATH}/name.basics.tsv.gz", delimiter="\t",
                                               na_values=["\\N"], verbose=self._verbose)
            self._all_actors["primaryProfession"] = self._all_actors["primaryProfession"].apply(lambda x: x.split(","))
            self._all_actors = self._all_actors.stack("primaryProfession", "primaryProfession")
            self._all_actors = self._all_actors.filter_by(["actor", "actress"], "primaryProfession")
            self._all_actors["gender"] = self._all_actors.apply(lambda p: self.add_actor_gender(p))
        return self._all_actors

    @property
    def rating(self):
        if self._rating is None:
            download_file(IMDB_RATING_URL, f"{OUTPUT_PATH}/title.ratings.tsv.gz", False)
            self._rating = SFrame.read_csv(f"{OUTPUT_PATH}/title.ratings.tsv.gz", delimiter="\t", na_values=["\\N"],
                                           verbose=self._verbose)
            self._rating = self._rating.join(self.title)
        return self._rating

    @property
    def crew(self):
        if self._crew is None:
            download_file(IMDB_CREW_URL, f"{OUTPUT_PATH}/title.crew.tsv.gz", False)
            self._crew = SFrame.read_csv(f"{OUTPUT_PATH}/title.crew.tsv.gz", delimiter="\t", na_values=["\\N"],
                                         verbose=self._verbose)
            self._crew["directors"] = self.crew["directors"].apply(lambda c: c.split(","))
            self._crew = self._crew.stack("directors", "directors")
        return self._crew

    @property
    def title(self):
        if self._title is None:
            download_file(IMDB_TITLES_URL, f"{OUTPUT_PATH}/title.basics.tsv.gz", False)
            self._title = SFrame.read_csv(f"{OUTPUT_PATH}/title.basics.tsv.gz", delimiter="\t", na_values=["\\N"],
                                          verbose=self._verbose)
        return self._title

    @property
    def first_name_gender(self):
        if self._first_name_gender is None:
            self._first_name_gender = SFrame(f"{DATA_PATH}/first_names_gender.sframe")
            self._first_name_gender = self._first_name_gender.unstack(["First Name", "Gender Dict"])[0][
                "Dict of First Name_Gender Dict"]
        return self._first_name_gender

    def get_movies_data(self):
        rating = self.rating[self.rating["numVotes"] > 1000]
        sf = self.title.join(rating)
        sf = sf[sf["titleType"] == "movie"]
        return sf.sort("averageRating", ascending=False)

    def get_directors_data(self):

        rating = self.rating[self.rating["numVotes"] > 10000]

        sf = self.crew.join(rating)

        title = self.title[self.title["titleType"] == "movie"]
        sf = sf.join(title)
        sf = sf.groupby(key_column_names='directors',
                        operations={'averageRating': agg.AVG("averageRating"), 'count': agg.COUNT()})

        sf = sf[sf["count"] > 5]

        names = SFrame.read_csv(f"{OUTPUT_PATH}/name.basics.tsv.gz", delimiter="\t")
        sf = sf.join(names, {"directors": "nconst"})
        return sf.sort("averageRating", ascending=False)

    def get_movies_by_character(self, character):
        p = self.actors_movies.dropna("characters").stack("characters", new_column_name="character")
        char_movies = p[p["character"].apply(lambda x: 1 if character in x else 0)]
        char_movies = char_movies.join(self.rating)
        char_movies = char_movies[char_movies["numVotes"] > 2000].filter_by("movie", "titleType")
        return char_movies[["primaryTitle", "tconst", "startYear", "averageRating", "numVotes"]].unique()

    def get_movies_by_title(self, title):
        m = self.rating[self.rating["primaryTitle"].apply(lambda x: 1 if title in x else 0)]
        m = m[m["numVotes"] > 2000].filter_by("movie", "titleType")
        return m[["primaryTitle", "tconst", "startYear", "averageRating", "numVotes"]].unique()


imdb_data = IMDbDatasets()
# imdb_data.actors
# isf.title
# import gzip
#
# with gzip.open(f"{TEMP_PATH}/title.basics.tsv.gz", 'rt') as f:
#     for line in f:
#         print(line)
