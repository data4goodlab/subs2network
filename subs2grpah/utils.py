def add_prefix_to_dict_keys(d, prefix, sep="-"):
    h = {}
    if type(d) is dict:
        d = d.items()
    for k, v in d:
        h[prefix + sep + k] = v
    return h



