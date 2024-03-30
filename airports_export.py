import json
import pickle
import re

airports = r'C:\Users\ujasv\OneDrive\Desktop\codes\Cirrostrats\cirrostrats-backend\all_US_airports_dict.pkl'
with open(airports, 'rb') as f:
    x = pickle.load(f)

xx = []
for a,b in x.items():
    cities = b[1]
    for y in cities:
        xx.append(y)
test = {}
for i in xx:
    
    first_dash_index = re.search(r'-', i).start()
    
    # Splitting the string by the first dash
    first_part = i[:first_dash_index]
    second_part = i[first_dash_index + 1:]
    
    test.update({first_part:second_part})


with open('airports_dump.json','w') as f:
    json.dump(test,f)