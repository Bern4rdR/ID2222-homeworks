import math
import random
import time
from collections import defaultdict

from import_data import EdgeStream


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

    def adjacency_bench(self):
        print(f"Append Time: {self.append_time}")
        print(f"Remove Time: {self.remove_time}")
        print(f"Pop Time: {self.pop_time - self.remove_time}")


# edge = (op, (u, v))
class Triest:
    t = 0
    s = 0
    d0 = 0
    di = 0
    phi = 0
    decrements = 0
    sample_runtime = 0
    update_runtime = 0
    S: AdjacencyMatrix
    num_edges = 0
    triangle_est_at_time_t = []
    task_count = 0

    def __init__(self, M, data_url):
        self.es = EdgeStream(data_url)
        self.M = M
        self.S = AdjacencyMatrix(M)
        self.name = data_url.split("/")[-1].split(".")[0]

    @property
    def num_edges(self):
        return self.S.num_edges

    def count_neighbors(self, u, v):
        if self.num_edges == 0:
            return 0
        ne = len(self.S.data[u] & self.S.data[v])
        return ne
        # return len(u_neigbors.intersection(v_neighbors))

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

    def update_counters(self, elem):
        start = time.perf_counter()
        op, (u, v) = elem
        sn = self.count_neighbors(u, v)
        self.phi += sn if op == "+" else -sn
        self.update_runtime += time.perf_counter() - start

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

    def print_debug(self):
        print(f"K: {self.k()}\t\tphi: {self.phi}")
        print(f"S: {self.num_edges}")
        print(f"Edge Count:\t\033[32m{self.t:,}\033[0m")
        print(f"Triangle Count:\t\033[32m{int(self.p()):,}\033[0m")

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
                # this never gets called
                print("Did remove")
                self.update_counters(elem)  # assuming op is -
                self.S.remove((u, v))
                self.di += 1
            else:
                print("Did missing edge remove")
                self.d0 += 1

            if self.t % 5000 == 0:
                ee = 5000000
                elap = time.perf_counter() - total_start
                ratio = (1 - (self.t / ee)) / (self.t / ee)
                print(
                    f"Processing:\t{self.t / ee * 100:0.1f}% ETA: {ratio * elap:.0f}s",
                    end="\r",
                )
            elem = self.es.get_next_edge()

        print()
        self.print_debug()
        print(f"Total Runtime:\t{time.perf_counter() - total_start:.2f}s   ")
        print(f"Sample Runtime:\t{self.sample_runtime:.2f}s")
        print(f"Update Counter Runtime:\t{self.update_runtime:.2f}s")
        print(f"File IO time:\t{self.es.runtime:.2f}s")


if __name__ == "__main__":

    def do_all():
        for url in [
            "https://snap.stanford.edu/data/web-Google.txt.gz",  # Edges: 5,105,039    Triangles: 13,391,903
            "https://snap.stanford.edu/data/web-BerkStan.txt.gz",  # Edges: 7,600,595    Triangles: 64,690,980
            "https://snap.stanford.edu/data/web-NotreDame.txt.gz",  # Edges: 1,497,134    Triangles: 8,910,005
            "https://snap.stanford.edu/data/web-Stanford.txt.gz",  # Edges: 2,312,497    Triangles: 11,329,473
        ]:
            tr = Triest(1_000_000, url)
            print("\n\033[32m" + "#" * (16 + len(tr.name)))
            print(f"#{' ' * 7}{tr.name}{' ' * 7}#")
            print("#" * (16 + len(tr.name)) + "\033[0m")
            tr.main_loop()

    def do_google():
        url = "https://snap.stanford.edu/data/web-Google.txt.gz"
        tr = Triest(1_000_000, url)
        tr.main_loop()

    do_google()
    # do_all()
