import traceback
from subs2graph.consts import DEBUG
from subs2graph.utils import send_email
from subs2graph.videos_sn_creator import get_best_directors, get_best_movies, get_worst_movies, test_get_movie, \
    get_popular_movies, get_popular_actors, test_get_actor_movies, load_black_list, generate_actors_file, \
    get_bechdel_movies, generate_blacklist_roles, get_movies_by_character, get_movies_by_title

if __name__ == "__main__":
    try:
        from fuzzywuzzy.fuzz import token_set_ratio

        # ignore_roles_names = load_black_list()
        # test_get_actor_movies("Ben Foster", ignore_roles_names, ["actor"])
        # generate_actors_file()
        # generate_blacklist_roles()

        # get_bechdel_movies()
        # get_movies_by_character("James Bond", True)
        # get_movies_by_title("Star Wars", True)
        # test_get_movie("The Phantom of the Opera at the Royal Albert Hall", 2011, "2077886",  {"averageRating": 8.8})
        get_popular_movies()
        # get_best_directors()
    except Exception as e:
        if not DEBUG:
            send_email("dimakagan15@gmail.com", "Subs2Graph Code Crashed & Exited", traceback.format_exc())
        else:
            raise e
    if not DEBUG:
        send_email("dimakagan15@gmail.com", "Subs2Graph Code Finished", "Code Finished")
