from datetime import datetime
import json
import pickle
import re
from typing import Dict, Union
from fastapi import APIRouter,FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fuzzywuzzy import fuzz, process
# from levenshtein import levenshtein  # type: ignore
from pydantic import BaseModel
import requests
from decouple import config
from bson import ObjectId

from routes.root.weather_parse import Weather_parse

try:        # This is in order to keep going when collections are not available
    from config.database import collection_airports, collection_weather, collection_gates, collection_searchTrack
except Exception as e:
    print('Mongo collection(Luis) connection unsuccessful\n', e)

from routes.root.search.query_classifier import QueryClassifier
from schema.schemas import serialize_document, serialize_document_list, individual_airport_input_data, serialize_airport_input_data
from .root.test_data_imports import MockTestDataImports
from .root.gate_checker import Gate_checker
from .root.root_class import Root_class, Fetching_Mechanism, Root_source_links, Source_links_and_api
from .root.dep_des import Pull_flight_info
from .root.flight_deets_pre_processor import resp_initial_returns, resp_sec_returns, response_filter, raw_resp_weather_processing
from .root.search.search_data import get_search_suggestion_data

app = FastAPI()
qc = QueryClassifier(icao_file_path="unique_icao.pkl")


test_suggestions = True if config('test_suggestions')=='1' else False
qc.initialize_collections(test_suggestions=test_suggestions)

# Define the origins that are allowed to access the backend
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://18.224.64.51",
    "http://127.0.0.1:8000/",
    ""
    # Add any other origins that should be allowed
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

"""
if you look up http://127.0.0.1:8000/airports this following function will be called.
It is calling the /airports route which automatically calls the async function get_airports()
it looks up the database through `collection` from the config/database.py file
collection has these crud operation methods like find(), insert_one(), insert_many() and delete_one()
The return from the collection is a type - <class 'pymongo.cursor.Cursor'>
it gets sent to list serial to convert the database into python readble format.
This serialize_document_list return is a list type with each item a dict.
Each list item is a mdb document
Check individual_serial to see the dict format.
"""

#_____________________________________________________________________________
""" Tracking, saving and retrieving searches"""
# Define a Pydantic model to validate incoming request data
class SearchData(BaseModel):
    email: str
    searchTerm: Union[str, None]
    submitTerm: Union[str, None]        # submitTerm can be string or null type of variable from react
    submitId: Union[str, None]
    timestamp: datetime


@router.get('/searches/suggestions/{email}')
# @functools.lru_cache(maxsize=100)         # TODO investigate and check Levenshtein how it supplements
# def fuzzy_search_cached(query, limit=100):
async def fetch_most_searched(email: str, query: str, limit=5):  # Default page and page size
    """Cached fuzzy search to improve performance for repeated queries."""
    data = get_search_suggestion_data(c_docs=qc.c_sti_docs)

    # For very short queries, prioritize prefix matching
    if len(query) <= 2:

        # First find exact prefix matches
        prefix_matches = [item for item in data 
                         if item['search_text'].startswith(query.lower())]
        # Return prefix matches if we have enough

        if len(prefix_matches) >= limit:
            return prefix_matches[:limit]
            
        # Otherwise, supplement with fuzzy matches
        remaining = limit - len(prefix_matches)
        search_universe = [item for item in data if item not in prefix_matches]

    else:
        prefix_matches = []
        search_universe = data
        remaining = limit
        parsed_query = qc.parse_query(query)           # Attempt to run the parse query when suggestions are exhausted.
        print('pq', parsed_query)

    # Get search text from all items
    choices = [item['search_text'] for item in search_universe]
    
    # Get fuzzy matches using fuzzywuzzy
    fuzzy_matches = process.extract(
        query.lower(), 
        choices,
        limit=remaining,
        scorer=fuzz.partial_ratio  # Better for autocomplete scenarios
    )
    
    # Get the corresponding items
    fuzzy_items = [search_universe[choices.index(match)] for match, score in fuzzy_matches 
                  if score > 60]  # Minimum similarity threshold
    
    # Combine prefix and fuzzy matches
    return prefix_matches + fuzzy_items



@router.post('/searches/track')
def track_search(data: SearchData):
    
    # This function is called when a user searches for a term. it stores the search term based on email and tracks the count.

    update_query = {
        "$setOnInsert": {"email": data.email},  # Only set email on document creation
        "$set": {"lastUpdated": data.timestamp},  # Update timestamp
    }

    # Create update operation using MongoDB's atomic operators
    if data.submitTerm is None:     # disregard submitTerm if submission is not made and just pass keystrokes
        update_query.update({"$inc": {f"searchTerm.{data.searchTerm}": 1}})     # Increment count
    elif data.submitTerm is not None:       # if submission is made disregard keystrokes(SearchTerm)
        update_query.update({"$inc": {f"submits.{data.submitTerm}.count": 1}})        # Increment count
        if data.submitId is not None:       # if submission contains ID.
            # TODO: Removed objectId from the database. Keeps frontend and backend in sync without ObjectId conversion issue.
            update_query.update({"$set": {f"submits.{data.submitTerm}.id": data.submitId}})  # Ensure ID is stored
    
    # result = collection_searchTrack.update_one(
    #     {"email": data.email},
    #     update_query,
    #     upsert=True
    # )
    print("update_query: ", update_query)

    # return {"status": "success", "matched_count": result.matched_count, "modified_count": result.modified_count}

@router.get('/searches/all')
async def get_all_searches():
    # Shows all the searches that have been made.
    all_results = collection_searchTrack.find({})
    
    return serialize_document_list(all_results)

@router.get('/searches/{email}')
async def get_user_searches(email):
    # Shows all the searches that have been made by the user.
    all_results = collection_searchTrack.find({"email": email})
    return serialize_document_list(all_results)


# @router.get('/searches/suggestions/{email}')
async def fetch_most_searched(email: str, query: str, page: int = 0, page_size: int = 20):  # Default page and page size
    regex_pattern: str = query.upper()

    # Calculate skip value for pagination
    skip = page * page_size
    def call_collection_page(c,regex_pattern,skip,page_size):
        # Perform the query with pagination
        cursor = c.find(
            {'flightID': {'$regex': regex_pattern}},
            {'flightID': 1}
        ).skip(skip).limit(page_size)
        # Convert cursor to list of documents
        results = [doc for doc in cursor]
        # for doc in cursor:
            # doc['type']=
            
        return results

    # results_flights = call_collection_page(collection_flights,regex_pattern,skip,page_size)
    results_airports = call_collection_page(collection_airports,regex_pattern,skip,page_size)
    # results_gates = call_collection_page(collection_gates,regex_pattern,skip,page_size)
    # merged_results = results_flights + results_airports + results_gates
    # results = merged_results
    
    # Get total count for pagination metadata
    total_count = collection_airports.count_documents({'flightID': {'$regex': regex_pattern}})
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    print('TOTALS *****',total_count, total_pages)
    print('results:',results_airports)
    results = results_airports
    results = [i for i in serialize_document_list(results)]  # serialize_document_list(suggestions]  # serialize_document_list(suggestions)

    # Return paginated results with metadata
    data = {"results": results,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages - 1,
            "has_prev": page > 0
        }
    }

    return results


# ____________________________________________________________________________



@router.get('/query')       
# @router.get('/query/{passed_variable}')       # This can be used to get the passed variable.
async def initial_query_processing_react(passed_variable: str = None, search: str = None):
    # This function runs when the auto suggest is exhausted. Intent: processing queries in python, that are unaccounted for in react.
    # This code is present in the react as last resort when dropdown is exhausted.
    # The only reason I have left passed_variable here is for future use of similar variable case.
    # you can store the airport_id thats coming from the react as a variable to be used here in this case it is passed_variable
    print('Last resort since auto suggestion is exhausted. passed_variable:', passed_variable,)
    print('search value:', search)
    # As user types in the search bar this if statement gets triggered.
    
    return None
    # return qc.parse_query(search)
    # if (passed_variable != "airport"):
    #     print('passed_variable is not airport. It is:', passed_variable)
    #     # TODO: Do something here to process the raw search query and return it to the frontend.
    #     return None



# ___________________________________________________________________________

@router.get("/ajms/{flight_number}")
async def aws_jms(flight_number, mock=False):
    # TODO: ***CAUTION values of the dictionary may not be a string. it may be returned in a dict form {'ts':ts,'value':value} -- redis duplcates anomaly
            # still needs work to address dict returns and arrival and destinationAirport mismatch.
    # TODO: Mock data and mock testing crucial. Match it with pattern matching at source such that outlaws are detected and addressed using possibly notifications.
    returns = {}
    try:
        if mock:
            data = mock
            # print('test data', data)
        else:
            data = requests.get(f'http://3.146.107.112:8000/flights/{flight_number}?days_threshold=1')
            data = json.loads(data.text)
        mongo,latest = data.get('mongo'),data.get('latest')

        # This is throughly sought! if mongo and latest both not availbale just return. if either is available just fix them!
        # Data is flowing in popularity increments - latest is the best, mongo is second best
        if not mongo and not latest:
            return {}
        
        elif mongo:     # if mongo availbalem, temporarily fix that cunt first! process it later
            # TODO: This needs fixing. mongo base that is a list type is redundant. just pass the insider dict instead of dict inside of the list since theres only one dict with `flightID` and `matching_versions` for its keys. 
            # Check all areas that it reachs and account for all areas. 
            mongo:dict =  mongo[0]['matching_versions']            # mongo is a list type at the base that has only one dict with keys `flightID` and `matching_versions`. hence magic number 0 to get rid of the base list.
            
        # TODO: Again hazardous!! ****CAUTION*** FIX ASAP! clearance subdoc may not reflect the same as the secondary flight data subdoc..
        if not latest:      # Idea is to get clearance and if found in latest return that and mongo
            print('no latest w mongo')
            latest_mogno = mongo[-1]
            if latest_mogno.get('towerAircraftID') and len(mongo)>=2:
                print('mongo clearance found')
                second_latest_mongo = mongo[-2]
                merged_dict = {**latest_mogno,**second_latest_mongo}
                returns = merged_dict
                # print('here', mongo)
            else:
                print('no latest, no clearance found in mongo, returinng latest mongo only')
                returns = latest_mogno
            # print(mongo)
            # print('found mongo but not latest')
        elif latest:
            print('found latest checking if it has clearance')
            if not latest.get('clearance'):
                print('Latest doesnt have clearance, returning it as is')
                returns = latest
            else:
                print('found clearance in latest')
                if mongo:
                    print('have clearance from latest now updating latest mongo to it')
                    latest_mogno = mongo[-1]
                    if not latest_mogno.get('clearance'):
                        merged_dict = {**latest,**latest_mogno}
                        # print('latest', latest)
                        returns =  merged_dict
                    else:
                        print('!!! found clearance in latest as well as latest_mongo')
                        # TODO: log this data for inspection and notification later on.
                        second_latest_mongo = mongo[-2] if len(mongo)>=2 else {}
                        print('second_latest_mogno',second_latest_mongo)

                        returns = {**latest, **second_latest_mongo}
                elif not mongo:
                    print('NOMAD,No old mongo data for this flight!, investigate!')
                    # This should never be the case unless a flight has never had a history in mongo and flight data has very recently been born and put into latest.
                    returns =  latest
                    
    except Exception as e:
        print(e)

    
    return returns


@router.get("/flightViewGateInfo/{flightID}")
async def ua_dep_dest_flight_status(flightID):
    # dep and destination id pull
    flt_info = Pull_flight_info()
    flightID = flightID.upper()

    airline_code, flightID_digits = qc.prepare_flight_id_for_webscraping(flightID="UCA492")

    united_dep_dest = flt_info.flight_view_gate_info(airline_code=airline_code,flt_num=flightID_digits, departure_airport=None)
    # united_dep_dest = flt_info.united_departure_destination_scrape(airline_code=airline_code,flt_num=flightID, pre_process=None)
    # print('depdes united_dep_dest',united_dep_dest)
    return united_dep_dest


@router.get("/flightStatsTZ/{flightID}")
async def flight_stats_url(flightID,airline_code="UA"):      # time zone pull
    flt_info = Pull_flight_info()
    flightID = flightID.upper()

    airline_code, flightID_digits = qc.prepare_flight_id_for_webscraping(flightID="UCA492")
    
    fs_departure_arr_time_zone = flt_info.flightstats_dep_arr_timezone_pull(
        airline_code=airline_code,flt_num_query=flightID_digits,)
    print('fs_departure_arr_time_zone',fs_departure_arr_time_zone)

    return fs_departure_arr_time_zone


# TODO: Need to account for aviation stack
@router.get("/flightAware/{airline_code}/{flight_number}")
async def flight_aware_w_auth(airline_code, flight_number):
    return None
    # sl.flight_stats_url(flight_number_query),])
    fm = Fetching_Mechanism(flt_num=flight_number)
    sl = Source_links_and_api()
    flt_info = Pull_flight_info()

    link = sl.flight_aware_w_auth(airline_code, flight_number)
    resp_dict: dict = await fm.async_pull([link])

    resp = response_filter(resp_dict, "json",)
    fa_return = resp['flights']
    flight_aware_data = flt_info.fa_data_pull(
        airline_code=airline_code, flt_num=flight_number, pre_process=fa_return)

    # Accounted for gate through flight aware. gives terminal and gate as separate key value pairs.
    return flight_aware_data


@router.get('/mdbAirportWeather/{airport_id}')       # you can store the airport_id thats coming from the react as a variable to be used here.
async def get_airport_data(airport_id, search: str = None):

    # TODO: Temp fix. Find better wayto do this.
    if len(airport_id)<=4:   # airport ID can be bson id itself from mongo or a icao airportID code.
        airport_id = airport_id[1:] if len(airport_id)==4 else airport_id
        find_crit = {"code": airport_id}
    else:
        find_crit = {"airport_id": ObjectId(airport_id)}

    return_crit = {'weather':1,'code':1,'_id':0}

    res = collection_weather.find_one(find_crit, return_crit)
    code = res.get('code') if res else None
    if res:
        res = res.get('weather')
        # TODO: Need to be able to add the ability to see the departure as well as the arrival datis
        # weather = weather.scrape(weather_query, datis_arr=True)
        weather = Weather_parse()
        weather = weather.processed_weather(weather_raw=res)
        weather.update({'code':code})


        return weather

@router.get("/liveAirportWeather/{airportCode}")
async def Weather_raw(airportCode):
    # TODO: Tests - check if Datis is N/A for 76 of those big airports, if unavailable fire notifications. 

    fm = Fetching_Mechanism()
    rsl = Root_source_links

    def link_returns(weather_type, airport_id):
        wl = rsl.weather(weather_type,airport_id)
        return wl
    
    wl_dict = {weather_type:link_returns(weather_type,airportCode) for weather_type in ('metar', 'taf','datis')}
    resp_dict: dict = await fm.async_pull(list(wl_dict.values()))
    weather_dict = raw_resp_weather_processing(resp_dict, airport_id=airportCode)
    return weather_dict

@router.get("/NAS/{departure_id}/{destination_id}")
async def nas(departure_id, destination_id):

    # Probably wont work. If it doesnt its probably because of the reesp_sec_returns
    # does not account for just nas instead going whole mile to get and process weather(unnecessary)
    fm = Fetching_Mechanism()
    sl = Source_links_and_api()
    
    resp_dict: dict = await fm.async_pull([sl.nas()])
    resp_sec = resp_sec_returns(resp_dict, departure_id, destination_id)
    
    nas_returns = resp_sec
    print(nas_returns)

    return nas_returns


@router.get("/testDataReturns")
def test_flight_deet_data():

    bulk_flight_deets:dict = MockTestDataImports()

    return bulk_flight_deets














# ____________________________________________________________________________________

@router.get('/query')       # /query/{passed_variable} can be used tp get the passed variable from frontend
async def initial_query_processing_react(passed_variable: str = None, search: str = None):
    # TODO: Make this function run only when user hits submit. right now it runs soon as the drop down is exhausted.

    # This function runs when the auto suggest is exhausted. Intent: processing queries in python, that are unaccounted for in react.
    # This code is present in the react as last resort when dropdown is exhausted.
    # The only reason I have left passed_variable here is for future use of similar variable case.
    # you can store the airport_id thats coming from the react as a variable to be used here in this case it is passed_variable
    print('Last resort since auto suggestion is exhausted. passed_variable:', passed_variable,)
    print('search value:', search)
    # As user types in the search bar this if statement gets triggered.
    # return None
    return qc.parse_query(search)
    # if (passed_variable != "airport"):
    #     print('passed_variable is not airport. It is:', passed_variable)
    #     # TODO: Do something here to process the raw search query and return it to the frontend.
    #     return None


async def flight_deets(airline_code=None, flight_number_query=None, bypass_fa=True):
    # You dont have to turn this off(False) running lengthy scrape will automatically enable fa pull
    if config('env') == 'production':       # to restrict fa api use: for local use keep it False.       
        bypass_fa = False

    bulk_flight_deets = {}

    # TODO: Priority: Consider Separation of concern. Each individual scrape should be separate function . Also separate scrape from api fetch
    ''' *****VVI******  
    Logic: resp_dict gets all information fetched from root_class.Fetching_Mechanism().async_pull(). Look it up and come back.
    pre-processes it using resp_initial_returns and resp_sec_returns for inclusion in the bulk_flight_deets..
    first async response returs origin and destination through united's flight-status since their argument only
    takes in flightnumber and it als, also gets scheduled times in local time zones through flightstats,
    and the packet from flightaware.
    This origin and destination is then used to make another async request that requires additional arguments
    This is the second resp_dict that returns weather and nas in the resp_sec,
    '''

    sl = Source_links_and_api()
    fm = Fetching_Mechanism(airline_code=airline_code, flt_num=flight_number_query)
    if bypass_fa:

        resp_dict: dict = await fm.async_pull([sl.ua_dep_dest_flight_status(flight_number_query),
                                              sl.flight_stats_url(flight_number_query),])
        # """
        # This is just for testing
        # fa_test_path = r"C:\Users\ujasv\OneDrive\Desktop\codes\Cirrostrats\dj\fa_test.pkl"
        # with open(fa_test_path, 'rb') as f:
        # resp = pickle.load(f)
        # fa_resp = json.loads(resp)
        # resp_dict.update({'https://aeroapi.flightaware.com/aeroapi/flights/UAL4433':fa_resp})
        # """
    else:
        resp_dict: dict = await fm.async_pull([sl.ua_dep_dest_flight_status(flight_number_query),
                                              sl.flight_stats_url(
                                                  flight_number_query),
                                              sl.flight_aware_w_auth(
                                                  airline_code, flight_number_query),
                                               ])
    # /// End of the first async await, next one is for weather and nas ///.

    # flight_deet preprocessing. fetched initial raw data gets fed into their respective pre_processors through this function that iterates through the dict
    resp_initial = resp_initial_returns(
        resp_dict=resp_dict, airline_code=airline_code, flight_number_query=flight_number_query)
    # assigning the resp_initial to their respective variables that will be fed into bulk_flight_deets and..
    # the departure and destination gets used for weather and nas pulls in the second half of the response pu

    united_dep_dest, flight_stats_arr_dep_time_zone, fa_data = resp_initial
    # united_dep_dest,flight_stats_arr_dep_time_zone,flight_aware_data,aviation_stack_data = resp_initial

    # This will init the flight_view for gate info
    # Flightaware data is prefered as source for other data.
    if fa_data['origin']:
        fm = Fetching_Mechanism(flight_number_query,
                        fa_data['origin'], fa_data['destination'])
        sl = Source_links_and_api()
        wl_dict = sl.weather_links(fa_data['origin'], fa_data['destination'])
        # OR get the flightaware data for origin and destination airport ID as primary then united's info.
        # also get flight-stats data. Compare them all for information.

        # fetching weather, nas and gate info since those required departure, destination
        # TODO: Probably take out nas_data from here and put it in the initial pulls.
        resp_dict: dict = await fm.async_pull(list(wl_dict.values())+[sl.nas(),])

        # /// End of the second and last async await.

        # Weather and nas information processing
        resp_sec = resp_sec_returns(
            resp_dict, fa_data['origin'], fa_data['destination'])

        weather_dict = resp_sec

        # This gate stuff is a not async because async is throwig errors when doing async
        gate_returns = Pull_flight_info().flight_view_gate_info(
            flt_num=flight_number_query, departure_airport=fa_data['origin'])
        bulk_flight_deets = {**united_dep_dest, **flight_stats_arr_dep_time_zone,
                             **weather_dict, **fa_data, **gate_returns}
    # If flightaware data is not available use this scraped data. Very unstable. TODO: Change this. Have 3 sources for redundencies
    elif united_dep_dest['departure_ID']:
        fm = Fetching_Mechanism(
            flight_number_query, united_dep_dest['departure_ID'], united_dep_dest['destination_ID'])
        sl = Source_links_and_api()
        wl_dict = sl.weather_links(
            united_dep_dest['departure_ID'], united_dep_dest['destination_ID'])
        # OR get the flightaware data for origin and destination airport ID as primary then united's info.
        # also get flight-stats data. Compare them all for information.

        # fetching weather, nas and gate info since those required departure, destination
        # TODO: Probably take out nas_data from here and put it in the initial pulls.
        resp_dict: dict = await fm.async_pull(list(wl_dict.values())+[sl.nas()])

        # /// End of the second and last async await.
        # /// End of the second and last async await.

        # Weather and nas information processing
        resp_sec = resp_sec_returns(
            resp_dict, united_dep_dest['departure_ID'], united_dep_dest['destination_ID'])

        # Weather and nas information processing
        resp_sec = resp_sec_returns(
            resp_dict, united_dep_dest['departure_ID'], united_dep_dest['destination_ID'])

        weather_dict = resp_sec
        gate_returns = Pull_flight_info().flight_view_gate_info(
            flt_num=flight_number_query, departure_airport=united_dep_dest['departure_ID'])
        bulk_flight_deets = {**united_dep_dest, **flight_stats_arr_dep_time_zone,
                             **weather_dict, **fa_data, **gate_returns}

    else:
        print('No Departure/Destination ID')
        bulk_flight_deets = {**united_dep_dest, **flight_stats_arr_dep_time_zone,
                             **fa_data, }
    # More streamlined to merge dict than just the typical update method of dict. update wont take multiple dictionaries

    # If youre looking for without_futures() that was used prior to the async implementation..
        #  you fan find it in Async milestone on hash dd7ebd0efa3b5a62798c88bcfe77cc43f8c0048c
        # It was an inefficient fucntion to bypass the futures error on EC2

    return bulk_flight_deets


@router.get('/test')
async def get_airports():

    # list_serial only returns id
    mdb = (serialize_document_list(collection_airports.find({})))
    print(mdb[:2])
    for i in mdb[:2]:
        id = i['id']
        name = i['name']
        code = i['code']
        # print(1,id,name,code)


    result = collection_airports.find({})

    return serialize_document_list(result)
