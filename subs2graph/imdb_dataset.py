from turicreate import SFrame
from subs2graph.consts import IMDB_RATING_URL, TEMP_PATH, IMDB_CREW_URL, IMDB_TITLES_URL, IMDB_PRINCIPALS_URL
from subs2graph.utils import download_file
import turicreate.aggregate as agg


def get_gender(profession):
    if "actor" in profession:
        return "M"
    if "actress" in profession:
        return "F"
    return "NA"


class IMDbDatasets(object):

    def __init__(self):
        self._rating = None
        self._crew = None
        self._title = None
        self._actors = None
        self._actors_movies = None

    def get_movie_rating(self, imdb_id):
        try:
            return self.rating[self.rating["tconst"] == f"tt{imdb_id}"]["averageRating"][0]
        except IndexError:
            return None

    def get_actor_gender(self, actor):
        try:
            return self.actors[self.actors["primaryName"] == actor]["gender"][0]
        except IndexError:
            return None

    def get_actor_movies(self, actor):
        try:
            return self.actors_movies[self.actors_movies["nconst"] == actor]
        except IndexError:
            return None

    @property
    def actors(self):
        if self._actors is None:
            download_file(IMDB_PRINCIPALS_URL, f"{TEMP_PATH}/title.principals.tsv.gz", False)
            self._actors = SFrame.read_csv(f"{TEMP_PATH}/title.principals.tsv.gz", delimiter="\t", na_values=["\\N"])
            self._actors = self._actors.filter_by(["actor", "actress"], "category")["tconst", "nconst"]
            names = SFrame.read_csv(f"{TEMP_PATH}/name.basics.tsv.gz", delimiter="\t")
            self._actors = self._actors.join(
                self.rating[(self.rating["titleType"] == "movie") & (self.rating["numVotes"] > 5000)])
            self._actors = self._actors.groupby("nconst", operations={'averageRating': agg.AVG("averageRating"),
                                                                      'count': agg.COUNT()})
            self._actors = self._actors.join(names)
            self._actors = self._actors.sort("averageRating", ascending=False)
            self._actors["gender"] = self._actors["primaryProfession"].apply(lambda p: get_gender(p))
        return self._actors

    @property
    def actors_movies(self):
        if self._actors_movies is None:
            download_file(IMDB_PRINCIPALS_URL, f"{TEMP_PATH}/title.principals.tsv.gz", False)
            self._actors_movies = SFrame.read_csv(f"{TEMP_PATH}/title.principals.tsv.gz", delimiter="\t",
                                                  na_values=["\\N"])
            self._actors_movies = self._actors_movies.filter_by(["actor", "actress"], "category")["tconst", "nconst"]
            self._actors_movies = self._actors_movies.join(self.title[self.title["titleType"] == "movie"])
            self._actors_movies = self._actors_movies.join(self.actors)
        return self._actors_movies

    @property
    def rating(self):
        if self._rating is None:
            download_file(IMDB_RATING_URL, f"{TEMP_PATH}/title.ratings.tsv.gz", False)
            self._rating = SFrame.read_csv(f"{TEMP_PATH}/title.ratings.tsv.gz", delimiter="\t", na_values=["\\N"])
            self._rating = self._rating.join(self.title)
        return self._rating

    @property
    def crew(self):
        if self._crew is None:
            download_file(IMDB_CREW_URL, f"{TEMP_PATH}/title.crew.tsv.gz", False)
            self._crew = SFrame.read_csv(f"{TEMP_PATH}/title.crew.tsv.gz", delimiter="\t", na_values=["\\N"])
            self._crew["directors"] = self.crew["directors"].apply(lambda c: c.split(","))
            self._crew = self._crew.stack("directors", "directors")
        return self._crew

    @property
    def title(self):
        if self._title is None:
            download_file(IMDB_TITLES_URL, f"{TEMP_PATH}/title.basics.tsv.gz", False)
            self._title = SFrame.read_csv(f"{TEMP_PATH}/title.basics.tsv.gz", delimiter="\t", na_values=["\\N"])
        return self._title

    def get_movies_data(self):
        rating = self.rating[self.rating["numVotes"] > 5000].sort("averageRating", ascending=False)
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

        names = SFrame.read_csv(f"{TEMP_PATH}/name.basics.tsv.gz", delimiter="\t")
        sf = sf.join(names, {"directors": "nconst"})
        return sf.sort("averageRating", ascending=False)


imdb_data = IMDbDatasets()
# isf.title
# import gzip
#
# with gzip.open(f"{TEMP_PATH}/title.basics.tsv.gz", 'rt') as f:
#     for line in f:
#         print(line)
