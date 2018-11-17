import os
from dotenv import load_dotenv
load_dotenv()


IMDB_CAST = "cast"
IMDB_NAME = "name"
MIN_NAME_SIZE = 2
SRC_ID = "src_id"
DST_ID = "dst_id"
WEIGHT = "weight"

SUBTITLE_SLEEP_TIME = 3

EPISODE_ID = "id"
EPISODE_NAME = "title"
EPISODE_NUMBER = "episode"
EPISODE_RATING = "rating"
SEASON_ID = "seasonid"
SEASON_NUMBER = "SeasonNumber"
DVD_SEASON = "DVD_season"
DVD_EPISODE = "DVD_episodenumber"
SERIES_ID = "seriesid"
EPISODE_GUEST_STARTS = "GuestStars"
SERIES_NAME = "Series_name"
IMDB_ID = "imdb_id"
VIDEO_NAME = "movie_name"
IMDB_RATING = "imdb_rating"
SUBTITLE_PATH = "subtitle_path"
ROLES_PATH = "roles_path"
MOVIE_YEAR = "movie_year"
ROLES_GRAPH = "roles_graph"
ACTORS_GRAPH = "actors_graph"
MAX_YEAR = 2018
TEMP_PATH = f"{os.getenv('RELATIVE_PATH')}temp"
DATA_PATH = f"{os.getenv('RELATIVE_PATH')}data"
THE_TVDB_URL = r"http://thetvdb.com/data/series/%s/all/en.xml"

IMDB_NAMES_URL = "https://datasets.imdbws.com/name.basics.tsv.gz"
IMDB_TITLES_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
IMDB_CREW_URL = "https://datasets.imdbws.com/title.crew.tsv.gz"
IMDB_RATING_URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"

STANFORD_NLP_MODEL = f"{os.getenv('RELATIVE_PATH')}ner/classifiers/english.all.3class.distsim.crf.ser.gz"
STANFORD_NLP_JAR = f"{os.getenv('RELATIVE_PATH')}ner/stanford-ner.jar"
DEBUG = os.getenv('DEBUG') == 'True'
