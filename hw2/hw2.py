def support(baskets):
    pass


def singletons(baskets):
    return {s for basket in baskets for s in basket}


def candidate(baskets, k, s, singletons):
    k_1_tuples = candidate(baskets, k - 1, s, singletons)
    k_tuples = set()
    for t1 in k_1_tuples:
        for t2 in singletons:
            if t1 != t2:
                k_tuples.add(tuple(sorted(t1 + t2)))
    return k_tuples


if __name__ == "__main__":
    baskets = [{"a", "b", "c"}, {"b", "d", "e"}, {"a", "b", "d"}]
    s = singletons(baskets)
    candidate(baskets, 3, 0.5, s)
