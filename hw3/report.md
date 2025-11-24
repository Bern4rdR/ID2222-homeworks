# Homework 2
November 10 or whatever

### Authors
Bernard Rumar -- [bernardr@kth.se](mailto:bernardr@kth.se)

Vivienne Curewitz -- [curewitz@kth.se](mailto:curewitz@kth.se)

## Datasets used
We used the datasets from standford webgraph. Our code automatically fetches the dataset if it isn't already on the user's hard drive based on the URL provided when the Triest Object is initialized in the python script. 


## Solution
We implemented Triest ("Triangle Estimation", not the village in Italy.) We implemented the dynamic algorithm as described in the Triest paper. At init, we specify a Size M, which is the size of the resevoir we sample. 
The steps of the algorithm are simple:
1. Sample the edge - check if we will add the edge to the resevoir - if the resevoir size is smaller than M, we always add the edge. If the resevoir size is larger than M, we do standard resevoir sampling to determine if we add the new edge to the resevoir. Where t is the potential sample number, and M is the size of the resevoir, we sample with probability M/t. If we sample, we remove a previous sample from the edge with uniform probability. When an edge is removed, we update the counters.
2. Updating Counters - if the edge is sampled, we update counters. We define a neighborhood of (u, v), where u and v are the nodes of the edge. The neighborhood of u is every node it is connected to that is also within the resevoir. The neighborhood of u and v is the intersection of the neigborhoods of u and v. When we update counters, we update the global counter with by adding the size of the neighborhood(u, v). If an edge is removed, we subtract the size of neighborhood. Note that if u, v are connected, the neighborhood(u, v) is the number of trianlges that have u and v as two of its point.


To make the algorithm "dynamic" it has to handle node deletions. We keep seperate counters, d0 and di, to track these. When we see an edge that is not in the resevoir being removed, we increment d0. When we remove an edge from the resevoir (we get a edge with the "-" operation that exists within the resevoir), we increment di.

The sample edge function also has different behavior based on the values of di and d0. If d0 + di != 0, the edge is sampled at probability (di/(di + d0)) and di is decremented. If the edge is sampled, then d0 is decremented. 


    ```python
   def sample_edge(self, edge):
        u, v = edge
        if v in self.S.data[u]: # skip duplicate edge
            return False

        if self.d0 + self.di == 0:
            if self.num_edges < self.M:
                self.S.append(edge)
                return True
            elif random.choices(population=[True, False], weights=[self.M/self.t, 1-self.M/self.t]):
                rm_index = random.randint(0, self.num_edges - 1)
                rm_edge = self.S.elem_list[rm_index]
                self.update_counters(("-", rm_edge))
                self.S.swap(rm_index, edge)
                return True
        elif random.choices(population=[True, False], weights=[self.di / (self.di + self.d0), 1 - self.di / (self.di+self.d0)]):
            self.S.append(edge)
            self.di -= 1
            return True
        else:
            self.d0 -= 1
            return False
 
    ```

The main loop is shown below.  

```python
    def main_loop(self):
        elem = self.es.get_next_edge()
        total_start = time.perf_counter()
        while elem:
            # start main loop here algo 2, section 4.3 triest
            op, (u, v) = elem
            self.t += 1
            self.s += 1 if op == "+" else -1
            if op == "+":
                # if true, we call update counter
                # it is true when we add a new edge
                # we only update the counter when we remove before adding
                if self.sample_edge((u, v)):
                    self.update_counters(elem)
            elif (u, v) in self.S:
                print("Did remove")
                self.update_counters(elem)  # assuming op is -
                self.S.remove((u, v))
                self.di += 1
            else:
                print("Did missing edge remove")
                self.d0 += 1
```

Updating counters is straighforwards:
```python
    def update_counters(self, elem):
        start = time.perf_counter()
        op, (u, v) = elem
        sn = self.count_neighbors(u, v)
        self.phi += sn if op == "+" else -sn
        self.update_runtime += time.perf_counter() - start
```

Triangle estimation is as follows:
```python
    def k(self):
        s = self.s
        di = self.di
        d0 = self.d0
        w = min(self.M, self.s + self.di + self.d0)
        return 1 - sum(
            [math.comb(s, j) * math.comb(di + d0, w - j) for j in range(3)]
        ) / math.comb(s + di + d0, w)

    def p(self):
        if self.num_edges < 3:
            return 0

        M = self.num_edges
        s = self.s
        return (self.phi / self.k()) * (s * (s - 1) * (s - 2)) / (M * (M - 1) * (M - 2))

```
Where P is the number of triangles. 

For efficient calculation, we use an "AdjacencyMatrix" to store the edges. This allows us to handle each edge in O(1) time.
```python
class AdjacencyMatrix:
    data: defaultdict
    elem_list: list
    num_edges: int
    remove_time = 0
    append_time = 0
    pop_time = 0

    def __init__(self, M):
        self.elem_list = []
        self.data = defaultdict(set)
        # self.elem_list = [None for _ in range(M)] not worth the hassle
        self.num_edges = 0

    def append(self, edge):
        u, v = edge
        self.data[u].add(v)
        self.data[v].add(u)
        self.elem_list.append(edge)
        self.num_edges += 1

    def remove(self, edge):
        u, v = edge
        self.data[u].discard(v)
        self.data[v].discard(u)
        self.num_edges -= 1

    def swap(self, index, new):
        ru, rv = self.elem_list[index]
        self.data[ru].discard(rv)
        self.data[rv].discard(ru)
        u, v = new
        self.data[u].add(v)
        self.data[v].add(u)
        self.elem_list[index] = new

    # too slow, do not use
    def pop(self, index):
        start = time.perf_counter()
        edge = self.elem_list.pop(index)
        self.remove(edge)
        self.pop_time += time.perf_counter() - start
        return edge
```

### Bonus
The bonus for this lab is answering questions:
Q1) What were the challenges we faced when implementing the algorithm? First, the paper uses M as 6 as an example. While this technically works, when M is that small, with a sample size of 5*10^6, the each seen triangle in the resevoir is estimated to represent something like 2*10^19 actual triangles. We did not realize this at first. When increasing M, we realized that our algorithm required O(M) time to hanlde an edge, so we had to refactor to bring that to O(1) time so we could run with a reasonably sized M.

Q2) Triest is not designed to be parallelized. First, the more memory you have, the larger your resevoir, and the better your estimate. So you are better off having a larger resevoir than multiple workers with proportionally smaller resevoirs. Second, an edge can be added in O(1) time; there is not iteration required so in most cases you could add edges as fast as you can receive them. Third, each step in the algorithm mutates the whole state of the resevoir, which means that each add remove effects the results of the next add/remove.

Q3) Yes, unbounded graph streams are the actual use case. We resevoir sample, so after time t, all elements have the same probability of being in the stream. At any time, the number of triangles seen so far can be estimated based on the counters at the current time. This estimate takes into account the total size of the stream in proportion to the resevoir size, so it will provide a reasonable estimate. Although as time stretches to infinity, we will have less accurate estimates. Eventually the error gets so large that it gets pointless.

Q4) Yes, Triest dynamic as it is implemented supports edge deletions. Further, we can see an edge deletion before we see that edge being added and the algorithm will function. 

## Installation
We developed in python 3.12. Run "pip install -r requirements.txt".

## Results
We are able to estimate the number of triangles with reasonable accuracy.

If M > the size of the graph (M > S) then we achieve 100% for "estimated" triangles. Obviously, we are just counting the triangles at this point. 

If M < the size of the graph (M < S) our accuracy decays as M gets smaller.

**Log output**
(datamining) vivienne@mbp python hw3.py
Processing:     102.1% ETA: -2s (this updates all the time, and we estimate the size of the graph so it doesn't get to exactly 100%)


K: 1.0          phi: 109614
S: 1000000
Edge Count:     5,105,039
Triangle Count: 14,583,583
Total Runtime:  146.83s   
Sample Runtime: 0.00s
Update Counter Runtime: 16.75s
## Benchmarks
Processing:     1.7% ETA: 49s
K: 1.0          phi: 1612010
S: 88234
Edge Count:     88,234
Triangle Count: 1,612,010
Total Runtime:  0.88s   
Sample Runtime: 0.00s
Update Counter Runtime: 0.26s
File IO time:   0.42s
Processing:     1.7% ETA: 53s
K: 1.0          phi: 1183819
S: 80000
Edge Count:     88,234
Triangle Count: 1,588,271
Total Runtime:  1.02s   
Sample Runtime: 0.00s
Update Counter Runtime: 0.33s
File IO time:   0.41s
Processing:     1.7% ETA: 71s
K: 1.0          phi: 457834
S: 60000
Edge Count:     88,234
Triangle Count: 1,456,026
Total Runtime:  1.53s   
Sample Runtime: 0.00s
Update Counter Runtime: 0.48s
File IO time:   0.45s
Processing:     1.7% ETA: 82s
K: 1.0          phi: 165896
S: 40000
Edge Count:     88,234
Triangle Count: 1,780,662
Total Runtime:  1.78s   
Sample Runtime: 0.00s
Update Counter Runtime: 0.53s
File IO time:   0.46s
Processing:     1.7% ETA: 91s
K: 1.0          phi: 46935
S: 20000
Edge Count:     88,234
Triangle Count: 4,030,557
Total Runtime:  1.74s   
Sample Runtime: 0.00s
Update Counter Runtime: 0.51s
File IO time:   0.50s
Processing:     1.7% ETA: 88s
K: 1.0          phi: 16133
S: 10000
Edge Count:     88,234
Triangle Count: 11,085,073
Total Runtime:  1.62s   
Sample Runtime: 0.00s
Update Counter Runtime: 0.44s
File IO time:   0.49s
