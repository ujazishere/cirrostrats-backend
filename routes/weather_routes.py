from fastapi import APIRouter
from services.weather_service import store_live_weather_service,get_mdb_airport_data_service,liveAirportWeather_service
from typing import Optional

router = APIRouter()

@router.post("/storeLiveWeather")
async def store_live_weather(mdbAirportReferenceId: Optional[str] = None,
                            rawCode: Optional[str] = None):
    # return
    return await store_live_weather_service(mdbAirportReferenceId=mdbAirportReferenceId, rawCode=rawCode)


@router.get('/mdbAirportWeatherById/{airportCacheReferenceId}')
async def get_mdbAirportWeatherById(airportCacheReferenceId):
    return await get_mdb_airport_data_service(airportCacheReferenceId=airportCacheReferenceId)


@router.get('/mdbAirportWeatherByAirportCode/{airportCode}')
async def get_mdbAirportWeatherByAirportCode(airportCode):
    # TODO weather: TODO airport weather, use this in the raw submits. Theres more to this I forgot I walked away from it.
    if len(airportCode) == 4:
        return await get_mdb_airport_data_service(ICAOAirportCode=airportCode)
    elif len(airportCode)== 3:
        return await get_mdb_airport_data_service(IATAAirportCode=airportCode)


@router.get("/liveAirportWeather/{airportCode}")
async def liveAirportWeather(airportCode):
    if len(airportCode) == 4:
        return await liveAirportWeather_service(ICAOAirportCode=airportCode)
    elif len(airportCode)== 3:
        return await liveAirportWeather_service(IATAAirportCode=airportCode)