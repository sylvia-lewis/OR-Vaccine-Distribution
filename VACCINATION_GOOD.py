from gurobipy import *

#DATA
IDtoLVC = [
[92.4,54.5,74.1,35.4,61.8,62.2,44.3,4.8],
[66.7,50.2,29.0,58.2,81.7,34.2,16.8,64.4],
[34.6,17.6,50.4,32.2,23.8,34.8,66.7,70.7]
]

CCDPop = [4241,4879,2653,3176,3132,4188,4946,3138,3140,4609,4132,3748,3639,3695,4551,3242,3996,3905,2457,3496,4088,3418,3534,3337,4073]         #DEMAND

CCDtoLVC = [
[0,0,0,44.1,0,0,0,5.5],
[0,0,0,0,0,0,32.7,20.7],
[0,0,0,0,0,0,18.0,31.8],
[0,0,41.1,0,0,0,9.7,0],
[0,0,32.9,0,0,0,21.1,0],
[0,0,0,27.4,0,0,0,18.9],
[0,0,0,28.4,0,0,30.2,21.1],
[0,0,0,29.9,0,0,22.9,29.2],
[0,0,27.8,0,0,23.8,15.7,0],
[0,0,23.6,0,0,0,29.8,0],
[0,0,0,20.7,0,0,0,29.6],
[0,26.8,0,6.6,0,0,0,0],
[0,18.6,0,17.8,0,25.8,0,0],
[0,22.2,19.9,0,0,7.8,0,0],
[0,0,9.1,0,0,24.1,0,0],
[0,0,0,25.2,21.4,0,0,0],
[0,20.0,0,15.8,15.3,0,0,0],
[0,8.5,0,30.0,0,23.8,0,0],
[26.7,12.9,29.6,0,0,14.8,0,0],
[24.3,0,19.3,0,0,26.5,0,0],
[0,0,0,40.0,16.9,0,0,0],
[0,34.4,0,0,10.1,0,0,0],
[28.1,22.1,0,0,30.0,0,0,0],
[9.3,36.8,0,0,0,0,0,0],
[8.0,0,0,0,0,38.1,0,0]
]

cost = [110, 182, 159]
costIDtoLVC = 0.20
costCCDtoLVC = 1.00
MAXID = 38000
MAXLVC = 16000
WEEKLYMAX = 2200
DELAYCOST = 10
MAXDIFF = 0.1

#MODEL
model = Model("Vaccines")

#SETS 
I = range(len(IDtoLVC))         #Set of Import Depots
J = range(len(IDtoLVC[0]))      #Set of Vaccination centres
K = range(len(CCDPop))          #Set of Population centres
T = range(6)                    #Weeks

#VARIABLES
X = {}                          #FLOW IN TO VACCINATION CENTRES
for i in I:
    for j in J:
        X[i,j] = model.addVar(name=f"X{[i]},{[j]}") 

Y = {}                          #FLOW OUT FROM VACCINATION CENTRES (people coming to get vaccinated)
for j in J:
    for k in K:
        for t in T:
            Y[j,k,t] = model.addVar(name=f"Y{[j]},{[k]},{[t]}")
            
R = {}                      #ratio vaccinated
for t in T:
    for k in K:
        R[k,t] = model.addVar(name=f"R{[k]},{[t]}")

min_ratio = {}              #min cumulutative fraction vaccinated
max_ratio = {}              #max cumulutative fraction vaccinated
for t in T:
    min_ratio[t] = model.addVar(name=f"min_ratio{[t]}")
    max_ratio[t] = model.addVar(name=f"max_ratio{[t]}")

#CONSTRAINTS
for t in T:
    for j in J:         
        flow_out_X = quicksum(Y[j,k,t] for k in K)
        C1 = model.addConstr(flow_out_X <= WEEKLYMAX, name="weekly max")                #restriction on doses given per week for each LVC
for j in J:                     
    flow_in_X = quicksum(X[i,j] for i in I)
    flow_out_total = quicksum(Y[j,k,t] for k in K for t in T)
    C2 = model.addConstr(flow_in_X == flow_out_total, name="flow in/flow out")         #flow in/flow out equality
    C3 = model.addConstr(flow_in_X <= MAXLVC, name="MAXLVC")                           #Restriction on total number of vaccinations per vaccination centre
for k in K:                     #flow in to people must satify demand
    flow_in_K = quicksum(Y[j,k,t] for j in J for t in T if CCDtoLVC[k][j] != 0)
    C4 = model.addConstr(flow_in_K >= CCDPop[k], name="demand")
for i in I:                     #Restriction on number imported through each ID
    flow_out_ID = quicksum(X[i,j] for j in J)
    C5 = model.addConstr(flow_out_ID <= MAXID, name="MAXID")                         
for t in T:                     #fairness constraint
    for k in K:
        vaxxed = quicksum(Y[j,k,t] for j in J)
        if t == 0:
            R[k,t] = vaxxed / CCDPop[k]
        elif t > 0:
            R[k,t] = R[k, t-1] + (vaxxed / CCDPop[k])
        C6 = model.addConstr(min_ratio[t] <= R[k,t], name="find min ratio")                         #finding min ratio per t
        C7 = model.addConstr(max_ratio[t] >= R[k,t], name="find max ratio")                         #finding max ratio per t
        C8 = model.addConstr(max_ratio[t] - min_ratio[t] <= MAXDIFF, name="ratio difference")       #difference between max and min is less than 0.1
       
#NEW BOOKKEEPING VARIABLES
Z = {}                          #How much to import to each ID
for i in I:
    Z[i] = quicksum(X[i,j] for j in J)

U = {}                          #How many people left unvaccinated after each week
for t in T:
    vaxxed = quicksum(Y[j,k,t] for j in J for k in K)
    if t == 0:
        U[t] = sum(CCDPop) - vaxxed
    if t > 0:
        U[t] = U[t-1] - vaxxed 

#OBJECTIVE
model.setObjective(
    quicksum(cost[i] * Z[i] for i in I)                                                         #IMPORT COSTS FOR EACH ID
        + quicksum(costIDtoLVC * IDtoLVC[i][j] * X[i,j] for j in J for i in I)                  #TRANSPORT COSTS TO DISTRIBUTE TO LVCs
        + quicksum(costCCDtoLVC * CCDtoLVC[k][j] * Y[j,k,t] for j in J for k in K for t in T)   #TRANSPORT COSTS FOR CITIZENS
        + quicksum(DELAYCOST * U[t] for t in T)                                                 #DELAY COSTS
    )

#OPTIMISE
model.optimize()

#PRINT
for i in I:
    for j in J:
        if (X[i,j].x > 0):
            print("Import from ID", i, "to LVC", j, X[i,j].x, "doses")
        
t = 0                                           #vaccinations during the first week, can be changed to plan for each week
print("for t = 0:")
for k in K:
    for j in J:
        if (Y[j,k,0].x > 0):print("People from", k, "Get vaxxed at", j, "number:", Y[j,k,0].x)
           
#SENSITIVITY ANALYSIS    
print("Constraints sensitivity")
for c in [C1,C3,C5]:
    print(c.ConstrName, "-> dual variable:", round(c.pi,4), "slack:", round(c.slack,4), 
          "SARHSLow:", round(c.SARHSLow,4), "RHS:", round(c.RHS,4), "SARHSUp:", round(c.SARHSUp,4))
    
