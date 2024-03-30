import pickle
import os


# WARNING: TO OPEN FILE, DJANGO IS USING /WEATHER_WORK/DJ AS WORKING DIRECTORY WHEREAS THE RAW FILE IS USING /CIRROSTRATS 

# print(os.getcwd())

# .keys() in the dict are states and the value is a list.
# This list contains 2 items.
    # first one is the link(a string) and other is the list of all airports of that state
# Example: {'Florida': ['https:link.com', ['ZPH - Zephyrhills Municipal' , 'KDAB - Daytona airport']]}

# Use following variables depending on the use case;
django_path = 'dj_app/root/pkl/all_US_airports_dict.pkl'
external_path = 'dj/dj_app/root/pkl/all_US_airports_dict.pkl'

django_path_id = 'dj_app/root/pkl/airport_identifiers_US.pkl'
external_path_id = 'dj/dj_app/root/pkl/airport_identifiers_US.pkl'

# with open(django_path, 'rb') as f:
    # airports = pickle.load(f)

id_3_letter = []
with open(external_path_id, 'rb') as f:
    id = pickle.load(f)
for i in id:
    if len(i) == 3:
        id_3_letter.append(i)
print(len(id_3_letter))


# ['florida'][0] refers to link, ['florida'][1] refers to all the airports. ['florida'][1][0] refers to the first airport
# print(((airports['Florida'][1][100])))
