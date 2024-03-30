import json
import pickle
import re

airports = r'C:\Users\ujasv\OneDrive\Desktop\codes\cirrostrats-backend\all_US_airports_dict.pkl'
with open(airports, 'rb') as f:
    x = pickle.load(f)

xx = []
for a,b in x.items():
    cities = b[1]
    for y in cities:
        xx.append(y)

airport_dict = {}
for i in xx:
    
    first_dash_index = re.search(r'-', i).start()
    
    # Splitting the string by the first dash
    first_part = i[:first_dash_index][:-1]
    second_part = i[first_dash_index + 1:][1:]
    
    airport_dict.update({first_part:second_part})

airport_list = []
for airport_id, airport_name in airport_dict.items():
    airport_data = {
        'id': airport_id,
        'name': airport_name,
        'code': airport_id  # Assuming the code is the same as the airport ID
    }
    airport_list.append(airport_data)


with open('airports_dump.json','w') as f:
    json.dump(airport_dict,f)