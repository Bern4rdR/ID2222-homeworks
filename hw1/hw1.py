import numpy as np
from functools import reduce


def shingle(k, doc):
    # currently case-sensitive
    # each hash is 32 bits
    return set([hash(doc[i : i + k]) for i in range(len(doc) - k + 1)])


def jaccard(shing1, shing2):
    intersection = len(shing1.intersection(shing2))
    union = len(shing1.union(shing2))
    return intersection / union


def minhash(times, shingles):
    all_sh = np.unique(np.concatenate(shingles))

    # create single matrix
    rows = [np.isin(all_sh, sh_arr) for sh_arr in shingles]
    shingle_matrix = np.array(rows)  # bool matrix

    # create signature matrix
    sig_matrix = [[] for _ in range(times)]
    for p in range(times):
        perm = np.random.permutation(range(len(shingle_matrix[0])))
        for s in range(len(shingles)):
            for i in perm:
                if shingle_matrix[s][i]:
                    sig_matrix[p].append(i)
                    break

    return np.array(sig_matrix)


def compare(k, doc1, doc2, perms=100):
    sh1 = shingle(k, doc1)
    sh2 = shingle(k, doc2)

    mh = minhash(perms, [list(sh1), list(sh2)])
    same = sum([1 for i in range(len(mh)) if mh[i][0] == mh[i][1]])

    return float(same) / len(mh)


if __name__ == "__main__":
    doc1 = "Hello, World!"
    doc2 = "hello, world!"
    sh1 = shingle(3, doc1)
    sh2 = shingle(3, doc2)

    print(f"Minhash:\n{minhash(10, [list(sh1), list(sh2)])}")
    print(f"Sim. estimate: {compare(3, doc1, doc2)}")
    print(f"Jaccard: {jaccard(sh1, sh2)}")
