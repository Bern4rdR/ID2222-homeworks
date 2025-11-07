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
|Threshold| Naive pairs | LSH pairs  |
|---------|-------------|------------|
|  0.05   |     133     |     27     |
|  0.10   |       7     |      3     |
|  0.20   |       1     |      0     |
|  0.30   |       1     |      0     |
|  0.40   |       0     |      0     |
|  0.50   |       0     |      0     |

## Benchmarks
- Naive runtime -- ~20.73s
- LSH runtime -- ~18.01s  (~13% faster)
> Results are averaged over 3 runs
