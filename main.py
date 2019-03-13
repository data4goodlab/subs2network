import traceback
from subs2graph.consts import DEBUG
from subs2graph.utils import send_email
from subs2graph.videos_sn_creator import get_best_directors, get_best_movies, get_worst_movies, generate_movie_graph, \
    get_popular_movies, get_popular_actors, generate_actor_movies_graphs, load_black_list, generate_actors_file, \
    get_bechdel_movies, generate_blacklist_roles, get_movies_by_character, get_movies_by_title
import cProfile
if __name__ == "__main__":
    try:

        # ignore_roles_names = load_black_list()
        # test_get_actor_movies("Ben Foster", ignore_roles_names, ["actor"])
        # generate_actors_file()
        # generate_blacklist_roles()
        # generate_actors_file()
        # get_bechdel_movies()
        # get_movies_by_character("James Bond", True)
        get_movies_by_title("Star Wars", True)
        generate_movie_graph("The Godfather", 1972, "0068646", {"averageRating": 9.2})
        # get_popular_movies(resume=True)
        # get_best_directors()
    except Exception as e:
        if not DEBUG:
            send_email("dimakagan15@gmail.com", "Subs2Graph Code Crashed & Exited", traceback.format_exc())
        else:
            raise e
    if not DEBUG:
        send_email("dimakagan15@gmail.com", "Subs2Graph Code Finished", "Code Finished")
