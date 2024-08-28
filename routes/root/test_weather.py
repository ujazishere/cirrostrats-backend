"""
# This is the jupyter code to initialize 
from config.database import collection, collection_weather
from schema.schemas import individual_serial, list_serial, individual_airport_input_data, serialize_airport_input_data
from routes.root.root_class import Root_class, Fetching_Mechanism, Source_links_and_api, Root_source_links
from bson import ObjectId
import requests
import datetime as dt
import json
import pickle
from pymongo import UpdateOne

all_datis_airports_path = r'c:\users\ujasv\onedrive\desktop\codes\cirrostrats\all_datis_airports.pkl'
with open(all_datis_airports_path, 'rb') as f:
    all_datis_airports = pickle.load(f)

rsl = Root_source_links
fm = Fetching_Mechanism()
all_airport_codes = [i['code'] for i in collection.find({})]
# weather_links = [rsl.weather(weather_type="metar",airport_id="K"+each_airport_code) for each_airport_code in all_airport_codes]
# resp_dict: dict = await fm.async_pull(list(weather_links))

def list_of_weather_links(type_of_weather,list_of_airport_codes):
    return [rsl.weather(weather_type=type_of_weather,airport_id="K"+each_airport_code) for each_airport_code in list_of_airport_codes]

test_list_of_airport_codes = all_airport_codes[:10]       
test_weather_links = list_of_weather_links('metar',test_list_of_airport_codes)


# returns a dict with key as url and value as metar
resp_dict: dict = await fm.async_pull(list(test_weather_links))


for a, b in resp_dict.items():
    print(str(a)[-3:])

def mdb_updates(resp_dict: dict, type_of_weather):
    # This function creates a list of fields/items that need to be upated and passes it as bulk operation to the collection.
    update_operations = []

    for url, weather in test_resp_dict.items():
        airport_id = str(url)[-3:]
        
        update_operations.append({
            UpdateOne({'code': airport_id},
                      {'$set': {f'weather.{type_of_weather}': weather}})
        })
    
    result = collection_weather.bulk_write(update_operations)
    print(result)
    

"""

# Create a proof of concept. Details can be worked on later with cleaning and improving efficiency.

from config.database import collection, collection_weather
from schema.schemas import individual_serial, list_serial, individual_airport_input_data, serialize_airport_input_data
from routes.root.root_class import Root_class, Fetching_Mechanism, Source_links_and_api, Root_source_links
from bson import ObjectId
import requests
import datetime as dt
import json
from pymongo import UpdateOne
import pickle
import asyncio
from routes.root.weather_parse import Weather_parse

# CAUTION!!! the .delete_many with delete all the documents
# collection_weather.count_documents({})      # returls total documents
# collection_weather.delete_many({})          # Deletes them all



rc = Root_class()
sl = Source_links_and_api()
rsl = Root_source_links
fm = Fetching_Mechanism()

def later_use():

    test_mdb = [i for i in collection.find({})][:3]

    utc_now = dt.datetime.now(dt.UTC)
    yyyymmddhhmm = utc_now.strftime("%Y%m%d%H%M")

all_datis_airports_path = r'c:\users\ujasv\onedrive\desktop\codes\cirrostrats\all_datis_airports.pkl'
with open(all_datis_airports_path, 'rb') as f:
    all_datis_airport_codes = pickle.load(f)

with open(r"C:\Users\ujasv\OneDrive\Desktop\pickles\taf_positive_airports.pkl", 'rb') as f:
    # TODO: These airport codes are speciafically selected to fetch taf data. Add scheduler to fetch data from all airports for taf everyonce a while and see what airports have been returned.
        # TODO HP: also account for - contruct a checking mechanism to check the validity of the data if it makes sense using regex. Setup notification if it doesn't match
            # This can be easily accomplished with regex or use sentences and frequently occouring bits to disregard them and ones that stand out need to be looked at.

    # TODO: TAF positive airports need to be checked at in the all mdb airports if they exist.
    taf_positive_airport_codes = pickle.load(f)

#  All airport codes from mongo db
all_mdb_airport_codes = [i['code'] for i in collection.find({})]

# These two are using async fetch. And its a complete set of returns for the weather.
# weather_links = [rsl.weather("metar",airport_id=each_airport_code) for each_airport_code in all_airport_codes]
# resp_dict: dict = await fm.async_pull(list(weather_links))

def list_of_weather_links(type_of_weather,list_of_airport_codes):
    return [rsl.weather(weather_type=type_of_weather,airport_id="K"+each_airport_code) for each_airport_code in list_of_airport_codes]

test_list_of_airport_codes = all_mdb_airport_codes[:5]       
test_weather_links = list_of_weather_links('datis',test_list_of_airport_codes)
# test_resp_dict: dict = await fm.async_pull(list(test_weather_links))





async def resp_dict_returns(weather_links):
    resp_dict: dict = await fm.async_pull(list(weather_links))
    return resp_dict




def mdb_updates(resp_dict: dict, weather_type):
    # This function creates a list of fields/items that need to be upated and passes it as bulk operation to the collection.
    # TODO: Now need to account for new airport codes, maybe upsert or maybe just none for now.
    update_operations = []

    for url, weather in resp_dict.items():
        airport_code_trailing = str(url)[-3:]
        
        update_operations.append({
            UpdateOne({'code': airport_code_trailing},
                      {'$set': {f'weather.{weather_type}': weather}})
        })
    
    result = collection_weather.bulk_write(update_operations)
    print(result)
    
def datis_processing(resp_dict:dict):
    # datis raw returns is a list of dictionary when resp code is 200 otherwise its a json return as error.
    # This function processess the raw list and returns just the pure datis
    for url,datis in resp_dict.items():
        if not 'error' in datis:
            raw_datis_from_api = json.loads(datis)
            raw_datis = Weather_parse().datis_processing(raw_datis_from_api)
            resp_dict[url]=raw_datis
    return resp_dict

# TODO: This needs to be put in a scheduler like celery.
weather_links_dict = {
    "datis": list_of_weather_links('datis',all_datis_airport_codes),
    "metar": list_of_weather_links('metar',all_mdb_airport_codes),
    "taf": list_of_weather_links('taf',taf_positive_airport_codes),
}

for weather_type, weather_links in weather_links_dict.items():
    # This is one way to do it in the terminal. Or rather outside of the jupyter. Might need dunder name == main for it tho. -check bulk_datis_extrator
    # Check datis bulk extract and bulk weather extract for help on this.
    resp_dict = asyncio.run(resp_dict_returns(weather_links))
    
    # Datis needs special processing before you put into collection. This bit accomplishes it
    if weather_type == 'datis':
        resp_dict = datis_processing(resp_dict)
    
    mdb_updates(resp_dict,weather_type)
    # THATS IT. WORK ON GETTING THAT DATA ON THE FRONTEND AVAILABLE AND HAVE IT HIGHLIGHTED.
    







def weather_field_metar_returns():
    for a, b in test_resp_dict.items():
        airport_id = str(a)[-3:]
        # return just the weather field of the document in question. In this case metar.
        print(collection_weather.find_one({'code': airport_id},{'weather.metar':1}))















# proof of concept for updating a field. Now just need to do multiple at once.:
for a, b in test_resp_dict.items():
    airport_id = str(a)[-3:]
    collection_weather.update_one({'code': airport_id},
    {
        '$set':
        {
            'weather.metar':b
        }
    })
    print(collection_weather.find_one({'code': airport_id}))
    break


def mdb_updates(resp_dict: dict, type_of_weather):
    # This function creates a list of fields/items that need to be upated and passes it as bulk operation to the collection.
    update_operations = []

    for url, weather in test_resp_dict.items():
        airport_id = str(url)[-3:]
        
        update_operations.append({
            UpdateOne({'code': airport_id},
                      {'$set': {f'weather.{type_of_weather}': weather}})
        })
    
    result = collection_weather.bulk_write(update_operations)
    print(result)
    













def x():
    
    # Basics:

    # This returns mongo cursor object. Using for loop you can loop through documents which are essentially python dictionaries.
    collection.find({})    

    # all database
    x = [i for i in collection.find()]
    # return the first one
    print(x[0])

    # Either/or to return the content example of the collection. In this case just the first one. Loop breaaks right after.
    for each_document in collection.find({}):
        def dict_input(doc_dict:dict):
            for a,b in doc_dict.items():
                print(a,b)
        dict_input(doc_dict=each_document)
        break
    for each_d in collection_weather.find():
        print(each_d.keys())
        break

    # Insert one:
    collection.insert_one({'name':'Chicago','code':'ORD', 'weather':'Some_weather'})
    # Find one: Elaborted below see `More on find mdb`
    collection.find_one({'code':'OZR'})     # Returns the whole document - inefficient.
    doc_id = collection.find_one({'code':'OZR'},{'_id':1})       # Returns a specific field from within the document. In this case the '_id' field of the document only. 1 is equivalent to True.
    # Delete a document:
    collection_weather.delete_one({'_id':ObjectId(doc_id)})



    # `More on find mdb`
    # This will request the id item only of the requested document. It is more efficient than [i['_id'] for i in collection.find({'code':'OZR'})]
    # Check the second argument passed in find method. It basically asks to return just the _id field. 1 is equivalelent to true.
    # Check if theere exists a find_many.
    collection.find({'code':'OZR'},{'_id':1})
    # This s inefficient list comprehension since it is fetch intensive on db:
    [i['_id'] for i in collection.find({'code':'OZR'},{'_id':1})]


    for document in collection.find({}):
        airport_code = document['code']
        # Looking up the airport from collection into the weather_collection and inserting metar,taf on the base layer of the document.
        collection_weather.insert_one({'airport':ObjectId(document['_id']),
                                        'weather':{
                                            'metar': '',
                                            'taf': ''}
                                        })

    # Return the weather['metar'] sub-document/sub-field :
    for a, b in test_resp_dict.items():
        airport_id = str(a)[-3:]
        # return just the weather field of the document in question.
        print(collection_weather.find_one({'code': airport_id},{'weather.metar':1}))


    # Attempt to update the document. In this case remove a field(key value pair).
    weather = {             # This weather dict wouldnt be necessary since the unset operator is removing the whole weather field itself.
        'metar':'',
        'taf':'',
        'datis':''
    }
    for each_d in collection_weather.find():
        airport_id = "K"+each_d['code']
    
        collection_weather.update_one(
            {'_id':each_d['_id']},            # This is to direct the update method to the apporpriate id to change that particular document
            
            {'$unset': {'weather':weather}},
            # When you use $unset with the key weather, it removes the entire weather field, not just the contents inside it.
            upsert=True
            )


    # This is the corrected way of deleting the contents of the weather field rather than deleting the whole weather key field instead.
    weather_fields = {
        'weather.metar': '',
        'weather.taf': '',
        'weather.datis': ''
    }
    
    for each_d in collection_weather.find():
        collection_weather.update_one(
            {'_id': each_d['_id']},  # Target the specific document by its _id
            {'$unset': weather_fields},  # Remove the specific fields inside 'weather'
            upsert=True  # Optional: Use with caution, not needed in this case
        )
    







# A powerful and flexible way to efficiently update multiple collections. Master it:
def powerful_aggregatae_way(resp_dict:dict):
    pipeline = [
        {"$match": {"airport_code": {"$in": list(resp_dict.keys())}}},
        {"$addFields": {
            "weather": {
                "$switch": {
                    "branches": [
                        {"case": {"$eq": ["$airport_code", code]}, "then": data}
                        for code, data in resp_dict.items()
                    ],
                    "default": "$weather"
                }
            }
        }},
        {"$merge": {
            "into": "weather_collection",
            "on": "airport_code",
            "whenMatched": "replace",
            "whenNotMatched": "insert"
        }}
    ]
    
    collection_weather.aggregate(pipeline)
    





# legacy: This code was used to init the weather collection documents.
for each_airport in collection.find({}):
    collection_weather.insert_one({'airport_id': each_airport['_id'],
        'code': each_airport['code'],
        'weather': {},
        })





