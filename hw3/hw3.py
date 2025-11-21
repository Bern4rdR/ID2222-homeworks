from import_data import EdgeStream
import time
import random
import math
# global t, s, d0, di# = (0, 0, 0 ,0)
COUNTER = {
    't': 0,
    's': 0,
    'd0': 0,
    'di':0,
    'phi': 0,
    'decrements': 0,
    'sample_runtime': 0,
    'update_runtime': 0,
}
S = []
M = 1000
triangle_est_at_time_t = []

# edge = (op, (u, v))

def count_neighbors(u, v):
    if len(S) == 0:
        return 0
    # su = {u}
    # sv = {v}
    nu = set()
    nv = set()
    # u_neigbors = {(set(n)-su).pop() for n in S if u in n}
    # v_neighbors = {(set(n) - sv).pop() for n in S if v in n}
    for (a, b) in S:
        if a == u:
            nu.add(b)
        elif b == u:
            nu.add(a)
        if a == v:
            nv.add(b)
        elif b == v:
            nv.add(a)
    return len(nu & nv)
    # return len(u_neigbors.intersection(v_neighbors))
    

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


# this function is the vast majority of the time required to run the algo
# to parallelize, we have some challenges
# count neighbors relies on S, but the main loop will update S (but only when it calls count neighbors)
# we could serialize S, and send it to the thread P;
# better, S could be kept in shared memory, and P could handle doing the copy
# so it saves time in the main thread
def update_counters(elem):
    start = time.perf_counter()
    op, (u, v) = elem
    sn = count_neighbors(u, v)
    COUNTER['phi'] += sn if op == "+" else -sn
    COUNTER['update_runtime'] += time.perf_counter() - start

def sample_edge(edge):
    start = time.perf_counter()
    u_end = 0
    if COUNTER['d0'] + COUNTER['di'] == 0:
        if len(S) < M:
            S.append(edge)
        elif random.randint(0, COUNTER['t'] - 1) < M:
            rm_edge = S.pop(random.randint(0, len(S) - 1))
            u_start = time.perf_counter()
            update_counters(('-', rm_edge))
            u_end = time.perf_counter() - u_start
            S.append(edge)
    elif random.randint(0, COUNTER['di']+COUNTER['d0']) < COUNTER['di']:
        S.append(edge)
        COUNTER['di'] -= 1
    else:
        COUNTER['d0'] -= 1  
        return False
    COUNTER['sample_runtime'] += time.perf_counter() - start - u_end
    return True

def print_debug():
    print(COUNTER)
    print(f"K: {k()}")
    print(f"S: {len(S)}")
    print(f'triangle count {p()}')


def main_loop():
    es = EdgeStream()
    elem = es.get_next_edge()
    total_start = time.perf_counter()
    last_count = 0
    while elem:
        # start main loop here algo 2, section 4.3 triest
        op, (u, v) = elem 
        COUNTER['t'] += 1
        COUNTER['s'] += 1 if op == "+" else -1
        if op == "+":
            if sample_edge((u, v)):
                update_counters(elem)
        elif (u, v) in S:
            print("Did remove")
            update_counters(elem) # assuming op is -
            S.remove((u, v))
            COUNTER['di'] += 1
        else:
            print("Did missing edge remove")
            COUNTER['d0'] += 1

        if COUNTER['t']%5000 == 0:
            print(f"{COUNTER['t']/50000:0.1f}%", end="\r")
        # if COUNTER['t']%1000 == 0 and last_count != p(): 
        #     print_debug()
        #     last_count = p()
        #     break
        # if COUNTER['t'] > 10000000:
        #     break
        # get ready for next loop
        elem = es.get_next_edge()
    print_debug()
    print(f"Total Runtime: {time.perf_counter() - total_start}")
    print(f"Sample Runtime: {COUNTER['sample_runtime']}")
    print(f"Update Counter Runtime: {COUNTER['update_runtime']}")
    print(f"File IO time: {es.runtime}")
    

if __name__ == "__main__":
    main_loop()