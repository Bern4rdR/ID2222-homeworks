import os

def load_baskets(filename='T10I4D100K.dat'):
    baskets = []
    with open(filename, 'r') as f:
        for line in f.readlines():
            baskets.append(set([int(x) for x in line.strip().split(" ")]))
    return baskets

if __name__ == "__main__":
    print(load_baskets()[:20])