import traceback
from subs2network.consts import DEBUG
from subs2network.utils import send_email
from subs2network.videos_sn_creator import get_best_directors, get_best_movies, get_worst_movies, generate_movie_graph, \
    get_popular_movies, get_popular_actors, generate_actor_movies_graphs, get_black_list, generate_actors_file, \
    get_bechdel_movies, generate_blacklist_roles, get_movies_by_character, get_movies_by_title

if __name__ == "__main__":
    try:

        # ignore_roles_names = load_black_list()
        # test_get_actor_movies("Ben Foster", ignore_roles_names, ["actor"])
        # generate_actors_file()
        # generate_blacklist_roles()
        # generate_actors_file()
        # get_bechdel_movies()
        # get_movies_by_character("James Bond", True)
        # get_movies_by_title("Star Wars", True)
        generate_movie_graph("The Innkeepers", 2011, "1594562", {"averageRating": 5.5})

        # get_popular_movies(resume=True)
        # get_best_directors()
    except Exception as e:
        if not DEBUG:
            send_email("dimakagan15@gmail.com", "subs2network Code Crashed & Exited", traceback.format_exc())
        else:
            raise e
    if not DEBUG:
        send_email("dimakagan15@gmail.com", "subs2network Code Finished", "Code Finished")
