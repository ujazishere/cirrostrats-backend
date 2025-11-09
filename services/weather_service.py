import bson
from bson import ObjectId
from core.weather_fetch import Singular_weather_fetch
from core.root_class import AirportValidation
from core.weather_parse import Weather_parse
from typing import Optional

from config.database import collection_airports_cache_legacy, collection_weather_cache
from services.notification_service import send_telegram_notification_service


async def store_live_weather_service(
    mdbAirportReferenceId: Optional[str] = None,
    rawCode: Optional[str] = None,
):
    """ 
    The flow is search_index_collection's referenceID (r_Id) -> collection_airports_cache_legacy' _id -> collection_airports_cache_legacy' code (IATA) -> collection_weather_cache's code (IATA)

    This function fetches live weather and stores it in mdbairport code/mdbAirportReferenceId provided from frontend.
        The mdbAirportReferenceId is a unique identifier passed from frontend using search_index collection's referenceID which is in the collection_airports_cache_legacy' _id.
        that is used retrieve airport 'code' (IATA) from the collection_airports_cache_legacy.
        That airport code is in used to fetch the latest weather from the weather collection .
        This function is called at frontend request to update old data in mongo if it exists.
        """

    # TODO weather: This whole 3 way to using mdbAirportReferenceId to get airport code from collection_airports_cache_legacy then getting associated airport code
        # to get collection_weather_cache seems a bit redundant.
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

    collection_weather_cache_id = collection_weather_cache.find_one(find_crit, return_crit)
    print('collection_weather_cache_id:', collection_weather_cache_id)

    # This is checking if the mdbAirportReferenceId provided from frontend is the same as airport_id from weather collection, if so, it updates the new weather.
    airportReferenceId = collection_weather_cache_id.get('airport_id')
    if collection_weather_cache_id and airportReferenceId:
        if str(airportReferenceId) == mdbAirportReferenceId:

            swf  = Singular_weather_fetch()
            weather_dict = await swf.async_weather_dict(ICAO_airport_code_to_fetch)
        
            collection_weather_cache.update_one(
                {'code': IATA_airport_code},
                {'$set': {'weather': weather_dict},}
            )

    # result = collection_weather_cache.bulk_write(update_operations)
    return {"status": "success"}

async def get_airport_data_service(airport_id):
    """
    Retrieve airport weather data using a flexible airport identifier.

    Args:
        airport_id (str): The identifier for the airport. This can be:
            - A MongoDB BSON ObjectId (as a string)
            - A 4-letter ICAO code
            - A 3-letter IATA code

    Returns:
        dict: Weather data for the airport, with HTML-injected formatting if present. 
            Returns an empty dictionary if no data is found.

    Notes:
        - 4-letter ICAO codes are internally converted to 3-letter IATA codes 
          for querying the MongoDB weather collection.
        - If a BSON ObjectId is provided, it attempts a lookup by airport document ID.
        - Raises ValueError if the id is invalid.
    """

    # Determining find criteria for mongo collection- Airport code/bson id validation for find criteria
    if len(airport_id)<=4:   # ICAO or IATA code
        # validate iata/icao code here and use it as find criteria
        # TODO Weather: Refactor
            # Check the usage and see if the IATA is used at all. if not then convert all to keys as icao instead of 'code' and appropriate value.
            # Seems a lot more appropriate to do that and might just reduce unnecessary processing for
            # validating the airport from root_class.validate_airport_code as that takes another collection to validate the airport code.
        av = AirportValidation()
        # Since mdb takes iata code as airport_code, we need to validate the airport_code and return the iata code.
        airport_data = av.validate_airport_code(airport_id, iata_return=True, supplied_param_type='mdbAirportWeather Route')
        find_crit = {'code': airport_data.get('iata')}
    else:  # Assume bson id, validate it
        # Check if airport_id is a valid ObjectId before using it
        if not ObjectId.is_valid(airport_id):
            send_telegram_notification_service(message=f'airport_code {airport_id} is not a valid ObjectId in get_airport_data_service')
            raise ValueError('Invalid airport ID')
        find_crit = {'airport_id': ObjectId(airport_id)}
        # If not icao or iata code, assume its bson id here.
        # TODO test: error handling here if its not an ObjectId either. It is sommething else - an impossible return.
        try:
            # find_criteria = {'airport_code': ObjectId(airport_code)}
            find_crit = {'airport_id': ObjectId(airport_id)}
        except bson.errors.InvalidId:
            send_telegram_notification_service(message=f'airport_code {airport_id} is not a valid ObjectId in get_airport_data_service')
            # Handle the case where airport_code is not a valid ObjectId
            raise ValueError('Invalid airport ID')

    return_crit = {'weather':1,'code':1,'_id':0}

    # mdb weather returns
    res = collection_weather_cache.find_one(find_crit, return_crit)
    code = res.get('code') if res else None
    if res:
        res = res.get('weather')
        # HTML injection to color code the weather data
        wp = Weather_parse()
        weather = wp.html_injected_weather(weather_raw=res)
        weather.update({'code':code})       # add airport code to the weather dict
        # print('res weather',weather )

        return weather
    else:
        return {}
    
async def liveAirportWeather_service(ICAO_code_to_fetch):
    """ Airport code can be either icao or iata. If its iata it will be converted to icao.
        Fetches live weather from source using icao airport code and returns it."""

    av = AirportValidation()
    # NOTE: The integrity of the function is not verified. This may be an IATA code. check and test pending.
    # Since mdb takes iata code as airport_id, we need to validate the airport_id and return the iata code.
    airport_data = av.validate_airport_id(ICAO_code_to_fetch, icao_return=True, supplied_param_type='mdbAirportWeather Route')
    ICAO_airport_code = airport_data.get('icao')

    # TODO Test: - check if Datis is N/A for 76 of those big airports, if unavailable fire notifications. 
    swf  = Singular_weather_fetch()
    weather_dict = await swf.async_weather_dict(ICAO_code_to_fetch=ICAO_airport_code)

    wp = Weather_parse()
    weather_dict = wp.html_injected_weather(weather_raw=weather_dict)

    return weather_dict