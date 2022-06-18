from gurobipy import *
setParam('MIPGap', 0)
#DATA
IDtoLVC = [
[92.4,54.5,74.1,35.4,61.8,62.2,44.3,4.8],
[66.7,50.2,29.0,58.2,81.7,34.2,16.8,64.4],
[34.6,17.6,50.4,32.2,23.8,34.8,66.7,70.7]
]

CCDPop = [6220,3739,4765,4625,5937,6415,4248,4406,6392,5952,5309,4951,5477,5793,4400,5078,5442,3473,5137,5637,4615,5113,4738,5385,5065]

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

LVCUCost = [1909000,1249000,1028000,1608000,1480000,1384000,1579000,1229000]

LVCCSaving = [3502000,5892000,4424000,3154000,4370000,3499000,3925000,4566000]

cost = [110, 182, 159]
costIDtoLVC = 0.20
costCCDtoLVC = 1.00
MAXID = 52000
MAXLVC = 16000      #upgraded LVC max = MAXLVC * 1.5

#MODEL
model = Model("Vaccines")

#SETS
I = range(len(IDtoLVC))         #Set of Import Depots
J = range(len(IDtoLVC[0]))      #Set of Vaccination centres
K = range(len(CCDPop))          #Set of Population centres

#VARIABLES
X = {}                          #FLOW IN TO VACCINATION CENTRES
for i in I:
    for j in J:
        X[i,j] = model.addVar(name=f"X{[i]},{[j]}")

U = {j: model.addVar(vtype=GRB.BINARY) for j in J}      #Yes (1) or No (0) will the LVC be upgraded?

C = {j: model.addVar(vtype=GRB.BINARY) for j in J}      #Yes (1) or No (0) will the LVC be CLOSED?

V = {}      #Yes (1) or No (0) will CCD[k] be sent to LVC[j]
for j in J:
    for k in K:
        V[j,k] = model.addVar(vtype=GRB.BINARY)
            

#CONSTRAINTS
for j in J:
    flow_in_X = quicksum(X[i,j] for i in I)
    flow_out_total = quicksum(V[j,k] * CCDPop[k] for k in K)   #sum of populations being sent to LVC
    C1 = model.addConstr(flow_in_X == flow_out_total, name="flow_in/flow_out")         #flow in/flow out equality
    C2 = model.addConstr(U[j] + C[j] <= 1)       #can't be both closed and upgraded
    C3 = model.addConstr(flow_in_X <= MAXLVC*(1 + 0.5 * U[j] - C[j]), name="MAXLVC")    #MAXLVC constraint with normal and upgraded
for k in K:
    model.addConstr(quicksum(V[j,k] for j in J if (CCDtoLVC[k][j] == 0)) == 0)
    C4 = model.addConstr(quicksum(V[j,k] for j in J) == 1)  #CCDs sent to one and one only LVC
for i in I:                     
    flow_out_ID = quicksum(X[i,j] for j in J)
    C5 = model.addConstr(flow_out_ID <= MAXID, name="MAXID")    #Restriction on number imported through each ID

#BOOKKEEPING VARIABLE
Z = {i: model.addVar() for i in I}                          #How much to import to each ID
for i in I:
    Z[i] = quicksum(X[i,j] for j in J)

#OBJECTIVE
model.setObjective(
    quicksum(cost[i] * Z[i] for i in I)                                            #IMPORT COSTS FOR EACH ID
        + quicksum(costIDtoLVC * IDtoLVC[i][j] * X[i,j] for j in J for i in I)     #TRANSPORT COSTS TO DISTRIBUTE TO LVCs
        + quicksum(costCCDtoLVC * CCDtoLVC[k][j] * V[j,k] * CCDPop[k] for j in J for k in K) #TRANSPORT COSTS FOR CITIZENS
        + quicksum(LVCUCost[j] * U[j] for j in J)                                  #UPGRADE COSTS
        - quicksum(LVCCSaving[j] * C[j] for j in J)                            #CLOSED SAVINGS
    )

#OPTIMISE
model.optimize()

#PRINT
for j in J:
    if C[j].x >= 0.5:
        print("LVC {} to be closed".format(j))
    elif U[j].x >= 0.5:
        print("LVC {} to be upgraded".format(j))
    else:
        print("LVC {} no change".format(j))
        
for k in K:
    for j in J:
        if (CCDtoLVC[k][j] != 0):
            if V[j,k].x > 0.05:
                print(f"CCD-{k} sent to LVC-{j}".rjust(20))


