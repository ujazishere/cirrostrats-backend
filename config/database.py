"""
MongoDB database can contain multiple collections and each collection contains multiple documents.
These documents are the key value pairs. Each document is essentially a key value pair. Simpl put, its a dictionary in python lingo.
For e.g there can be a bookstore database within which books can be one collection, authors can be another collection and so on.
a key value pair can be interchangably be reffered to as field or property or just attribute.
"""


from pymongo import MongoClient
# import motor.motor_asyncio
from pydantic import BaseModel
from decouple import config
import certifi

# print('CONNECTION STRING',config('connection_string'))

# When getting key=value pair error, one of the reason is because the VS code terminal is truncating the connection string
# Updating VS code to the latest buil should fix the issue. If it doesn't,
# Try using command promt window or terminal window outside of VS code instead of using the vs code terminal.
client = MongoClient(config('connection_string'), tlsCAFile=certifi.where())
# client = MongoClient(config('connection_string'))

# database name
db = client.cirrostrats

# collection name
collection = db['airports']
collection_gates = db['us-gates']
collection_weather = db['Weather']

# From here on its all custom code for database crud operation.


# This function creates data within the datbase. Currently/previously only used to feed data into database through
    # Python rather than having to manually create items on the mongoDB server through browser.
class Airport(BaseModel):
    name: str
    code: str
def create_airport(airport: Airport):
    result = collection.insert_one({})
    return {'id': str(result.inserted_id)}

# This will add info based on object id and refer to it.
"""
from config.database import collection, collection_weather
from schema.schemas import individual_serial, list_serial, individual_airport_input_data, serialize_airport_input_data
from routes.root.root_class import Root_class, Fetching_Mechanism, Source_links_and_api, Root_source_links
from bson import ObjectId
for i in collection.find({}):
    airport_code = i['code']

    collection_weather.insert_one({'airport':ObjectId(i['_id]),
                                    'metar':'some val',
                                    'taf':'some extra'})
Delete:
# collection_weather.delete_one({'_id':ObjectId(i['_id'])})
Insert one:
# collection.insert_one({'name':'Chicago','code':'ORD', 'weather':'Some_weather'})
Insert many:
# collection.insert_many(
    # icao airports (2000ish)
    # xx
# )

"""