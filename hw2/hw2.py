from get_data import load_baskets
from hashlib import md5 #make professor happy, not sure if actually necessary
from multiprocessing import Pool, Queue
from time import perf_counter

_baskets = None

def support(baskets):
    pass


def singletons(baskets):
    return {s for basket in baskets for s in basket}

# I don't think this terminates, but maybe I don't understand it
def candidate(baskets, k, s, singletons):
    k_1_tuples = candidate(baskets, k - 1, s, singletons)
    k_tuples = set()
    for t1 in k_1_tuples:
        for t2 in singletons:
            if t1 != t2:
                k_tuples.add(tuple(sorted(t1 + t2)))
    return k_tuples

# second attempt for k-tons where k > 2
# expect M*(S - K) where M is size of previous candidate list
# S is number of singletons and K is the K-ton of the prev_candidates
# should be S - K because K singletons will already be in the candidate
def candidates(prev_candidates, singletons):
    new_cands = []
    for pc in prev_candidates:
        for si in singletons:
            if si not in pc:
                new_cands.append(pc | {si})
    return new_cands

# I believe this is a special case, (N(N-1))/2 candidates
# generates the first 2-ton candidate list from just the singletons
def candidates_singletons(singletons):
    new_cands = []
    for i, pc in enumerate(singletons):
        if i + 1 == len(singletons):
            break
        for si in singletons[i+1:]:
            new_cands.append({pc, si})
    return new_cands

# this is probably as fast as this itemset is going to get, change my mind
def fast_count_items(baskets: list[set[int]], results_arr: list[int]):
    for bk in baskets:
        for item in bk:
            results_arr[item] += 1
    return results_arr

# make this faster
# count_kton and count_kton_pool are identical, but pool is parallelized and runs much faster.
# really easy to parallelize this one so might as well
# however it is easier to debug the serial one
def count_kton(baskets: list[set[int]], ktons: list[set[int]], threshold):
    passing_candidates = []
    step = 1
    for i, kt in enumerate(ktons):
        count = 0
        for bk in baskets:
            if kt.issubset(bk):
                count += 1
        if count/len(baskets) > threshold:
            passing_candidates.append(kt) 
        if i/len(ktons)*100 > step:
            print(f"{step}% complete.")
            step += 1
    return passing_candidates

def init_pool(baskets_):
    global _baskets
    _baskets = baskets_

def ktf(k_args):
    kt, threshold = k_args
    count = 0
    for bk in _baskets:
        if kt.issubset(bk):
            count += 1
    return (count/len(_baskets) > threshold, kt)

def count_kton_pool(baskets: list[set[int]], ktons: list[set[int]], threshold):
    passing_candidates = []
    with Pool(10, initializer=init_pool, initargs=(baskets,)) as p: #I have 12 logical threads, these should be like 99% the whole time so no need to go past number threads in cpu
        passing_candidates = p.map(ktf, [(kt, threshold) for kt in ktons])
    # run pool
    return passing_candidates

# max is 999, min is 0 so this is easy
def sanity_check(baskets: list[list[int]]):
    mmax = 0
    mmin = 1000
    for bk in baskets:
        mmax = mmax if mmax > max(bk) else max(bk)
        mmin = mmin if mmin < min(bk) else min(bk)
    print(f"Max {mmax} Min {mmin}")

def pipeline(baskets, threshold, max_k_ton):
    # first pass, then n passes
    count_init = [0 for x in range(1000)]
    singletons = [i for i, x in enumerate(fast_count_items(baskets, count_init)) if x/len(baskets) > threshold]
    candidate_kton = candidates_singletons(singletons)
    print(f"Candidates sample :: \n {candidate_kton[:10]}\n Total Candidate Pairs: {len(candidate_kton)}")
    for i in range(2, max_k_ton + 1):
        check_start = perf_counter()
        remaining = [x[1] for x in count_kton_pool(baskets, candidate_kton, 0.005) if x[0]] # setting threshold low to test
        pool_time = perf_counter() - check_start
        print(f"Passing Candidates: {len(remaining)}, {remaining[0]} in {pool_time} s")
        c_gen_start = perf_counter()
        candidate_kton = candidates(remaining, singletons)
        c_gen_time = perf_counter() - c_gen_start
        print(f"Generated {len(candidate_kton)} in {c_gen_time} s")


if __name__ == "__main__":
    # sanity_check(load_baskets())
    baskets = load_baskets()
    count_init = [0 for x in range(1000)]
    pipeline(baskets=baskets, threshold=0.02, max_k_ton=4) #375 meet this thresh, 70125 candidate pairs for theshold 0.01