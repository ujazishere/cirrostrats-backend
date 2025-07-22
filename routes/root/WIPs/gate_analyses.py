from matplotlib import pyplot as plt
from config.database import collection_flights, client_UJ, db_UJ        # UJ mongoDB

"""
Idea is to inspect the rate of departures and arrivals at a gate.
intent: To separate saturated and unsaturated gates.
"""
gates_test = db_UJ['ewrGates']   # create/get a collection

return_crit = {'_id':0}
# find_crit = {"_id": ObjectId(gate_id)}
# find_crit = {'Gate':{'$regex':"101"}}
find_crit = {}
res = gates_test.find(find_crit, return_crit)
ewr_gates = list(res)

ewr_gate_departure_analyses = {}
# c_digits = set()

for i in ewr_gates:
    for a,b in i.items():
        if b[0] == "C":
            # ints =  int(b[1:])
            # c_digits.add(ints)
            # ewr_gate_departure_analyses[ints] = ewr_gate_departure_analyses.get(ints,0) +1
            ewr_gate_departure_analyses[b] = ewr_gate_departure_analyses.get(b,0) +1

"""
TODO: Notams This link contains database of safetly reports and is categorised by good metrics:
     https://asrs.arc.nasa.gov/search/database.html
    Reports can be downloaded in csv, find a way to decipher these and represent it in
    a readable format based on airports and show it on the web app airport page/components.
"""