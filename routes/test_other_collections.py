from pymongo import MongoClient, UpdateOne
# import motor.motor_asyncio
from pydantic import BaseModel
from decouple import config
import certifi
import requests
from bs4 import BeautifulSoup as bs4

client = MongoClient(config('connection_string'), tlsCAFile=certifi.where())
# database name
db = client.cirrostrats

collection_gates = db['US-gates']
collection_flights = db['Flights']

nums = list(range(4300,4600))
flightNumbers = ['UA'+str(i) for i in nums]

update_operations = []

# This will insert flightnumbers in the collection if it doesnt exist.
for i in  flightNumbers[:5]:
    
    update_operations.append(
        UpdateOne({'flightNumber': i},
                  {'$set': {'flightNumber': i}},
                  upsert=True
                  )
    )

result = collection_flights.bulk_write(update_operations)
print(result)



