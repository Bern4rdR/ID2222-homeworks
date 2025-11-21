from import_data import EdgeStream
import time
import random
import math
from multiprocessing import Queue, Process
from collections import defaultdict
# global t, s, d0, di# = (0, 0, 0 ,0)

class AdjacencyMatrix:
    data: defaultdict
    elem_list: list = []
    num_edges: int
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

    def pop(self, index):
        edge = self.elem_list.pop(index)
        self.remove(edge)
        return edge
                # for i, k in enumerate(self.data.keys()):
        #     if total_len + len(self.data[k]) > index:
        #         rem_key = self.data[k].pop()
        #         self.data[rem_key].discard(k)
        #         return (k, rem_key)
        #     else:
        #         total_len += len(self.data[k])
        # print("No pop")
        
            

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
    work_queue = None
    data_queue = None
    task_count = 0
    def __init__(self, M):
        self.M = M 
        self.S = AdjacencyMatrix(M) 
        work_queue = Queue(10000) #quite big, no kill computer tack
        data_queue = Queue()

    @property
    def num_edges(self):
        return self.S.num_edges

    def count_neighbors(self, u, v):
        if self.num_edges == 0:
            return 0
        return len(self.S.data[u] & self.S.data[v])
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


    # this function is the vast majority of the time required to run the algo
    # to parallelize, we have some challenges
    # count neighbors relies on S, but the main loop will update S (but only when it calls count neighbors)
    # we could serialize S, and send it to the thread P;
    # better, S could be kept in shared memory, and P could handle doing the copy
    # so it saves time in the main thread
    def update_counters(self, elem):
        start = time.perf_counter()
        op, (u, v) = elem
        sn = self.count_neighbors(u, v)
        self.phi += sn if op == "+" else -sn
        self.update_runtime += time.perf_counter() - start

    def sample_edge(self, edge):
        start = time.perf_counter()
        u_end = 0
        if self.d0 + self.di == 0:
            if self.num_edges < self.M:
                self.S.append(edge)
                # self.num_edges += 1
            elif random.randint(0, self.t - 1) < self.M:
                rm_edge = self.S.pop(random.randint(0, self.num_edges - 1))
                u_start = time.perf_counter()
                self.update_counters(('-', rm_edge))
                u_end = time.perf_counter() - u_start
                self.S.append(edge)
        elif random.randint(0, self.di+self.d0) < self.di:
            self.S.append(edge)
            self.di -= 1
        else:
            self.d0 -= 1  
            return False
        self.sample_runtime += time.perf_counter() - start - u_end
        return True

    def print_debug(self):
        print(f"K: {self.k()}")
        print(f"S: {self.num_edges}")
        print(f'triangle count {self.p()}')


    def main_loop(self):
        es = EdgeStream()
        elem = es.get_next_edge()
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
            # if self.t%1000 == 0 and last_count != p(): 
            #     print_debug()
            #     last_count = p()
            #     break
            # if self.t > 10000000:
            #     break
            # get ready for next loop
            elem = es.get_next_edge()
        self.print_debug()
        print(f"Total Runtime: {time.perf_counter() - total_start}")
        print(f"Sample Runtime: {self.sample_runtime}")
        print(f"Update Counter Runtime: {self.update_runtime}")
        print(f"File IO time: {es.runtime}")
    

if __name__ == "__main__":
    tr = Triest(1000)
    tr.main_loop()