# Homework 1
November 10

### Authors
Bernard Rumar -- [bernardr@kth.se](mailto:bernardr@kth.se)

Vivienne Curewitz -- [curewitz@kth.se](mailto:curewitz@kth.se)

## Datasets used
- [Druglip](https://archive.ics.uci.edu/static/public/461/drug+review+dataset+druglib+com.zip)
  - the correct dataset will be automatically downloaded during the first execution of the program


## Installation
1. Run `pip install -r requirements.txt` to install the required packages
2. Run `python hw1.py` to start the start the program
    - this will automatically set up the dataset

### Requirements
- Python 3.8+
- pip
- virtual environment (optional)

## Solution
The program benchmarks the performance of two different implementations of document comparison. The difference is in the way they implement minhash. The faster version generates hashes and applies them to the a shorter shingle matrix. This is noticeably faster but has the drawback of being less accurate.

**Naive minhash:**
```python
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
```
The naive approach collects all shingles and then generates a sparse presence matrix for each document. Then, the algorithm creates a permutation and seeks the first appearance of a shingle in each document. If two documents have the same shingle appear first, it increases the confidence of the similarity between the two documents.

**Fast minhash:**
```python
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
```
Instead of permuting the presence matrix, a more efficient approach is to hash the shingles instead. The matrix is also cut to reduce the number of computations.

In addition to this, we also use locality sensitive hashing (LSH) to further reduce computation.
**LSH:**
```python
def lsh_pairs(sig_matrix, threshold):
    band_size = threshold_to_band_size(sig_matrix.shape[1], threshold)
    buckets = {}
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
```

## Results
------ Documents with similarity 5% ------
Document A:The quality of sleep is better that ohter drugs i've taken is the only benefit I  find.  I tried to taper off of it and fould it very difficult the lowest doesage i can take is 100mg.  a little drowsy in the morning but after a couple of cups of coffee im fine.
Document B:There was very little benefit to me. I was having psychotic episodes every day. The drug puportedly taken to stop the episodes did nothing. The best thing it did was make me drowsy and help me sleep.

Document A:Reduction of pain and inflammation.
Document B:Reduced redness of complexion; reduction in overall inflammation of skin; reduced breakouts of acne.

------ Documents with similarity 10% ------

Document A:I felt that i did not feel any benefits from this drug.
Document B:I did not experience any benefits whatsoever.

Document A:I didn't take the product long enough to evaluate the benefits. I quit because of side effects.
Document B:I couldn't tolerate the side effects, so I was unable to experience the benefits.

------ Documents with similarity 20% ------
Document A:For the first time in my life I had enough lashes to apply mascara to.  I had tried eyelash extensions which only broke off or pulled out what few thin lashes I did have.  Strip lashes were itchy and uncomfortable.  I now have normal lashes.

Even though I only applied it to upper lashes the lower lashes have grown longer and thicker too.
Document B:For the first time in my life, I had enough eyelashes to apply mascara to.  I had tried eyelash extensions previously but they only worsened the problem by breaking off or pulling out what skimpy lashes I did have.  After several months of Latisse I have eyelashes and even though I apply it only to upper lashes it has made lower lashes grow too.

## Benchmarks
The runtime and effectiveness of any algorithm is dependent on the number of permutations. Specifically, increasing the number of permutations means all algorithms will evenutally approach accuracy of doing a naive Jaccard comparison on the shingle set. 

### Naive Permutation vs Fast Min Hashing
Both of these algorithms accomplish the same thing - permutating the shingles within the document being analyzed to estimate Jaccard simulatrity. However, the naive algorithm needs to allocate memory that scales at O(N) with the number of permutations. The fast min hash algorithm creates N hash functions once - this is also a memory allocation, but only happens one time. It then creates a single signature matrix. The upfront cost of the fast min hash algorithm means that for small numbers of permutations or documents, a naive permutation algo may be faster. However, for any practical number of permutations and documents, fast min hashing is faster. 

Naive Permutations are compared to fast min hashing on a set of 3064 documents. Three benchmarks are run at 100, 200, and 300 permutations.
|Permuations| Runtime(s) Naive| Runtime(s) Fast Min Hash|
|-----------|-----------------|-------------------------|
|100        | 84.64           | 52.91                   |
|200        | 171.64          | 95.34                   |
|300        | 255.12          | 138.01                  |

Both algorithms scale linearly, but Fast Min Hash takes about 50% of the time.

Accuracy - How do these compare to a Naive Jaccard. We know these algos are estimates, so we would like to test and see how they compare.
Over 100 documents with 1000 permutations per document, we see the following:
 - Naive Permutation Error: 0.23%
 - Fast MinHash Error: 0.32%
In general, this is a small amount of error. Error is measured as  
`abs(estimate - actual)`

Finally, we should compare fast 

First, consider just 100 permutations:
|Threshold| Naive pairs | LSH pairs  |
|---------|-------------|------------|
|  0.05   |     133     |     27     |
|  0.10   |       7     |      3     |
|  0.20   |       1     |      0     |
|  0.30   |       1     |      0     |
|  0.40   |       0     |      0     |
|  0.50   |       0     |      0     |

- Fast Min Hash with Naive Jaccard runtime -- ~20.73s
- Fast Min Hash with LSH runtime -- ~18.01s  (~13% faster)
> Results are averaged over 3 runs

Now, consider the same test with 10,000 permutations:
|Threshold| Naive pairs | LSH pairs  |
|---------|-------------|------------|
|  0.05   |     133     |      56    |
|  0.10   |       7     |      11    |
|  0.20   |       1     |      4     |
|  0.30   |       1     |      3     |
|  0.40   |       0     |      2     |
|  0.50   |       0     |      0     |

- Fast Min Hash with Naive Jaccard runtime -- ~437 s
- Fast Min Hash with LSH Runtime -- ~344 s (~21% faster)

But breaking down the algos, we see:
~340 s in both cases to run the fast min hash algorithm. This means:
 - Naive Jaccard on the signature matrix: ~97 s
 - LSH on the signature matrix: ~4 s
So we see that LSH 
