from import_data import EdgeStream
import random
import math
# global t, s, d0, di# = (0, 0, 0 ,0)
COUNTER = {
    't': 0,
    's': 0,
    'd0': 0,
    'di':0,
    'phi': 0,
    'decrements': 0
}
S = []
M = 6
triangle_est_at_time_t = []

# edge = (op, (u, v))

def count_neighbors(u, v):
    if len(S) == 0:
        return 0
    su = {u}
    sv = {v}
    u_neigbors = {(set(n)-su).pop() for n in S if u in n}
    v_neighbors = {(set(n) - sv).pop() for n in S if v in n}
    return len(u_neigbors.intersection(v_neighbors))
    

def k(): 
    s = COUNTER['s']
    di = COUNTER['di']
    d0 = COUNTER['d0']
    w = min(M, COUNTER['s']+COUNTER['di']+COUNTER['d0'])
    return 1 - sum([math.comb(s, j)*math.comb(di+d0, w-j) for j in range(3)]) / math.comb(s+di+d0, w)


def p():
    if len(S) < 3:
        return 0

    s = COUNTER['s']
    return (COUNTER['phi']/k()) * ( s*(s-1)*(s-2) )/( len(S)*(len(S)-1)*(len(S)-2) )



def update_counters(elem):
    op, (u, v) = elem
    sn = count_neighbors(u, v)
    COUNTER['phi'] += sn if op == "+" else -sn

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
        if COUNTER['t'] > 1000:
            break
        # get ready for next loop
        elem = es.get_next_edge()

    print(COUNTER)
    print(f"K: {k()}")
    print(f"S: {len(S)}")
    print(f'triangle count {p()}')


if __name__ == "__main__":
    main_loop()