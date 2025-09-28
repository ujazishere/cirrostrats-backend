from typing import Dict, Optional, Union
from bson import ObjectId
from core.weather_fetch import Singular_weather_fetch
from schema.schemas import serialize_document_list
from core.root_class import AirportValidation
from core.weather_parse import Weather_parse
import bson
try:        # This is in order to keep going when collections are not available
    from config.database import collection_airports, collection_weather, collection_searchTrack
    from config.database import collection_flights, db_UJ
except Exception as e:
    print('Mongo collection(Luis) connection unsuccessful\n', e)
from core.root_class import Fetching_Mechanism, Root_source_links
from core.flight_deets_pre_processor import raw_resp_weather_processing


async def store_live_weather_service(
    mdbId: Optional[str] = None,
    rawCode: Optional[str] = None,
):
    """ fetches and saves weather based on airport code provided from frontend.
        This function is called at frontend request to update old data in mongo if it exists."""

    ICAO_code_to_fetch = None           # I could use rawCode here but code wont be as readable.
    if mdbId:
        find_crit = {"_id": ObjectId(mdbId)}
        # Check if the mdbId exists in the collection
        mdb_weather_data = collection_airports.find_one(find_crit, {"code": 1})
        if mdb_weather_data:
            av = AirportValidation()
            iata_code = mdb_weather_data.get('code')
            ICAO_code_to_fetch = av.validate_airport_id(airport_id=iata_code, icao_return=True).get('icao')
        else:
            # Throw a python error if the mdbId is not found
            print("Error: Airport ID not found in the weather collection.")
    elif rawCode:
        return
        # TODO weather: when rawCode is provided, use the rawCode to fetch the ICAO code
            # If saved in the db, it will interfere with celery task since it uses 3 char airport code.
            # This will probably require either a separate collection or meticulous manipulating legacy code(interferers with celery task)
            # Better with a separate collection. Since airport collection will be primary containing popular US airports.
        airport_code_data = av.validate_airport_id(airport_id=rawCode, icao_return=True)
        ICAO_code_to_fetch = airport_code_data.get('icao')
        iata_code = airport_code_data.get('iata')
        # Now all you will have to do is get latest weather to upsert the data in the weather collection based on iata code povided

    swf  = Singular_weather_fetch()
    weather_dict = swf.async_weather_dict(ICAO_code_to_fetch)

    find_crit = {'code': mdb_weather_data.get('code')}
    return_crit = {'airport_id':1,'_id':0}
    cwaid = collection_weather.find_one(find_crit, return_crit)

    if cwaid and cwaid.get('airport_id'):
        if str(cwaid.get('airport_id')) == mdbId:
            print('Already in the database, updating it')
            collection_weather.update_one(
                {'code': mdb_weather_data.get('code')},
                {'$set': {'weather': weather_dict},}
            )

    # result = collection_weather.bulk_write(update_operations)
    return {"status": "success"}

async def get_airport_data_service(airport_id):
    """Airport ID can be bson id itself for mongo or a icao/iata airportID code.
        4 letter ICAO codes are converted to 3 letter IATA codes for mdb weather collection.
    """

    # Airport code/bson id validation for find criteria
    if len(airport_id)<=4:   
        # TODO Efficiency: if a code is provided and found, add it to the mdb airport collection for caching and fetching next time.
                # Maybe even insert a TTL index to auto delete after a certain time period?
        # TODO Weather: Refactor weather collection docs `code` field to reflect if its icao or iata
            # Check the usage and see if the IATA is used at all. if not then convert all to keys as icao instead of 'code' and appropriate value.
            # Seems a lot more appropriate to do that and might just reduce unnecessary processing for
            # validating the airport from root_class.validate_airport_id as that takes another collection to validate the airport code.
        av = AirportValidation()
        # Since mdb takes iata code as airport_id, we need to validate the airport_id and return the iata code.
        airport_data = av.validate_airport_id(airport_id, iata_return=True, supplied_param_type='mdbAirportWeather Route')
        find_crit = {"code": airport_data.get('iata')}
    else:
        # TODO test: error handling here if its not an ObjectId either. It is sommething else - an impossible return.
        try:
            # find_criteria = {"airport_id": ObjectId(airport_id)}
            find_crit = {"airport_id": ObjectId(airport_id)}
        except bson.errors.InvalidId:
            # Handle the case where airport_id is not a valid ObjectId
            raise ValueError("Invalid airport ID")

    return_crit = {'weather':1,'code':1,'_id':0}

    # mdb weather returns
    res = collection_weather.find_one(find_crit, return_crit)
    code = res.get('code') if res else None
    if res:
        res = res.get('weather')
        # TODO VHP Weather: Need to be able to add the ability to see the departure as well as the arrival datis
            # try this: weather = weather.scrape(weather_query, datis_arr=True)
        # HTML injection to color code the weather data
        wp = Weather_parse()
        weather = wp.html_injected_weather(weather_raw=res)
        weather.update({'code':code})       # add airport code to the weather dict
        # print('res weather',weather )

        return weather
    else:
        return {}
    
async def liveAirportWeather_service(airportCode):
    """ Airport code can be either icao or iata. If its iata it will be converted to icao.
        Fetches live weather from source using icao airport code and returns it."""

    # TODO Test: - check if Datis is N/A for 76 of those big airports, if unavailable fire notifications. 

    fm = Fetching_Mechanism()
    rsl = Root_source_links
    av = AirportValidation()

    # Validate airport code and convert to ICAO if IATA is provided.
    airport_data = av.validate_airport_id(airportCode, icao_return=True, supplied_param_type='liveAirportWeather route')
    airportCode =  airport_data.get('icao')

    def link_returns(weather_type, airport_id):
        wl = rsl.weather(weather_type,airport_id)
        return wl

    wl_dict = {weather_type:link_returns(weather_type,airportCode) for weather_type in ('metar', 'taf','datis')}
    resp_dict: dict = await fm.async_pull(list(wl_dict.values()))
    weather_dict = raw_resp_weather_processing(resp_dict=resp_dict, airport_id=airportCode, html_injection=True)
    return weather_dict