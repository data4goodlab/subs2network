from subs2graph.videos_sn_creator import get_best_directors

if __name__ == "__main__":
    get_best_directors()
    # try:
    #     # print(get_directors_data().head(100))
    #     get_best_directors()
    #     # test_get_movie("Fight Club", 1999, "0137523", {"averageRating": 8.8})
    #
    #     # get_best_movies()
    # #     test_get_movie("The Usual Suspects", 1995, "0114814", {"averageRating": 8.6})
    # #     # test_get_series("Friends", "0108778", set(range(1, 11)), set(range(1, 30)))
    # #     # test_get_director_movies("Quentin Tarantino")
    # #     # test_get_actor_movies("Brendan Fraser")
    # #     # v = VideosSnCreator()
    # #     # name = "Modern Family"
    # #     # v.save_series_graphs(name, "95011" ,set(range(1,7)), set(range(1,25)),"/temp/series/%s/subtitles" % name,
    # #     # "{TEMP_PATH}/series/%s/csv" % name, draw_graph_path="{TEMP_PATH}/series/%s/graphs" % name)
    # except Exception as e:
    #     send_email("dimakagan15@gmail.com", "Subs2Graph Code Crashed & Exited", traceback.format_exc())
    # finally:
    #     send_email("dimakagan15@gmail.com", "Subs2Graph Code Finished", "Code Finished")
