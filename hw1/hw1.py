import numpy as np
import hashlib
from math import ceil
import time
from get_data import get_drug_data
import pandas as pd

shingle_size = 5

def generate_hashes(numHashes: int):
    funcs = []
    prime = 2147483647 # largest 32 bit prime
    rng = np.random.default_rng(1234)
    al = rng.integers(1, np.iinfo(np.uint32).max, size=numHashes, dtype=np.uint32).tolist()
    bl = rng.integers(0, np.iinfo(np.uint32).max, size=numHashes, dtype=np.uint32).tolist()
    for a, b in zip(al, bl):
        def make_hash(a=a, b=b):
            def h(x):
                x_u = np.uint32(x)
                return (a*x_u + b) % prime
            return h
        funcs.append(make_hash())
    return funcs

def shingle(k, doc):
    return set([hash(doc[i : i + k]) for i in range(len(doc) - k + 1)])

def shingle_md5(k, doc):
    encoded = doc.encode()
    return set([int(hashlib.md5(encoded[i : i+ k]).hexdigest()[:4], 16) for i in range(len(encoded) - k + 1)])


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


# less accurate
def fast_minhash(times, shingles):
    all_sh = np.unique(np.concatenate(shingles))
    rows = [np.isin(all_sh, sh_arr) for sh_arr in shingles]
    # row is document, column is shingle
    shingle_matrix = np.array(rows)
    k = min(times, shingle_matrix.shape[1])
    hashes = generate_hashes(k)
    # hashes for shingle n are columns, shingles are rows
    hash_vals = np.array([[hashes[i](all_sh[r]) for i in range(k)] for r in range(all_sh.shape[0])])
    signature_matrix = np.full((shingle_matrix.shape[0], k), np.inf)
    for r in range(shingle_matrix.shape[0]):
        for c in range(shingle_matrix.shape[1]):
            if shingle_matrix[r, c]:
                for i in range(signature_matrix.shape[1]):
                        signature_matrix[r, i] = min(signature_matrix[r,i], hash_vals[c, i])
    return signature_matrix


def compare(k, doc1, doc2, perms=100):
    sh1 = shingle_md5(k, doc1)
    sh2 = shingle_md5(k, doc2)

    mh = minhash(perms, [list(sh1), list(sh2)])
    same = sum([1 for i in range(len(mh)) if mh[i][0] == mh[i][1]])
    return float(same) / len(mh)

def jaccard_ndarray(nd1, nd2):
    assert nd1.shape == nd2.shape
    match_rows = sum([1 for i in range(nd1.shape[0]) if nd1[i] == nd2[i]])
    return match_rows/nd1.shape[0]
   

def minhash_many(doc_list, permutations):
    shingle_list = [list(shingle(shingle_size, doc)) for doc in doc_list]
    start = time.perf_counter()
    signature = minhash(permutations, shingle_list)
    end = time.perf_counter()
    print(f"Min Hash Time: {(end - start):.2f}ms on {len(doc_list)} documents")
    return signature


def fast_min_many(doc_list, permutations):
    shingle_list = [list(shingle_md5(shingle_size, doc)) for doc in doc_list]
    start = time.perf_counter()
    signature = fast_minhash(permutations, shingle_list)
    end = time.perf_counter()
    print(f"Fast Min Hash Time: {(end - start):.2f}ms on {len(doc_list)} documents")
    return signature


def hash_many_basic(many):
    a = 762
    b = 984747
    prime = 2147483647 # largest 32 bit prime
    return sum(a*x + b for x in many) % prime


def find_pairs(doc_list, permutations, min_thresholds): 
    sig_matrix = fast_min_many(doc_list, permutations)
    sims = []
    for threshold in min_thresholds:
        count = 0
        sim_pair = None
        for i in range(sig_matrix.shape[0]):
            for j in range(i+1, sig_matrix.shape[0]):
                if jaccard_ndarray(sig_matrix[i], sig_matrix[j]) > threshold:
                    if count == 0:
                        sim_pair = (doc_list[i], doc_list[j])
                    count += 1
        if count > 0:
            sims.append((count, sim_pair[0], sim_pair[1]))
        else: sims.append((count, "", ""))
    return sims

def find_pairs_lsh(doc_list, permutations, min_thresholds):
    sig_matrix = fast_min_many(doc_list, permutations)
    pairs = []
    for threshold in min_thresholds:
        pairs.append(lsh_pairs(sig_matrix, threshold))
    return pairs

def lsh_pairs(sig_matrix, threshold):
    band_size = threshold_to_band_size(sig_matrix.shape[1], threshold)
    # print(f"Band Size {band_size} at threshold {threshold} on {sig_matrix.shape[1]} unique shingles.")
    buckets = {} # dict to store the values the bands hash to
    # rows are docs, columns are shingles
    for r in range(sig_matrix.shape[0]):
        for c in range(0, sig_matrix.shape[1], band_size):
            vals = sig_matrix[r, c:c+band_size] if c+band_size < sig_matrix.shape[1] else sig_matrix[r, c:]
            hash = hash_many_basic(vals)
            if hash in buckets.keys():
                buckets[hash].append(r)
            else:
                buckets[hash] = [r]
    matches = []
    for pairs in buckets.values():
        if len(pairs) > 1:
            # matching set
            if jaccard_ndarray(sig_matrix[pairs[0]], sig_matrix[pairs[1]]) > threshold:
                matches.append((pairs[0], pairs[1]))
    return matches


def threshold_to_band_size(num_shingles, threshold):
    # probability of collision = 1 - (1 - t**r)**b
    # where r is band size in rows, b is number of bands, t is threshold
    for r in range(2, num_shingles+1):
        num_bands = ceil(num_shingles/r)
        p_hit = 1 - (1 - threshold**r)**num_bands
        if p_hit <= threshold:
            return r


"""
Test and benchmarking below this point
"""

def benchmark_minhash(doc_list, permutations):
    minhash_many(doc_list, permutations)
    fast_min_many(doc_list, permutations)

def basic_test():
    doc1 = "Hello, World!"
    doc2 = "hello, world!"
    sh1 = shingle_md5(3, doc1)
    sh2 = shingle_md5(3, doc2)
    signature = fast_minhash(100, [list(sh1), list(sh2)]) 
    print(f"Jaccard Fast Min Hash: {jaccard_ndarray(signature[0], signature[1])}")

    print(f"Sim. estimate: {compare(3, doc1, doc2)}")
    print(f"Jaccard: {jaccard(sh1, sh2)}")

def real_doc_test():
    perms = 20000
    doc_lists = get_drug_data()
    brc = doc_lists[0][2:4]
    shingles_fmh = [list(shingle_md5(shingle_size, doc)) for doc in brc[:2]]
    sig_fmh = fast_minhash(perms, shingles_fmh)
    print(f"Min Hash sim esitmate: {compare(shingle_size, brc[0], brc[1], perms)}")
    print(f"Jaccard Fast Min Hash: {jaccard_ndarray(sig_fmh[0], sig_fmh[1])}")
    print(f"Jaccard: {jaccard(set(shingles_fmh[0]), set(shingles_fmh[1]))}")

def real_doc_test_many():
    perms = 1000
    doc_lists = get_drug_data()
    naive_err = []
    fmh_err = []
    for i in range(102):
        brc = doc_lists[0][i:i+2]
        shingles_fmh = [list(shingle_md5(shingle_size, doc)) for doc in brc[:2]]
        sig_fmh = fast_minhash(perms, shingles_fmh)
        actual = jaccard(set(shingles_fmh[0]), set(shingles_fmh[1]))
        naive_err.append(abs(compare(shingle_size, brc[0], brc[1], perms) - actual))
        fmh_err.append(abs(jaccard_ndarray(sig_fmh[0], sig_fmh[1]) - actual))
    print(f"FMH Mean Err: {sum(fmh_err)/len(fmh_err)}")
    print(f"Naive Err: {sum(naive_err)/len(naive_err)}")

def pair_find_benchmark(doc_list, permutations, thresholds):
    start = time.perf_counter()
    naive_pairs = find_pairs(doc_list, permutations, thresholds)
    time_basic = time.perf_counter() - start
    print(f"\nNaive Runtime: {time_basic:.2f}s")

    start_lsh = time.perf_counter()
    lsh_pairs = find_pairs_lsh(doc_list, permutations, thresholds)
    time_lsh = time.perf_counter() - start_lsh
    print(f"LSH Runtime: {time_lsh:.2f}s")

    print()
    table = []
    for i, t in enumerate(thresholds):
        table.append([t, naive_pairs[i][0], len(lsh_pairs[i])])
    
    df = pd.DataFrame(table, columns=['theshold', 'naive pairs', 'lsh pairs'])
    print(df.to_string(index=False))


if __name__ == "__main__":
    thresholds = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5]
    # basic_test()
    # real_doc_test_many()
    doc_lists = get_drug_data()
    docs = []
    for doc in doc_lists[0]:
        if type(doc) == type('sr') and len(doc) >= shingle_size:
            docs.append(doc)
    # benchmark_minhash(docs, 300)
    pairs = find_pairs_lsh(docs[:400], 10000, thresholds)
    lines = []
    for i, thr in enumerate(thresholds):
        lines.append(f"----------------- Threshold: {thr*100}% -----------------")
        for k, pair in enumerate(pairs[i]):
            if i >= 10:
                break
            lines.append("\nDocument A:\n")
            lines.append(docs[pair[0]])
            lines.append("\nDocument B:\n")
            lines.append(docs[pair[1]])
            lines.append("\n\n")
    with open("matching_docs.txt", 'w') as f:
        f.writelines(lines)
    # print("Benchmarking pair algos")
    # pair_find_benchmark(docs[:100], 10000, thresholds)