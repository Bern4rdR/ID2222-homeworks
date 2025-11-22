import gzip
import hashlib
import os
import time
from urllib import parse

import mmh3
import requests
from bitarray import bitarray

my_table = dict()


def get_file(url, fname):
    data = requests.get(url).content
    with open(fname, "wb") as f:
        f.write(data)
    return fname


def decompress_data(fname, write_name):
    with open(write_name, "wb") as wf:
        with gzip.open(fname, "rb") as rf:
            content = rf.read()
            wf.write(content)
    return write_name


class BloomFilter:
    def __init__(self, size=10_000_000, hash_count=5):
        self.size = size
        self.hash_count = hash_count
        self.bit_array = bitarray(size)
        self.bit_array.setall(0)

    def _hashes(self, item):
        for i in range(self.hash_count):
            yield mmh3.hash(str(item), i) % self.size

    def add(self, item):
        for h in self._hashes(item):
            self.bit_array[h] = True

    def __contains__(self, item):
        return all(self.bit_array[h] for h in self._hashes(item))


class EdgeStream:
    file = None
    runtime = 0
    bloom: BloomFilter

    def __init__(self, url):
        self.bloom = BloomFilter()
        fname = parse.urlparse(url).path.split("/")[-1]
        write_name = ".".join(fname.split(".")[:2])
        if write_name not in os.listdir():
            fname = get_file(url, fname)
            decompress_data(fname, write_name)
        self.file = open(write_name, "r")

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
            u, v = int(nasta[0]), int(nasta[1])
            u, v = (u, v) if u <= v else (v, u)
            if (u, v) in self.bloom:
                # Duplicate edge found, skip it by getting next edge
                retval = self.get_next_edge()
            else:
                # Add edge to Bloom filter to detect future duplicates
                retval = ("+", (u, v))
        except:
            retval = False
        self.runtime += time.perf_counter() - start
        return retval

    def get_next_line_bytes(self):
        return bytes(self.file.readline(), "utf-8")


if __name__ == "__main__":
    es = EdgeStream()
    for i in range(10):
        edge = es.get_next_edge()
        print(edge)
