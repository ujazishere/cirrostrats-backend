from fastapi import APIRouter
from services.weather_service import store_live_weather_service,get_airport_data_service,liveAirportWeather_service
from typing import Optional

router = APIRouter()

@router.post("/storeLiveWeather")
async def store_live_weather(mdbAirportReferenceId: Optional[str] = None,
                            rawCode: Optional[str] = None):
    return await store_live_weather_service(mdbAirportReferenceId=mdbAirportReferenceId, rawCode=rawCode)

@router.get('/mdbAirportWeather/{airport_id}')
# TODO Refactor: Check how you can refactor this airport_id to ICAO/IATA airport code
async def get_airport_data(airport_id):
    print('airport_id from mdbAirportWeather', airport_id)
    return await get_airport_data_service(airport_id)

@router.get("/liveAirportWeather/{airportCode}")
async def liveAirportWeather(airportCode):
    return await liveAirportWeather_service(ICAO_code_to_fetch=airportCode)