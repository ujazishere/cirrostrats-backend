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



"""
When getting key=value pair error, one of the reason is because the VS code terminal is truncating the connection string
Updating VS code to the latest build should fix the issue. If it doesn't,
Try using command promt window or terminal window outside of VS code instead of using the vs code terminal.
"""
# print('CONNECTION STRING',config('connection_string'))
client = MongoClient(config('connection_string'), tlsCAFile=certifi.where())
# client = MongoClient(config('connection_string'))



# database name
db = client.cirrostrats


"""
mongodb collections are databaases. Document are set of key value pairs within collections.
These keys are called fields. They maybe nested fields and those are called sub-documents. 
"""

# TODO: HP Similar to the weather colleciton. Need to add the others
# collection name
collection = db['airports']
collection_weather = db['Weather']

collection_gates = db['us-gates']
collection_flights = db['Flights']

# From here on its all custom code for database crud operation.


# This function creates data within the datbase. Currently/previously only used to feed data into database through
    # Python rather than having to manually create items on the mongoDB server through browser.
# TODO: investigate this class. Its supposedely a `type` of the object thing that feeds into mdb.
class Airport(BaseModel):
    name: str
    code: str
def create_airport(airport: Airport):
    result = collection.insert_one({})
    return {'id': str(result.inserted_id)}

# This will add info based on object id and refer to it.
"""

"""