import glob
import os
from networkx.readwrite import json_graph
import json
import networkx as nx
import pandas as pd

from subs2graph.utils import add_prefix_to_dict_keys
from subs2graph.imdb_dataset import imdb_data
from subs2graph.consts import MOVIE_YEAR

def get_node_features(g):
    closeness = nx.closeness_centrality(g)
    betweenness = nx.betweenness_centrality(g)
    betweenness_weight = nx.betweenness_centrality(g, weight="weight")
    degree_centrality = nx.degree_centrality(g)
    pr = nx.pagerank(g, weight=None)
    pr_weight = nx.pagerank(g, weight="weight")
    clustering = nx.clustering(g)
    for v in g.nodes():
        res = {}
        res["total_weight"] = g.degree(v, weight="weight")
        res["degree"] = g.degree(v)
        res["movie_name"] = g.graph["movie_name"]
        res["year"] = g.graph["movie_year"]
        res["imdb_rating"] = g.graph["imdb_rating"]
        res["closeness"] = closeness[v]
        res["betweenness_weight"] = betweenness_weight[v]
        res["betweenness"] = betweenness[v]
        res["degree_centrality"] = degree_centrality[v]
        res["clustering"] = clustering[v]
        res["pagerank"] = pr[v]
        res["pr_weight"] = pr_weight[v]
        res["gender"] = imdb_data.get_actor_gender(v)
        res["name"] = v
        yield res


def get_actor_features(g, actor):
    res = {}
    closeness = nx.closeness_centrality(g)
    betweenness = nx.betweenness_centrality(g)
    betweenness_weight = nx.betweenness_centrality(g, weight="weight")
    degree_centrality = nx.degree_centrality(g)
    clustering = nx.clustering(g)
    pr = nx.pagerank(g, weight=None)
    pr_weight = nx.pagerank(g)

    v = actor
    res["total_weight"] = g.degree(v, weight="weight")
    res["degree"] = g.degree(v)
    res["closeness"] = closeness[v]
    res["betweenness"] = betweenness[v]
    res["betweenness_weight"] = betweenness_weight[v]
    res["degree_centrality"] = degree_centrality[v]
    res["clustering"] = clustering[v]
    res["movie_rating"] = g.graph["imdb_rating"]
    res["pagerank"] = pr[v]
    res["pagerank_weight"] = pr_weight[v]

    # res["gender"] = imdb_data.get_actor_gender(v)
    return res


def average_graph_weight(g):
    stats = pd.Series(list(nx.get_edge_attributes(g, "weight").values())).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "weight")


def average_graph_degree(g):
    stats = pd.Series([d for n, d in nx.degree(g, g.nodes())]).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "degree")


def average_actor_appearance(g):
    stats = pd.Series([g.degree(v, weight="weight") for v in g.nodes()]).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "appearance")


def average_closeness_centrality(g):
    stats = pd.Series(list(nx.closeness_centrality(g).values())).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "closeness")


def average_eigenvector_centrality(g):
    stats = pd.Series(list(nx.eigenvector_centrality(g).values())).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "eigenvector")


def average_betweenness_centrality(g):
    stats = pd.Series(list(nx.betweenness_centrality(g).values())).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "betweenness")

def average_pagerank(g):
    stats = pd.Series(list(nx. nx.pagerank(g,weight=None).values())).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "pagerank")

def average_weighted_pagerank(g):
    stats = pd.Series(list(nx. nx.pagerank(g, weight="weight").values())).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "weighted_pagerank")



def average_weighted_betweenness_centrality(g):
    stats = pd.Series(list(nx.betweenness_centrality(g).values())).describe()
    del stats["count"]
    return add_prefix_to_dict_keys(stats.to_dict(), "weighted_betweenness")

def average_clustering(g):
    try:
        return {"average_clustering": nx.average_clustering(g)}
    except:
        return {"average_clustering": 0}


def average_weighted_clustering(g):
    try:
        return {"average_weighted_clustering": nx.average_clustering(g, weight="weight")}
    except:
        return {"average_clustering": 0}

def graph_clique_number(g):
    return {"clique_number": nx.graph_clique_number(g)}


def average_degree_connectivity(g):
    return {"average_degree_connectivity": nx.average_degree_connectivity(g)}


def get_edge_number(g):
    return {"edge_number": len(g.edges)}


def get_node_number(g):
    return {"node_number": len(g.node)}


def analyze_movies():

    p = "../temp/movies/"
    res = []
    for movie in tqdm(os.listdir(p)):
        path = os.path.join(p, movie)
        g_pth = os.path.join(path, f"json/{movie}.json")
        if not os.path.exists(g_pth):
            g_pth = glob.glob(os.path.join(path, f"json/*.json"))
            if g_pth: g_pth = g_pth[0]
        if g_pth:
            # try:
            with open(g_pth) as f:
                g = json_graph.node_link_graph(json.load(f))
                if g.number_of_nodes() == 0:
                    continue
                d = extract_graph_features(g)
            #
            # with open(os.path.join(path, f"{movie}.json")) as f:
            #     movie_info = json.load(f)
            #     d.update(json.loads(movie_info))
            res.append(d)
            # except:
            #     pass
        # else:
        #     print(movie)
    pd.DataFrame(res).to_csv(f"../temp//graph_features.csv", index=False)


def analyze_directors():
    p = "../temp/directors/"
    for director in os.listdir(p):
        res = []
        json_path = os.path.join(p, director, "json")
        graphs = []
        for g_pth in glob.glob(os.path.join(json_path, f"*roles*")):

            if g_pth:
                try:
                    with open(g_pth) as f:
                        g = json_graph.node_link_graph(json.load(f))
                        d = extract_graph_features(g)
                        d.update({"rating": g.graph["imdb_rating"], "year": g.graph["movie_year"],
                                  "name": g.graph["movie_name"]})
                        graphs.append(g)
                    res.append(d)
                except:
                    pass
        if graphs:
            joined_grpah = nx.compose_all(graphs)
            d = extract_graph_features(joined_grpah)
            d["name"] = "combined"
            res.append(d)
        pd.DataFrame(res).to_csv(f"../temp/output/{director}.csv", index=False)


def get_triangles(g):
    all_cliques = nx.enumerate_all_cliques(g)
    return [x for x in all_cliques if len(x) == 3]


def analyze_triangles():
    p = "../temp/movies/"
    res = []
    json_path = os.path.join(p, "*", "json")
    for g_pth in tqdm(glob.glob(os.path.join(json_path, f"*roles.json"))):
        if g_pth:
            with open(g_pth) as f:
                g = json_graph.node_link_graph(json.load(f))
                tr = get_triangles(g)
            for t in tr:
                t.append(g.graph["movie_name"].replace(" - roles",""))
                t.append(g.graph["movie_year"])
            res += tr

    pd.DataFrame(res).to_csv(f"../temp/triangles.csv")


def analyze_genders():
    p = "../temp/movies/"
    res = []
    json_path = os.path.join(p, "*", "json")
    for g_pth in tqdm(glob.glob(os.path.join(json_path, f"*roles.json"))):

        if g_pth:
            with open(g_pth) as f:
                g = json_graph.node_link_graph(json.load(f))
                if g.number_of_nodes() > 5:
                    d = get_node_features(g)
                    res += list(d)

    pd.DataFrame(res).to_csv(f"../temp/gender.csv")


def extract_graph_features(g):
    d = {}
    d.update(get_edge_number(g))
    d.update(get_node_number(g))
    d.update(average_actor_appearance(g))
    d.update(average_closeness_centrality(g))
    d.update(average_clustering(g))
    d.update(average_weighted_clustering(g))
    d.update(average_betweenness_centrality(g))
    d.update(average_weighted_betweenness_centrality(g))
    # d.update(average_eigenvector_centrality(g))
    d.update(average_pagerank(g))
    d.update(average_weighted_pagerank(g))
    d.update(average_graph_degree(g))
    d.update(average_graph_weight(g))
    d.update(average_clustering(g))
    d.update(graph_clique_number(g))
    genders = get_genders_in_graph(g)
    d["m_count"] = genders.count("M")
    d["f_count"] = genders.count("F")
    d["movie_name"] = g.graph["movie_name"].replace(" - roles","")
    d["year"] = g.graph["movie_year"]
    d["imdb_rating"] = g.graph["imdb_rating"]
    return d


from tqdm import tqdm


def create_pdf():
    from PIL import Image
    from PIL import ImageFont
    from PIL import ImageDraw
    # imagelist is the list with all image filenames
    p = "../temp/movies/"
    res = []

    for i, movie in enumerate(tqdm(os.listdir(p), total=len(os.listdir(p)))):

        path = os.path.join(p, movie)
        image = glob.glob(os.path.join(path, f"graphs/*({'[0-9]'*4}).png"))
        if image:
            img = Image.open(image[0]).convert("RGB")
            draw = ImageDraw.Draw(img)
            # font = ImageFont.truetype(<font-file>, <font-size>)
            font = ImageFont.truetype("arial.ttf", 50)
            # draw.text((x, y),"Sample Text",(r,g,b))
            draw.text((10, 10), movie, (0, 0, 0), font=font)
            res.append(img)

    res[0].save("test4.pdf", "PDF", resolution=100.0, save_all=True, append_images=res[1:], quality=60, optimize=True)


def add_gender_to_graph(movie, is_roles=True):
    p = "../temp/movies/"
    json_path = os.path.join(p, movie, "json")
    if is_roles:
        graph_paths = glob.glob(os.path.join(json_path, f"*roles*"))[0]
    else:
        graph_paths = glob.glob(os.path.join(json_path, f"*{movie}.json"))
    imdb_data.actors_gender
    for graph_path in graph_paths:
        with open(graph_path) as f:
            g = json_graph.node_link_graph(json.load(f))
            for v in g.nodes():
                if is_roles:
                    g.node[v]["gender"] = imdb_data.get_actor_gender(v)
                else:
                    g.node[v]["gender"] = imdb_data.get_actor_gender(g.node[v]['role'])
        data = json_graph.node_link_data(g)
        json_path = f"../temp/({g.graph[MOVIE_YEAR]}) - {movie}.json"
        with open(json_path, 'w') as fp:
            json.dump(data, fp)


def gender_in_top_movies():
    p = "../temp/movies/"
    movies = imdb_data.get_movies_data()
    for m in tqdm(movies):
        gender = []
        movie_name = m['primaryTitle'].replace('.', '').replace('/', '')
        json_path = os.path.join(p, movie_name, "json")
        try:
            graph_path = glob.glob(os.path.join(json_path, f"*roles.json"))[0]
            with open(graph_path) as f:
                g = json_graph.node_link_graph(json.load(f))
                yield get_genders_in_graph(g)
        except IndexError:
            pass


def get_genders_in_graph(g):
    return [imdb_data.get_actor_gender(v) for v in g.nodes()]


if __name__ == "__main__":
    # gender_in_top_movies()
    # add_gender_to_graph("The Social Network", False)
    analyze_triangles()
    # analyze_genders()
    # analyze_directors()
    # create_pdf()
    # analyze_movies()
    # analyze_movies()
