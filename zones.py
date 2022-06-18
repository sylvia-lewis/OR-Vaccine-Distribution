from itertools import combinations
from functools import lru_cache

Z = range(9)
PROBOUTBREAK = [0.2 for j in Z]

# The state is a 9-tuple where each element is
# -1 = outbreak, 0 = normal, 1 = protected
# NextStates returns a list of tuples with a probability
# in position 0 and a state as a tuple in position 1
def NextStates(State, OutbreakProb):
    ans = []
    # Z0 are the normal zones
    Z0 = [j for j in Z if State[j]==0]
    n = len(Z0)
    for i in range(n+1):
        for tlist in combinations(Z0, i):
            p = 1.0
            slist = list(State)
            for j in range(n):
                if Z0[j] in tlist:
                    p *= OutbreakProb[Z0[j]]
                    slist[Z0[j]] = -1
                else:
                    p *= 1-OutbreakProb[Z0[j]]
            ans.append((p, tuple(slist)))
    return ans

# example
# zones 0, 6, 7 have been protected
# zones 3, 4, 8 have outbreaks
# zones 1, 2, 5 are normal (so there will be 2**3 = 8 possible next states)
states = NextStates((1,0,0,-1,-1,0,1,1,-1), [0.2 for j in Z])

Facilities = [
    'Supermarket',          #0
    'Government Office',    #1
    'Bus Depot',            #2
    'Wedding Chapel',       #3
    'Town Hall',            #4
    'Bank',                 #5
    'Medical Centre',       #6
    'Post Office',          #7
    'Library',              #8
    'Ambulance',            #9
    'Fire Station',         #10
    'Convenience Store',    #11
    'School',               #12
    'Hospital',             #13
    'Hotel',                #14
    'Police Station'        #15
]

Zones = [
    [5,8],          #0
    [0,1],          #1
    [7,9,11],       #2
    [0,1,4,14,15],  #3
    [2,13],         #4
    [9,10],         #5
    [3,15],         #6
    [6,11,12],      #7
    [12,15]         #8
]

neighbours = {
    0 : (1,3),
    1 : (0,2,4),
    2 : (1,5),
    3 : (0,4),
    4 : (1,3,5,7),
    5 : (2,4,6),
    6 : (5,8),
    7 : (4,),
    8 : (6,)
    }

important = [
    13, #'Hospital',
    4, #'Town Hall',
    9, #'Ambulance',
    0 #supermarket
    ]

def actionspace(s):
    actionspace = []
    for i in range(9):
        if s[i] == 0:
            actionspace += [i]
    return (actionspace)

def protect_zone(state, a):
    # try to protect next zone
    if a == None:
        return (state)
    next_state = list(state)
    next_state[a] = 1
    next_state = tuple(next_state)
    return (next_state)

def new_probabilities(s):
    new_prob = []
    for i in Z:
        n = 0
        for x in Z:
            if s[x] == -1:
                if x in neighbours[i]:
                    n += 1
        new_prob += [0.2 + 0.05 * n]
    return new_prob

def distinct_facilities(states):
    distinct_facilities = frozenset({})
    for i in Z:
        if states[i] != -1:
            for facility in Zones[i]:
                distinct_facilities = distinct_facilities | {facility}
    return distinct_facilities

# count how many distinct facilities are open given a potential state
def count_distinct_open(states):
    return (len(distinct_facilities(states)))

def important_saved(states):
    saved_important = 0
    distinct = distinct_facilities(states)
    for facility in distinct:
        if facility in important:
            saved_important += 1
    return (saved_important == 4)
                    

def transition(state, a):
    protected = protect_zone(state, a)
    new_prob = new_probabilities(state)
    new_state = NextStates(protected, new_prob) # PROBOUTBREAK) for comm. 13 
    # (p, state)
    return (new_state)

# communication 14
@lru_cache(maxsize=None)
def health_strategy_max_distinct_open(s):
    if 0 not in s:
        return (count_distinct_open(s), "Done")
    else:
        return (max(
            (sum(
                p * health_strategy_max_distinct_open(new_s)[0]
                for (p, new_s) in transition(s, a)
                ), a)
            for a in actionspace(s)
                ))

# communication 15
@lru_cache(maxsize=None)
def health_strategy_save_important(s):
    if 0 not in s:
        return (important_saved(s), "Done")
    else:
        return (max(
            (sum(
                p * health_strategy_save_important(new_s)[0]
                for (p, new_s) in transition(s, a)
                ), a)
            for a in actionspace(s)
                ))