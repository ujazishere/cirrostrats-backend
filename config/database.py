from pymongo import MongoClient
# import motor.motor_asyncio
from decouple import config


client = MongoClient(config('connection_string'))


# database name
db = client.cirrostrats

# collection name
collection = db['airports']
