"""
MongoDB can contain multiple collections and each collection contains multiple documents.
These documents are the key value pairs. Each document is essentially a key value pair. Simply put, its a dictionary in python lingo.
For e.g there can be a bookstore database within which books can be one collection, authors can be another collection and so on.
a key value pair can be interchangably be reffered to as field or property or just attribute.
"""


from pymongo import MongoClient
# import motor.motor_asyncio
from pydantic import BaseModel
from decouple import config
import certifi

"""
***CAUTION***
When getting key=value pair error, one of the reason is because the VS code terminal is truncating the connection string
Updating VS code to the latest build should fix the issue. If it doesn't,
Try using command promt window or terminal window outside of VS code instead of using the vs code terminal.
To troubeshoot make sure to print the connection string to see whats actuallly being used by the system.
"""
client = MongoClient(config('connection_string'), tlsCAFile=certifi.where())
client_UJ = MongoClient(config('connection_string_uj'), tlsCAFile=certifi.where())
# client = MongoClient(config('connection_string'))

# database name
db = client.cirrostrats
db_UJ = client_UJ.cirrostrats

"""
Think of collection as a database tree.
Collections contains documents and this is the first root branch of the collection tree. These documents have key value pairs.
The key value pairs within the documents are called fields. They maybe nested fields and those are called sub-documents. 
"""


# TODO weather: Fix IATA/ICAO issue - WIP -- collection_airports_cache_legacy documents gotta be migrated to uj collection with appropriate IATA/ICAO
    # 'code' key is used in search_index collection as well.
    # Changing icao would mean changing the search_index collection as well.
    # id's associated with the collection_airports_cache_legacy are used in search_index collection as well for collection cached airports.
    # collection_airports_cache_legacy documents has the IATA codes labeled as 'code' who's id's are referenced in the search_index collection.


# TODO: migrate away from luis's db
collection_airports_cache_legacy = db['airports']
# TODO: SearchTrack is user account based key stroke/ submits - This you may want to migrate too.
collection_searchTrackUsers = db['SearchTrack']

# UJ collections
gate_rows_collection = db_UJ['ewrGates']   # create/get a collection
collection_flights = db_UJ['flights']
collection_weather_cache_legacy = db_UJ['airport-weather']
airport_bulk_collection_uj = db_UJ['icao_iata']
new_airport_cache_collection = db_UJ['airport-cache-test']

# From here on its all custom code for database crud operation.

# This function creates data within the datbase. Currently/previously only used to feed data into database through
    # Python rather than having to manually create items on the mongoDB server through browser.

# This is data type validation. saying create_airport args should have name and code and their restricted type
# TOOD test VHP: this validation sholuld be done at source for collections.

class Airport(BaseModel):
    name: str
    code: str
def create_airport(airport: Airport):
    result = collection_airports_cache_legacy.insert_one({})
    return {'id': str(result.inserted_id)}

# This will add info based on object id and refer to it.