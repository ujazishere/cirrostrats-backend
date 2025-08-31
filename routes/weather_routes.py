from fastapi import APIRouter
from services.weather_service import store_live_weather_service,get_airport_data_service,liveAirportWeather_service
from typing import Optional

router = APIRouter()

@router.post("/storeLiveWeather")
async def store_live_weather(mdbId: Optional[str] = None, rawCode: Optional[str] = None):
    return store_live_weather_service(mdbId=mdbId, rawCode=rawCode)

@router.get('/mdbAirportWeather/{airport_id}')
async def get_airport_data(airport_id):
    return get_airport_data_service(airport_id)

@router.get("/liveAirportWeather/{airportCode}")
async def liveAirportWeather(airportCode):
    return liveAirportWeather_service(airportCode)