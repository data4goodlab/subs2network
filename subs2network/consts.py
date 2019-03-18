import os
from dotenv import load_dotenv

load_dotenv()

IMDB_CAST = "cast"
IMDB_NAME = "name"
MIN_NAME_SIZE = 0
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
dirname, filename = os.path.split(os.path.abspath(__file__))
THE_TVDB_URL = r"http://thetvdb.com/data/series/%s/all/en.xml"

IMDB_NAMES_URL = "https://datasets.imdbws.com/name.basics.tsv.gz"
IMDB_TITLES_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
IMDB_CREW_URL = "https://datasets.imdbws.com/title.crew.tsv.gz"
IMDB_RATING_URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"
IMDB_PRINCIPALS_URL = "https://datasets.imdbws.com/title.principals.tsv.gz"

BASE_DIR_NAME = ".subs2net"

BASEPATH = os.path.expanduser(os.path.join('~', BASE_DIR_NAME))
if not os.path.exists(BASEPATH):
    os.mkdir(BASEPATH)
    os.mkdir(f"{BASEPATH}/data")
    os.mkdir(f"{BASEPATH}/subtitles")
    os.mkdir(f"{BASEPATH}/output")
    os.mkdir(f"{BASEPATH}/ner")

OUTPUT_PATH = f"{BASEPATH}/output"
DATA_PATH = f"{BASEPATH}/data"
STANFORD_NLP_MODEL = f"{BASEPATH}/ner/english.all.3class.distsim.crf.ser.gz"
STANFORD_NLP_JAR = f"{BASEPATH}/ner/stanford-ner.jar"
STANFORD_NLP_JAR_URL = "https://github.com/data4goodlab/subs2network/raw/master/ner/stanford-ner.jar"
STANFORD_NLP_MODEL_URL = "https://github.com/data4goodlab/subs2network/raw/master/ner/classifiers/english.all.3class.distsim.crf.ser.gz"
DEBUG = True
