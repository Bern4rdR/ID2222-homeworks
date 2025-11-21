import gzip
import time

import hashlib

my_table = dict()

def decompress_data():
    with open("web_graph.txt", 'wb') as wf:
        with gzip.open('web-Google.txt.gz', 'rb') as rf:
            content = rf.read()
            wf.write(content)

class EdgeStream:
    file = None
    runtime = 0

    def __init__(self, fname="web_graph.txt"):
        self.file = open(fname, 'r')

    def get_next_edge(self):
        start = time.perf_counter()
        nasta = self.file.readline()
        if nasta == "":
            return False
        while nasta[0] == "#":
            nasta = self.file.readline()
        nasta = nasta.strip().split("\t")
        retval = None
        try:
            retval =  ('+', (int(nasta[0]), int(nasta[1]))) 
        except:
            retval =  False
        self.runtime += time.perf_counter() - start
        return retval

    def get_next_line_bytes(self):
        return bytes(self.file.readline(), 'utf-8')

if __name__ == "__main__":
    es = EdgeStream()
    for i in range(10):
        edge = es.get_next_edge() 
        print(edge)