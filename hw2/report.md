# Homework 2
November 10 or whatever

### Authors
Bernard Rumar -- [bernardr@kth.se](mailto:bernardr@kth.se)

Vivienne Curewitz -- [curewitz@kth.se](mailto:curewitz@kth.se)

## Datasets used
We used the dataset provided in the assignment which can be downloaded from canvas. https://canvas.kth.se/courses/57474/files/9553410/download?download_frd=1

## Solution
We implement APrioi in python, using no framework. There are really just 3 steps in the algorithm:
1. Find the singletons and create a data structure to count them.
    a. This is trivial for the provided dataset, as the singletons provided are integers between 0 and 999, so the counter is just an array where the singleton is the index value for the count.

2. Generate the initial 2-ton with the first pass; count all singleton and generate pairs with the singletons with support above the threshold

3. Generate k-tons to a limit; find all (k-1)tons with support > threshold, and use those to create a new candidate set. Testing the K-tons is the slowest part of the algo, se we parallelized it.

    ```def init_pool(baskets_):
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
        return passing_candidates```

The pipeline body is shown below. We can iterate to the desired k in kton with this loop:
    

    ```def pipeline(baskets, threshold, max_k_ton):
        # first pass, then n passes
        count_init = [0 for x in range(1000)]
        singletons = [i for i, x in enumerate(fast_count_items(baskets, count_init)) if x/len(baskets) > threshold]
        candidate_kton = candidates_singletons(singletons)
        print(f"Candidates sample :: \n {candidate_kton[:10]}\n Total Candidate Pairs: {len(candidate_kton)}")
        # n passes
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
        pipeline(baskets=baskets, threshold=0.02, max_k_ton=4) #375 meet this thresh, 70125 candidate pairs for theshold 0.01```


## Installation
We developed in python 3.12. Run "pip install -r requirements.txt".

## Results
We are able to capture k-tons fairly quickly up to 4-tons:
Log output
    ```Candidates sample :: 
    [{8, 6}, {12, 6}, {21, 6}, {27, 6}, {32, 6}, {38, 6}, {6, 39}, {48, 6}, {54, 6}, {57, 6}]
    2-ton
    Total Candidate Pairs: 11935
    Passing Candidates: 187, {32, 6} in 28.068102500998066 s
    3-ton
    Generated 28611 in 0.014186919004714582 s
    Passing Candidates: 72, {32, 6, 472} in 63.044519989001856 s
    4-ton
    Generated 10944 in 0.006440669996663928 s
    Passing Candidates: 24, {120, 593, 862, 895} in 26.31630003099417 s```

The above log used a higher support threshold for the singletons to artificially shrink the runtime. There were 155 singletons; which produces 11935 initial candidate pairs - (N**2 - N)/2. 187 pairs pass the support threshold (which is lowered to 0.005 for the rest of the test), and this becomes 28611 candidate 3-tons - N*(S-2) = 187*(155-2), 72 of which are above the support threshold, and this becomes 72*(155-3) = 10944 Candidate 4-tons, of which 24 pass the threshold.
## Benchmarks
Using 10 processes is faster than using 1.
