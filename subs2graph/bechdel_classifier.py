from turicreate import SFrame
from subs2graph.consts import DATA_PATH, DOWNLOAD_PATH
from turicreate import aggregate as agg
import pandas as pd
import math
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import precision_score, recall_score
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import roc_auc_score

from subs2graph.imdb_dataset import imdb_data
import numpy as np

genres = {'Action',
          'Adventure',
          'Animation',
          'Biography',
          'Comedy',
          'Crime',
          'Documentary',
          'Drama',
          'Family',
          'Fantasy',
          'Film-Noir',
          'History',
          'Horror',
          'Music',
          'Musical',
          'Mystery',
          'Romance',
          'Sci-Fi',
          'Sport',
          'Thriller',
          'War',
          'Western'}

drop_cols = ["X1", "genres", "imdbid", "originalTitle", 'endYear', 'isAdult', 'tconst',
             'titleType', 'tconst.1', 'titleType.1', 'originalTitle.1', 'isAdult.1', 'startYear.1', 'endYear.1',
             'runtimeMinutes.1', 'genres.1', 'primaryTitle', 'X1', 'id', 'imdbid', 'id']


def split_vals(a, n):
    return a[:n].copy(), a[n:].copy()


from sklearn.metrics import precision_score


def print_score(m, X_train, y_train, X_valid, y_valid):
    res = [
        (y_train, m.predict_proba(X_train)[:, 1]),
           roc_auc_score(y_valid, m.predict_proba(X_valid)[:, 1]),
           precision_score(y_train, m.predict(X_train)), precision_score(y_valid, m.predict(X_valid))]
    if hasattr(m, 'oob_score_'):
        res.append(m.oob_score_)
    print(res)


def calculate_gender_centrality():
    gender_centrality = pd.read_csv(f"{DOWNLOAD_PATH}/gender.csv", index_col=0)

    gender_centrality["rank_pagerank"] = gender_centrality.groupby("movie_name")["pagerank"].rank(
        ascending=False).astype(int)
    rank_pagerank = pd.pivot_table(gender_centrality[["gender", "rank_pagerank"]], index="gender",
                                   columns="rank_pagerank", aggfunc=len).T
    rank_pagerank["F%"] = rank_pagerank["F"] / (rank_pagerank["F"] + rank_pagerank["M"])
    rank_pagerank["M%"] = rank_pagerank["M"] / (rank_pagerank["F"] + rank_pagerank["M"])
    for gender in set().union(gender_centrality.gender.values):
        gender_centrality[gender] = gender_centrality.apply(lambda _: int(gender in _.gender), axis=1)
    gender_centrality = gender_centrality.sort_values(["movie_name", "rank_pagerank"])
    return gender_centrality


def get_female_in_top_10_roles():
    gender_centrality = calculate_gender_centrality()
    gender_centrality_movies = gender_centrality[gender_centrality["rank_pagerank"] < 11].groupby("movie_name").agg(
        ["sum", "count"])
    female_in_top_10 = pd.DataFrame()
    female_in_top_10["F_top10"] = gender_centrality_movies["F"]["sum"] / gender_centrality_movies["F"]["count"]
    female_in_top_10["year"] = gender_centrality_movies["year"]["sum"] / gender_centrality_movies["year"]["count"]
    female_in_top_10["movie_name"] = gender_centrality_movies.index.str.replace(" - roles", "")
    female_in_top_10["year"] = female_in_top_10["year"].astype(int)
    return female_in_top_10


def get_relationship_triangles():
    triangles = SFrame.read_csv(f"{DOWNLOAD_PATH}/triangles.csv", usecols=["0", "1", "2", "3", "4"])
    triangles_gender = triangles.apply(
        lambda x: [imdb_data.get_actor_gender(x["0"]), imdb_data.get_actor_gender(x["1"]),
                   imdb_data.get_actor_gender(x["2"])])
    triangles_gender = triangles_gender.unpack()
    triangles_gender["movie"] = triangles["3"]
    triangles_gender["year"] = triangles["4"]
    triangles_gender = triangles_gender.dropna()
    triangles_gender = triangles_gender.join(imdb_data.title, {"movie": "primaryTitle", "year": "startYear"})

    triangles_gender["1"] = triangles_gender["X.0"] == "M"
    triangles_gender["2"] = triangles_gender["X.1"] == "M"
    triangles_gender["3"] = triangles_gender["X.2"] == "M"
    triangles_gender["total_men"] = triangles_gender["1"] + triangles_gender["2"] + triangles_gender[
        "3"]

    triangles_gender["genres"] = triangles_gender["genres"].apply(lambda x: x.split(","))

    return triangles_gender


def count_triangles():
    triangles_gender_bin = get_relationship_triangles()

    triangles_df = triangles_gender_bin.to_dataframe()
    triangles_df = triangles_df[triangles_df["genres"].notnull()]
    for genre in set().union(*triangles_df.genres.values):
        triangles_df[genre] = triangles_df.apply(lambda _: int(genre in _.genres), axis=1)
    triangles_df = triangles_df.drop(["1", "2", "3", "genres"], axis=1)
    triangles_df = triangles_df.rename(columns={"total_men": "Males in triangle"})
    piv = pd.pivot_table(triangles_df, columns="Males in triangle", values=genres, aggfunc=np.sum)
    piv["total"] = piv[0] + piv[1] + piv[2] + piv[3]
    for i in range(4):
        piv[i] = piv[i] / piv["total"]
    return piv


def triangles():
    triagles_gender = get_relationship_triangles()

    moive_triangle = triagles_gender.groupby(["movie", "year", "total"], operations={'count': agg.COUNT()})

    traingles_at_movie = moive_triangle.to_dataframe().pivot_table(index=["movie", "year"], values="count",
                                                                   columns='total',
                                                                   aggfunc=lambda x: x)
    traingles_at_movie = traingles_at_movie.fillna(0)

    traingles_at_movie = traingles_at_movie.reset_index()
    return traingles_at_movie


class BechdelClassifier(object):

    def __init__(self):
        self.bechdel = SFrame.read_csv(f"{DATA_PATH}/bechdel.csv", column_type_hints={"imdbid": str})
        self.bechdel.sort("year", False)
        self.bechdel["tconst"] = "tt" + self.bechdel["imdbid"]
        self.bechdel_imdb = imdb_data.title.join(self.bechdel)
        self.clf = RandomForestClassifier(n_jobs=-1, n_estimators=100, max_depth=5, random_state=1)
        self._graph_features = SFrame()

    @property
    def graph_features(self):
        if not self.graph_features:
            try:
                self.graph_features = SFrame.read_csv(f"{DATA_PATH}/bechdel_features.csv")
            except:
                t = triangles()
                self.graph_features = SFrame.read_csv("../temp/graph_features.csv")

                self.graph_features = self.graph_features.join(SFrame(get_female_in_top_10_roles()),
                                                               on={"movie_name": "movie_name", "year": "year"})
                self.graph_features = self.graph_features.join(SFrame(t), on={"movie_name": "movie", "year": "year"})
                self.graph_features["total_tri"] = self.graph_features["0"] + self.graph_features["1"] + \
                                                   self.graph_features["2"] + self.graph_features["3"]
                for i in range(4):
                    self.graph_features[f"{i}%"] = self.graph_features[str(i)] / self.graph_features["total_tri"]

                self.graph_features.save(f"{DATA_PATH}/bechdel_features.csv", "csv")
        return self.graph_features

    @graph_features.setter
    def graph_features(self, value):
        self._graph_features = value

    def build_dataset(self):

        self.graph_features = imdb_data.title.filter_by("movie", "titleType").join(self.graph_features,
                                                                                   on={"primaryTitle": "movie_name",
                                                                                       "startYear": "year"})
        self.graph_features = self.graph_features[self.graph_features["node_number"] > 5]
        bechdel_ml = self.graph_features.join(self.bechdel_imdb,
                                              on={"primaryTitle": "primaryTitle", "startYear": "year"}, how='left')

        bechdel_ml = bechdel_ml[bechdel_ml["genres"] != None]
        bechdel_ml = bechdel_ml.to_dataframe()
        bechdel_ml["genres"] = bechdel_ml.genres.str.split(",")
        for genre in set().union(*bechdel_ml.genres.values):
            bechdel_ml[genre] = bechdel_ml.apply(lambda _: int(genre in _.genres), axis=1)

        train = bechdel_ml[bechdel_ml["rating"].notnull()]
        val = bechdel_ml[bechdel_ml["rating"].isnull()]
        val = val.fillna(0)
        train = train.fillna(0)
        train["rating"] = train["rating"] == 3

        self.val_title = val.pop('title')
        self.X_train = train.drop(drop_cols, axis=1)
        self.val = val.drop(drop_cols, axis=1)
        self.X_train = self.X_train.sort_values("startYear")
        self.title = self.X_train.pop('title')
        self.y = self.X_train.pop("rating")


    def triangles(self):
        triagles_gender = get_relationship_triangles()
        # triagles_gender["1"] = triagles_gender["X.0"] == "M"
        # triagles_gender["2"] = triagles_gender["X.1"] == "M"
        # triagles_gender["3"] = triagles_gender["X.2"] == "M"
        # triagles_gender["total"] = triagles_gender["1"] + triagles_gender["2"] + triagles_gender["3"]

        moive_triangle = triagles_gender.groupby(["movie", "year", "total_men"], operations={'count': agg.COUNT()})
        # type(moive_triangle)
        traingles_at_movie = moive_triangle.to_dataframe().pivot_table(index=["movie", "year"], values="count",
                                                                       columns='total_men',
                                                                       aggfunc=lambda x: x)
        traingles_at_movie = traingles_at_movie.fillna(0)

        traingles_at_movie = traingles_at_movie.reset_index()
        # bechdel_triangles = SFrame(traingles_at_movie).join(self.bechdel_imdb, {"tconst": "tconst"})
        return traingles_at_movie

    def train_val(self, additional_metrics={}):
        n_valid = 1000
        y_pred = []
        X_train, X_valid = split_vals(self.X_train, len(self.X_train) - n_valid)
        y_train, y_valid = split_vals(self.y, len(self.X_train) - n_valid)
        self.clf.fit(X_train, y_train)
        print_score(self.clf, X_train, y_train, X_valid, y_valid)
        # from sklearn.metrics import f1_score
        for k, m in additional_metrics:
            if not y_pred:
                y_pred = self.clf.predict(X_valid)
            print(f"{k}: {m(y_valid, y_pred)}")

    def train(self):
        self.clf = RandomForestClassifier(n_jobs=-1, n_estimators=100, max_depth=5, random_state=1)
        self.clf.fit(self.X_train, self.y)
        return self.clf

    def dataset_to_csv(self, path):
        pd.concat([self.X_train, self.y], axis=1).to_csv(path, index=False)


if __name__ == "__main__":
    # count_triangles()
    b = BechdelClassifier()
    b.build_dataset()
    # print(b.train_test())
    rfc = b.train()
    v = rfc.predict_proba(b.val)[:, 1]
    print(v.mean())
    b.val["decade"] = b.val["startYear"] // 10
    for y, d in b.val.groupby("decade"):
        if len(d) > 10:
            d.pop("decade")
            v = rfc.predict_proba(d)[:, 1]
            print(y, v.mean(), len(d))

    for g in genres:
        print(f"{g}:")
        x = b.val.iloc[b.val[g].nonzero()]
        for y, d in x.groupby("decade"):
            if len(d) > 10:
                d.pop("decade")
                v = rfc.predict_proba(d)[:, 1]
                print(y, v.mean(), len(d))
