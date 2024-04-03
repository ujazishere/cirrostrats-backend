from pymongo import MongoClient
# import motor.motor_asyncio
from decouple import config
import certifi


print('connection_string', config('connection_string'))
client = MongoClient(config('connection_string'), tlsCAFile=certifi.where())
# client = MongoClient(config('connection_string'))

# database name
db = client.cirrostrats

# collection name
collection = db['airports']
