from import_data import EdgeStream
import time
import random
import math
from collections import defaultdict

class AdjacencyMatrix:
    data: defaultdict
    elem_list: list = []
    num_edges: int
    remove_time = 0
    append_time = 0
    pop_time = 0
    def __init__(self, M):
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
        
    def adjacency_bench(self):
        print(f"Append Time: {self.append_time}")
        print(f"Remove Time: {self.remove_time}")
        print(f"Pop Time: {self.pop_time - self.remove_time}")
            

# edge = (op, (u, v))
class Triest():
    t=0
    s = 0
    d0 = 0
    di=0
    phi= 0
    decrements= 0
    sample_runtime= 0
    update_runtime= 0
    S: AdjacencyMatrix
    num_edges = 0
    triangle_est_at_time_t = []
    task_count = 0
    def __init__(self, M, data_url):
        self.es = EdgeStream(data_url)
        self.M = M 
        self.S = AdjacencyMatrix(M) 

    @property
    def num_edges(self):
        return self.S.num_edges

    def count_neighbors(self, u, v):
        if self.num_edges == 0:
            return 0
        ne = len(self.S.data[u] & self.S.data[v])
        return  ne 
        # return len(u_neigbors.intersection(v_neighbors))
        

    def k(self): 
        s = self.s
        di = self.di
        d0 = self.d0
        w = min(self.M, self.s+self.di+self.d0)
        return 1 - sum([math.comb(s, j)*math.comb(di+d0, w-j) for j in range(3)]) / math.comb(s+di+d0, w)


    def p(self):
        if self.num_edges < 3:
            return 0
        M = self.num_edges
        s = self.s
        return (self.phi/self.k()) * ( s*(s-1)*(s-2) )/( M*(M-1)*(M-2) )


    def update_counters(self, elem):
        start = time.perf_counter()
        op, (u, v) = elem
        sn = self.count_neighbors(u, v)
        self.phi += sn if op == "+" else -sn
        self.update_runtime += time.perf_counter() - start

    def sample_edge(self, edge):
        u_end = 0
        if self.d0 + self.di == 0:
            if self.num_edges < self.M:
                self.S.append(edge)
                # self.num_edges += 1
            elif random.randint(0, self.t - 1) < self.M:
                rm_index = random.randint(0, self.num_edges - 1)
                rm_edge = self.S.elem_list[rm_index]
                self.update_counters(('-', rm_edge))
                self.S.swap(rm_index, edge)
        elif random.randint(0, self.di+self.d0) < self.di:
            self.S.append(edge)
            self.di -= 1
        else:
            self.d0 -= 1  
            return False
        return True

    def print_debug(self):
        print(f"K: {self.k()}")
        print(f"S: {self.num_edges}")
        print(f'triangle count {self.p()}')


    def main_loop(self):
        elem = self.es.get_next_edge()
        total_start = time.perf_counter()
        last_count = 0
        while elem:
            # start main loop here algo 2, section 4.3 triest
            op, (u, v) = elem 
            self.t += 1
            self.s += 1 if op == "+" else -1
            if op == "+":
                if self.sample_edge((u, v)):
                    self.update_counters(elem)
            elif (u, v) in self.S:
                print("Did remove")
                self.update_counters(elem) # assuming op is -
                self.S.remove((u, v))
                self.di += 1
            else:
                print("Did missing edge remove")
                self.d0 += 1

            if self.t%5000 == 0:
                ee = 5000000
                elap = time.perf_counter() - total_start
                ratio = (1 - (self.t/ee))/(self.t/ee)
                print(f"{self.t/ee*100:0.1f}% ETA: {ratio*elap/60}", end="\r")
            elem = self.es.get_next_edge()

        self.print_debug()
        print(f"Total Runtime: {time.perf_counter() - total_start}")
        print(f"Sample Runtime: {self.sample_runtime}")
        print(f"Update Counter Runtime: {self.update_runtime}")
        print(f"File IO time: {self.es.runtime}")
    

if __name__ == "__main__":
    for url in ['https://snap.stanford.edu/data/web-Google.txt.gz',
                'https://snap.stanford.edu/data/web-BerkStan.txt.gz',
                'https://snap.stanford.edu/data/web-NotreDame.txt.gz',
                'https://snap.stanford.edu/data/web-Stanford.txt.gz']:
        tr = Triest(6000000, url)
        tr.main_loop()