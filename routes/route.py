from fastapi import APIRouter

from models.model import Flight, Airport
from config.database import collection
from schema.schemas import individual_serial, list_serial
from bson import ObjectId

router = APIRouter()

# get request method


# @router.get('/flight')
# async def get_flights():
#     flights = list_serial(collection.find())
#     return flights


# @router.post('/flight')
# async def add_flight(flight: Flight):
#     response = collection.insert_one(dict(flight))
#     return {"id": str(response.inserted_id)}


@router.get('/airports')
async def get_airports():

    result = collection.find({})
    return list_serial(result)


# airport requested data by id
# the id can be used to search for a specific airport
# data returned is a dictionary wiht the id,name and code of the airport
@router.get('/airports/{airportId}')
async def get_airport_data(airportId):

    res = collection.find_one(
        {"_id": ObjectId(airportId)})

    return individual_serial(res)


# print('airport', airport)
# result = collection.find({})
# return list_serial(result)
# airports = []
# cursor = collection.find({})
# print("airports", airports)
# airports['id'] = str(airports['_id'])
# return await airports.to_list(length=None)
# del [airports['_id']]

# airports = []
# cursor = collection.find({})
# async for document in cursor:
#     airports.append(individual_serial(document))
# return airports


# @router.post('/airports')
# async def new_airport():
# response = collection.find()
# for airport in (await response.to_list(length=100)):
#     airports.append(airport)
# return response

# flights = list_serial(collection.find())
# return flights
