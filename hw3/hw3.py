from import_data import EdgeStream

def update_counters(elem):
    op, edge = elem
    pass

def sample_edge(u, v):
    pass

def main_loop():
    es = EdgeStream()
    edge = es.get_next_edge()
    while edge:
        print(edge)
        edge = es.get_next_edge()


if __name__ == "__main__":
    main_loop()