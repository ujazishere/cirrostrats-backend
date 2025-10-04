import json
import pickle
import re

"""
Dumps all US airports from a pickle file allegedly. 
this is the source structure key as state : value as [link, [airport_1, airport_2, airport_3]]
example:
{'Alabama': ['https://skyvector.com/airports/United%20States/Alabama',
  ['TOI - Troy Municipal At N Kenneth Campbell Field Airport',

final return is a list of dictionaries with id, name and code
the label code would be better used as either ICAO or IATA
"""

airports = r'C:\Users\ujasv\OneDrive\Desktop\codes\cirrostrats-backend\all_US_airports_dict.pkl'
with open(airports, 'rb') as f:
    x = pickle.load(f)

xx = []
for a,b in x.items():
    US_state = a
    cities = b[1]
    for each_city in cities:
        xx.append(each_city)

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