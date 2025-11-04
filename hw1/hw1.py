import numpy as np
from functools import reduce
import hashlib
from math import pow
import time
from get_data import get_drug_data

shingle_size = 5

def generate_hashes(numHashes: int):
    funcs = []
    prime = 2147483647 # larget 32 bit prime
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
    # currently case-sensitive
    # each hash is 32 bits
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

# should be less accurate I think??? 
def fastminhash(times, shingles):
    all_sh = np.unique(np.concatenate(shingles))
    rows = [np.isin(all_sh, sh_arr) for sh_arr in shingles]
    # row is document, column is shingle
    shingle_matrix = np.array(rows)
    k = times #k = min(times, shingle_matrix.shape[1]) # fix later
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
        
# this one hashes index instead of shingle... (as per the docs)
def fastminhashindex(times, shingles):
    all_sh = np.unique(np.concatenate(shingles))
    rows = [np.isin(all_sh, sh_arr) for sh_arr in shingles]
    # row is document, column is shingle
    shingle_matrix = np.array(rows)
    k = times #k = min(times, shingle_matrix.shape[1]) # fix later
    hashes = generate_hashes(k)
    # hashes for shingle n are columns, shingles are rows
    hash_vals = np.array([[hashes[i](r) for i in range(k)] for r in range(all_sh.shape[0])])
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
   
def minhashmany(doc_list, permutations):
    shingle_list = [list(shingle(shingle_size, doc)) for doc in doc_list]
    start = time.perf_counter()
    signature = minhash(permutations, shingle_list)
    end = time.perf_counter()
    print(f"Min Hash Time ms: {(end - start)} on {len(doc_list)} documents")


def fastminmany(doc_list, permutations):
    shingle_list = [list(shingle_md5(shingle_size, doc)) for doc in doc_list]
    start = time.perf_counter()
    signature = fastminhash(permutations, shingle_list)
    end = time.perf_counter()
    print(f"Fast Min Hash Time ms: {(end - start)} on {len(doc_list)} documents")
    return signature

def fastminindexmany(doc_list, permutations):
    shingle_list = [list(shingle_md5(shingle_size, doc)) for doc in doc_list]
    start = time.perf_counter()
    signature = fastminhashindex(permutations, shingle_list)
    end = time.perf_counter()
    print(f"Fast Min Hash Index Time ms: {(end - start)} on {len(doc_list)} documents")

def find_pairs(doc_list, permutations, min_thresholds): 
    sig_matrix = fastminmany(doc_list, permutations)
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
                    else: count += 1
        if count > 0:
            sims.append((count, sim_pair[0], sim_pair[1]))
        else: sims.append((count, "", ""))
    for sim in sims:
        print(f"Similar Count: {sim[0]}\n Doc 1: {sim[1]} \n Doc 2: {sim[2]}")


"""
Test and benchmarking below this point
"""

def benchmark_minhash(doc_list, permutations):
    minhashmany(doc_list, permutations)
    fastminmany(doc_list, permutations)
    # fastminindexmany(doc_list, permutations)

def basic_test():
    doc1 = "Hello, World!"
    doc2 = "hello, world!"
    # br, ser, cr = get_drug_data()
    # doc1 = br[0]
    # doc2 = br[1]
    sh1 = shingle(3, doc1)
    sh2 = shingle(3, doc2)
    sh1_m5 = shingle_md5(3, doc1)
    sh2_m5 = shingle_md5(3, doc2)
    signature = fastminhash(100, [list(sh1_m5), list(sh2_m5)]) 
    print(f"Jaccard Fast Min Hash: {jaccard_ndarray(signature[0], signature[1])}")

    # print(f"Minhash:\n{minhash(10, [list(sh1), list(sh2)])}")
    print(f"Sim. estimate: {compare(3, doc1, doc2)}")
    print(f"Jaccard: {jaccard(sh1, sh2)}")

def real_doc_test():
    perms = 100000
    doc_lists = get_drug_data()
    brc = doc_lists[0][0:2]
    shingles_fmh = [list(shingle_md5(shingle_size, doc)) for doc in brc[:2]]
    sig_fmh = fastminhash(perms, shingles_fmh)
    # sig_fmhi = fastminhashindex(perms, shingles_fmh) # always shoots high and isn't faster
    print(f"Min Hash sim esitmate: {compare(shingle_size, brc[0], brc[1], perms)}")
    print(f"Jaccard Fast Min Hash: {jaccard_ndarray(sig_fmh[0], sig_fmh[1])}")
    # print(f"Jaccard Fast Min Index Hash: {jaccard_ndarray(sig_fmhi[0], sig_fmhi[1])}")
    print(f"Jaccard: {jaccard(set(shingles_fmh[0]), set(shingles_fmh[1]))}")



if __name__ == "__main__":
    # print("Running Basic Test")
    # basic_test()
    # print("Test on a pair of real documents")
    # real_doc_test()
    # print("Running Many Benchmark")
    doc_lists = get_drug_data()
    docs = []
    for doc in doc_lists[0]:
        if type(doc) == type('sr') and len(doc) >= shingle_size:
            docs.append(doc)
    # benchmark_minhash(docs, 100)
    print("Finding pairs")
    find_pairs(docs[:400], 100, [0.05, 0.1, 0.2, 0.3, 0.4, 0.5])