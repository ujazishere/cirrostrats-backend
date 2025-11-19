from time import sleep
import bson
from bson import ObjectId
from core.weather_fetch import Singular_weather_fetch
from core.root_class import AirportValidation
from core.weather_parse import Weather_parse
from typing import Optional

from config.database import collection_airports_cache_legacy, collection_weather_cache_legacy, db_UJ
from services.notification_service import send_telegram_notification_service


async def store_live_weather_service(
    mdbAirportReferenceId: Optional[str] = None,
    rawCode: Optional[str] = None,
):
    return
    """ 
    The flow is search_index_collection's referenceID (r_Id) -> collection_airports_cache_legacy' _id -> collection_airports_cache_legacy' code (IATA) -> collection_weather_cache_legacy's code (IATA)

    This function fetches live weather and stores it in mdbairport code/mdbAirportReferenceId provided from frontend.
        The mdbAirportReferenceId is a unique identifier passed from frontend using search_index collection's referenceID which is in the collection_airports_cache_legacy' _id.
        that is used retrieve airport 'code' (IATA) from the collection_airports_cache_legacy.
        That airport code is in used to fetch the latest weather from the weather collection .
        This function is called at frontend request to update old data in mongo if it exists.
        """

    # TODO weather: This whole 3 way to using mdbAirportReferenceId to get airport code from collection_airports_cache_legacy then getting associated airport code
        # to get collection_weather_cache_legacy seems a bit redundant.
    print('r_id, as mdbAirportReferenceId, received in store_live_weather_service:', mdbAirportReferenceId )
    ICAO_airport_code_to_fetch = None           # I could use rawCode here but code wont be as readable.
    if mdbAirportReferenceId:
        # IATA to ICAO conversion
        av = AirportValidation()
        # TODO VHP: multiple airports collection - one for cache and one with all airports 
            # Big problem here is that the airport codes for IATA and ICAO are fetched from two separate collections
                # collection_airports_cache_legacy = db['airports'] and airport_bulk_collection_uj = db_UJ['icao_iata']
        # This section uses both collections to get the ICAO code using mdbAirportReferenceId
            # mdbAirportReferenceId -> collection_airports_cache_legacy -> IATA code -> validate code using -> airport_bulk_collection_uj -> ICAO code
        IATA_airport_code, ICAO_airport_code_to_fetch = av.icao_iata_airport_code_validation(mdbAirportReferenceId)
        # Old code that is currently being abstracted away to AirportValidation()
        """
            # find_crit = {'_id': ObjectId(mdbAirportReferenceId)}
            # return_crit = {'code': 1}
            # # used collection_airports_cache_legacy to get IATA code 
            # IATA_airport_code_collection = collection_airports_cache_legacy.find_one(find_crit, return_crit)
            # if IATA_airport_code_collection:            # if associated airport in collection_airports_cache_legacy found then get its ICAO code
            #     av = AirportValidation()
            #     IATA_airport_code = IATA_airport_code_collection.get('code')
            #     ICAO_airport_code_to_fetch = av.validate_airport_code(airport_code=IATA_airport_code, icao_return=True).get('icao')
            # else:           # This is probably an imposible return
            #     # Throw a python error if the mdbAirportReferenceId is not found
            #     print('Error: airport_code not found in the weather collection.')
        """
    elif rawCode:   # Unused
        return
        # TODO weather: when rawCode is provided, use the rawCode to fetch the ICAO code
            # If saved in the db, it will interfere with celery task since it uses 3 char IATA airport code.
            # This will probably require either a separate collection or meticulous manipulating legacy code(interferers with celery task)
            # Better with a separate collection. Since airport collection will be primary containing popular US airports.
        airport_code_data = av.validate_airport_code(airport_code=rawCode, icao_return=True)
        ICAO_airport_code_to_fetch = airport_code_data.get('icao')
        IATA_airport_code = airport_code_data.get('iata')
        # Now all you will have to do is get latest weather to upsert the data in the weather collection based on iata code povided

    find_crit = {'code': IATA_airport_code}
    return_crit = {'airport_id':1,'_id':0}

    collection_weather_cache_legacy_id = collection_weather_cache_legacy.find_one(find_crit, return_crit)
    print('collection_weather_cache_legacy_id:', collection_weather_cache_legacy_id)

    # This is checking if the mdbAirportReferenceId provided from frontend is the same as airport_id from weather collection, if so, it updates the new weather.
    airportReferenceId = collection_weather_cache_legacy_id.get('airport_id')
    if collection_weather_cache_legacy_id and airportReferenceId:
        if str(airportReferenceId) == mdbAirportReferenceId:

            swf  = Singular_weather_fetch()
            weather_dict = await swf.async_weather_dict(ICAO_airport_code_to_fetch)
        
            collection_weather_cache_legacy.update_one(
                {'code': IATA_airport_code},
                {'$set': {'weather': weather_dict},}
            )

    # result = collection_weather_cache_legacy.bulk_write(update_operations)
    return {"status": "success"}

async def get_mdb_airport_data_service(**kwargs):
    """
    Only serves the purpose of retrieving airport weather from mongoDB
    airport weather cache collection applies html to the returned data using a flexible airport identifier.

    Args:
        airportCacheReferenceId- A MongoDB BSON ObjectId (as a string)
        ICAOAirportCode - A 4-letter ICAO code
        - A 3-letter IATA code         # NOTE: Thinking its best to not include 3 letter IATA code here since find can be extensive with duplicate IATAs around.

    Returns:
        dict: Weather data for the airport from mongodb collection only, with HTML-injected formatting.
            Returns an empty dictionary if no data is found.

    Notes:
        - 4-letter ICAO codes are internally converted to 3-letter IATA codes 
          for querying the MongoDB weather collection.
        - If a BSON ObjectId is provided, it attempts a lookup by airport document ID.
        - Raises ValueError if the id is invalid.
    """
    ICAOAirportCode = kwargs.get('ICAOAirportCode')
    airportCacheReferenceId = kwargs.get('airportCacheReferenceId')
    # Determining find criteria for mongo collection- Airport code/bson id validation for find criteria
    if ICAOAirportCode:

        # validate iata/icao code here and use it as find criteria
        # TODO Weather: Refactor
            # Check the usage and see if the IATA is used at all. if not then convert all to keys as icao instead of 'code' and appropriate value.
            # Seems a lot more appropriate to do that and might just reduce unnecessary processing for
            # validating the airport from root_class.validate_airport_code as that takes another collection to validate the airport code.
        # av = AirportValidation()
        # Since mdb takes iata code as airport_code, we need to validate the airport_code and return the iata code.
        # airport_data = av.validate_airport_code(airport_id, iata_return=True, supplied_param_type='mdbAirportWeatherById Route')
        find_crit = {'ICAO': ICAOAirportCode}
    elif airportCacheReferenceId:
        # Check if airport_id is a valid ObjectId before using it
        if not ObjectId.is_valid(airportCacheReferenceId):
            send_telegram_notification_service(message=f'airport_code {airportCacheReferenceId} is not a valid ObjectId in get_airport_data_service')
            raise ValueError('Invalid airport ID')
        find_crit = {'_id': ObjectId(airportCacheReferenceId)}
        # If not icao or iata code, assume its bson id here.
        # TODO test: error handling here if its not an ObjectId either. It is sommething else - an impossible return.

    return_crit = {'_id':0}

    # mdb weather returns
    new_airport_cache_collection = db_UJ['airport-cache-test']
    new_airport_cache_doc = new_airport_cache_collection.find_one(find_crit, return_crit)
    # weather_cache_doc = collection_weather_cache_legacy.find_one(find_crit, return_crit)
    # print('res', res)
    
    if new_airport_cache_doc:
        weather = new_airport_cache_doc.get('weather')
        # HTML injection to color code the weather data
        wp = Weather_parse()
        weather = wp.html_injected_weather(weather_raw=weather)

        new_airport_cache_doc.update({'weather':weather})
        # weather.update({'code':code})       # add airport code to the weather dict
        # print('res weather',weather )

        return new_airport_cache_doc
    elif not new_airport_cache_doc and ICAOAirportCode:       # New ICAO provided not found in mdb airport cache? fetch live abd aksi save it in airport cache?
        weather = await liveAirportWeather_service(ICAO_code_to_fetch=ICAOAirportCode)
        if weather:
            # TODO insert into airport cache collection
            return weather
    
    
async def liveAirportWeather_service(ICAO_code_to_fetch):
    """ Airport code can be either icao or iata. If its iata it will be converted to icao.
        Fetches live weather from source using icao airport code and returns it."""
    # sleep(3)
    # TODO Test: - check if Datis is N/A for 76 of those big airports, if unavailable fire notifications. 
    swf  = Singular_weather_fetch()
    weather_dict = await swf.async_weather_dict(ICAO_code_to_fetch=ICAO_code_to_fetch)

    wp = Weather_parse()
    weather_dict = wp.html_injected_weather(weather_raw=weather_dict)

    return weather_dict