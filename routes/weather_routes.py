from fastapi import APIRouter
from services.weather_service import store_live_weather_service,get_mdb_airport_data_service,liveAirportWeather_service
from typing import Optional

router = APIRouter()

@router.post("/storeLiveWeather")
async def store_live_weather(mdbAirportReferenceId: Optional[str] = None,
                            rawCode: Optional[str] = None):
    return await store_live_weather_service(mdbAirportReferenceId=mdbAirportReferenceId, rawCode=rawCode)

@router.get('/mdbAirportWeatherById/{airportBsonId}')
# TODO Refactor: Check how you can refactor this airport_id to ICAO/IATA airport code
async def get_mdbAirportWeatherById(airportCacheBsonId):
    print('SIC r_id i.e also airport_id from mdbAirportWeatherById route ', airportCacheBsonId)
    return await get_mdb_airport_data_service(airportCacheBsonId=airportCacheBsonId)

@router.get('/mdbAirportWeatherByAirportCode/{ICAOAirportCode}')
# TODO Refactor: Check how you can refactor this airport_id to ICAO/IATA airport code
async def get_mdbAirportWeatherByAirportCode(ICAOAirportCode):
    return await get_mdb_airport_data_service(ICAO=ICAOAirportCode)

@router.get("/liveAirportWeather/{airportCode}")
async def liveAirportWeather(airportCode):
    return await liveAirportWeather_service(ICAO_code_to_fetch=airportCode)