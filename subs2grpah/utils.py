def add_prefix_to_dict_keys(d, prefix, sep="-"):
    h = {}
    for k, v in d.iteritems():
        h[prefix + sep + k] = v
    return h



