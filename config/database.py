from pymongo import MongoClient
# import motor.motor_asyncio
from decouple import config
import certifi

# print('CONNECTION STRING',config('connection_string'))

# When getting key=value pair error, one of the reason is because the VS code terminal is truncating the connection string
# Updating VS code to the latest buil should fix the issue. If it doesn't,
# Try using command promt window or terminal window outside of VS code instead of using the vs code terminal.
client = MongoClient(config('connection_string'), tlsCAFile=certifi.where())
# client = MongoClient(config('connection_string'))
import certifi


client = MongoClient(config('connection_string'), tlsCAFile=certifi.where())


# database name
db = client.cirrostrats

# collection name
collection = db['airports']
