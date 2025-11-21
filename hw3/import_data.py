import gzip
import os
import time
import requests
import hashlib
from urllib import parse

my_table = dict()

def get_file(url, fname):
    data = requests.get(url).content
    with open(fname, 'wb') as f:
        f.write(data)
    return fname

def decompress_data(fname, write_name):
    with open(write_name, 'wb') as wf:
        with gzip.open(fname, 'rb') as rf:
            content = rf.read()
            wf.write(content)
    return write_name

class EdgeStream:
    file = None
    runtime = 0

    def __init__(self, url):
        fname = parse.urlparse(url).path.split("/")[-1]
        write_name = ".".join(fname.split(".")[:2])
        if write_name not in os.listdir():
            fname = get_file(url, fname)
            decompress_data(fname, write_name)
        self.file = open(write_name, 'r')

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