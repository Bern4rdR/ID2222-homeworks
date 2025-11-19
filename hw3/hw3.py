from import_data import EdgeStream
import random
# global t, s, d0, di# = (0, 0, 0 ,0)
COUNTER = {
    't': 0,
    's': 0,
    'd0': 0,
    'di':0,
    'phi': 0
}
S = []
M = 6

# edge = (op, (u, v))

def update_counters(elem):
    op, _ = elem
    COUNTER['phi'] += 1 if op == "+" else -1

def sample_edge(edge):
    if COUNTER['d0'] + COUNTER['di'] == 0:
        if len(S) < M:
            S.append(edge)
        elif random.randint(0, COUNTER['t']) < M:
            rm_edge = S.pop(random.randint(0, len(S) - 1))
            update_counters(('-', rm_edge))
    elif random.randint(0, COUNTER['di']+COUNTER['d0']) < COUNTER['di']:
        S.append(edge)
        COUNTER['di'] -= 1
    else:
        COUNTER['d0'] -= 1
        return False
    return True

def main_loop():
    es = EdgeStream()
    elem = es.get_next_edge()
    while elem:
        # start main loop here algo 2, section 4.3 triest
        op, (u, v) = elem 
        COUNTER['t'] += 1
        COUNTER['s'] += 1 if op == "+" else -1
        if op == "+":
            if sample_edge((u, v)):
                update_counters(elem)
        elif (u, v) in S:
            update_counters(elem) # assuming op is -
            S.remove((u, v))
            COUNTER['di'] += 1
        else:
            COUNTER['d0'] += 1

        # get ready for next loop
        elem = es.get_next_edge()

    print(COUNTER)


if __name__ == "__main__":
    main_loop()