from turicreate import SFrame
from subs2graph.consts import IMDB_RATING_URL, TEMP_PATH, IMDB_CREW_URL, IMDB_TITLES_URL
from subs2graph.utils import download_file
import turicreate.aggregate as agg


class IMDbDatasets(object):

    def __init__(self):
        self._rating = None
        self._crew = None
        self._title = None

    def get_movie_rating(self, imdb_id):
        try:
            return self.rating[self.rating["tconst"]==f"tt{imdb_id}"]["averageRating"][0]
        except IndexError:
            return None

    @property
    def rating(self):
        if self._rating is None:
            download_file(IMDB_RATING_URL, f"{TEMP_PATH}/title.ratings.tsv.gz", False)
            self._rating = SFrame.read_csv(f"{TEMP_PATH}/title.ratings.tsv.gz", delimiter="\t", na_values=["\\N"])
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
        rating = self.rating[self.rating["numVotes"] > 100000].sort("averageRating", ascending=False)
        sf = self.title.join(rating)
        sf = sf[sf["titleType"] == "movie"]
        return sf.sort("averageRating", ascending=False)

    def get_directors_data(self):

        rating = self.rating[self.rating["numVotes"] > 100000]

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
