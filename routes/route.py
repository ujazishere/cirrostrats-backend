from datetime import datetime
import json
from typing import Dict, Optional, Union
from routes.root.EDCT_Lookup import EDCT_LookUp
from fastapi import APIRouter, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fuzzywuzzy import fuzz, process
# from levenshtein import levenshtein  # type: ignore
from pydantic import BaseModel
import requests
from decouple import config
from bson import ObjectId

from models.model import SearchData
from routes.root.search.fuzz_find import fuzz_find
from routes.root.weather_parse import Weather_parse

try:        # This is in order to keep going when collections are not available
    from config.database import collection_airports, collection_weather, collection_gates, collection_searchTrack
    from config.database import collection_flights, db_UJ
except Exception as e:
    print('Mongo collection(Luis) connection unsuccessful\n', e)

from .root.search.query_classifier import QueryClassifier
from schema.schemas import serialize_document_list
from .root.tests.mock_test_data import Mock_data
from .root.root_class import Fetching_Mechanism, Root_source_links, Source_links_and_api
from .root.dep_des import Pull_flight_info
from .root.flight_deets_pre_processor import async_resp_returns_processing, response_filter, raw_resp_weather_processing
from .root.search.search_interface import SearchInterface

app = FastAPI()

qc = QueryClassifier(icao_file_path="unique_icao.pkl")
c_sti_docs = qc.initialize_c_sti_collections()      # Caching sti collecion docs;
if not config("env") == "dev":          # If dev skip the selenium
    el = EDCT_LookUp()
 

""" Define the origins that are allowed to access the backend --Seems like none of the orgins defined are working. 
TODO CORS: Setup a lightwight ngrok service to host the backend and frontend and show proof of concept
tried and failed - Cors changes on cloudflare(still shows cors issue), adding prints to show origins(doesnt print)
the ip address may have worked but that was throwing http vs https error but even then it wont send the response headers.
Tried nginx changes as well but it did not work.
"""
origins = [
#    "http://localhost",
#    "http://localhost:5173",
#    "http://18.224.64.51",
#    "http://127.0.0.1:8000/",
    "https://e693-69-120-60-223.ngrok-free.app/",
    "http://e693-69-120-60-223.ngrok-free.app/",
    "https://e693-69-120-60-223.ngrok-free.app",
    "http://e693-69-120-60-223.ngrok-free.app"
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
# Code to test the CORS response headers - Does not work and need troubleshooting.
from starlette.requests import Request
@app.middleware("http")
async def log_cors(request: Request, call_next):
    origin = request.headers.get("origin")
    print(f"Incoming Origin: {origin} | Path: {request.url.path}")
    response = await call_next(request)
    print(f"Outgoing CORS Header: {response.headers.get('access-control-allow-origin')}")
    return response
"""

#_____________________________________________________________________________

# SearhTracking section
@router.get('/searches/suggestions/{email}')
# @functools.lru_cache(maxsize=100)         # TODO investigate and check Levenshtein how it supplements fuzzfind
async def get_search_suggestions(email: str, query: str, limit=500):  # Default page and page size
    """Cached fuzzy search to improve performance for repeated queries.
        The Idea is to have some sort of a bucket that holds the initial popular fetches of upto 500 items(of the total 3500 sti) in suggestions and display only upto 5 in the drop-down.
        If the suggestions(display dropdown items) drop below 5 items then it should fetch the backend with the `latest query` to see if it returns any matches.
        Current state: Upto 2nd alphabet from `latest query` can match upto maybe <10 items of the 3500 for this bucket and return those to the frontend exhausting the 3500 items."""

    ff = SearchInterface()
    # TODO VHP: This maybe it! just flip do fuzzfind first then do the formatting.
    formatted_suggestions = ff.search_suggestion_format(c_docs=c_sti_docs)
    sti_items_match_w_query = fuzz_find(query=query, data=formatted_suggestions, qc=qc, limit=limit)

    # print('sti_items_match_w_query', len(sti_items_match_w_query))
    if not sti_items_match_w_query and len(query)>=3:
        # *****CAUTION**** Bad code exists here. this was a quick fix to account for exhaustion of csti.
        # At exhaustion it will search the collections based on the 'type of query.
        parsed_query = qc.parse_query(query=query)
        print('Exhausted parsed query',parsed_query)
        # Attempt to parse the query and do dedicated formating to pass it again to the fuzz find since these collections will be different to csti.
        val_field,val,val_type = ff.format_conversion(doc=parsed_query)
        if val_type == 'flight':
            # TODO: This is a temporary fix, need to implement a better way. this wont work not ICAO prepended lookups maybe?
            # N-numbers returns errors on submits.
            return_crit = {'flightID': 1}
            c = collection_flights.find({'flightID': {'$regex':val}}, return_crit).limit(10)
            search_index = []
            for i in c:
                x = {
                    'id': str(i['_id']),
                    val_field: i['flightID'],  # Use the field name dynamically
                    'display': i['flightID'],        # Merge code and name for display
                    'type': 'flight',
                }
                search_index.append(x)
            return search_index
                
        elif val_type == 'airport':
            # TODO: This is a temporary fix, need to implement a better way to handle airport search since it wont look up the airport code.
            # Plus its ugly -- abstract this away since flight ID is using the same logic.
            # TODO: integrate this with searchindex such that it secures it inthe popular hits and moves the submits up the ladder.
            return_crit = {'name': 1, 'code':1}
            case_insensitive_regex_find = {'$regex':val, '$options': 'i'}
            c = collection_airports.find({'name': case_insensitive_regex_find}, return_crit).limit(10)
            search_index = []
            for i in c:
                x = {
                    'id': str(i['_id']),
                    val_field: i['code'],  # Use the field name dynamically
                    'display': f"{i['code']} - {i['name']}",        # Merge code and name for display
                    'type': 'airport',
                }
                search_index.append(x)
            return search_index

    else:
        return sti_items_match_w_query



    # # If sti is exhausted, direct query to appropriate index.
    # if sti_items_match_w_query:
    #     print('len if sti',len(sti_items_match_w_query))

    #     return sti_items_match_w_query
    # elif not sti_items_match_w_query:
    #     if len(query)>=3:
    #         parsed_query = qc.parse_query(query=query)
    #         print('Exhausted parsed query',parsed_query)


""" Tracking, saving and retrieving searches"""

@router.post('/searches/track')
def track_search(data: SearchData):
    # Save the search term and timestamp to the database
    
    cts = db_UJ['test_st']   # create/get a collection
    ctrs = db_UJ['test_rst']   # create/get a collection

    # quick view of the search term. dropdown selection or raw search term
    # quick_view_st = data.submitTerm if data.submitTerm else cts.find_one({"_id": ObjectId(data.stId)}, {"_id": 0, "ph": 0, "r_id": 0})
    # 
    # TODO: query should be saved by user.
    update_query = {
        "$setOnInsert": {"email": data.email},  # Only set email on document creation
        "$set": {"lastUpdated": data.timestamp},  # Update timestamp
    }

    oid = {"_id": ObjectId(data.stId)}
    if data.stId:       # if submission with dropdown selection
        doc = cts.find_one(oid)
        if doc:
            if "submits" in doc:
                # If submits exists, just push the new timestamp -- append to the submits array
                cts.update_one(
                    {"_id": ObjectId(data.stId)},
                    {"$push": {"submits": data.timestamp}}
                )
            else:
                # If submits doesn't exist, set it as new array with the timestamp
                cts.update_one(
                    {"_id": ObjectId(data.stId)},
                    {"$set": {"submits": [data.timestamp]}}
                )
        doc = cts.find_one(oid)
    # TODO: This wont account for uniques. Every store is a new store.
    elif data.submitTerm:       # if submission with raw search term
        ctrs.update_one(
            {"rst": data.submitTerm},
            {"$push": {"submits": data.timestamp}},
            upsert=True
        )
    else:
        print("Impossible return!")


@router.get('/searches/timeline')
async def get_search_timeline():
    # Returns a timeline of all searches made by users in exploded fashion.

    cts = db_UJ['test_st']   # create/get a collection
    crts = db_UJ['test_rst']   # create/get a collection

    cts_returns =  list(cts.aggregate([
            { "$match": { "submits": { "$exists": True} } },
            { "$unwind": "$submits" },
            { "$addFields": { "timestamp": "$submits" } },
            { "$unset": ["_id", "r_id", "ph", "submits"] }
        ]))
    crts_returns =  list(crts.aggregate([
            { "$unwind": "$submits" },
            { "$project": {
                "_id": 0,
                "rst": 1,
                "timestamp": "$submits"
            }}
        ]))
    returns = cts_returns + crts_returns
    return returns


@router.get('/searches/all')
async def get_all_searches():
    
    cts = db_UJ['test_st']   # create/get a collection
    crts = db_UJ['test_rst']   # create/get a collection

    cts_all_results = list(cts.find({'submits': {'$exists': True}},{"_id":0,"ph":0,"r_id":0}))
    crts_call_results = list(crts.find({'submits': {'$exists': True}},{"_id":0}))
    all_results = cts_all_results + crts_call_results

    # transformed converts `all_results` which is a list of dicts. Conversions are such:
    # [{'fid_st': 1, 'submits': 2}, {'airport_st': 3, 'submits': 4}] --- > [{1: 2}, {3: 4}]
    transformed = [{v1: v2} for d in all_results for v1, v2 in zip(d.values(), list(d.values())[1:])]
    return serialize_document_list(transformed)

@router.get('/searches/{email}')
async def get_user_searches(email):
    # Supposed to show all the searches that have been made by the user.
    all_results = collection_searchTrack.find({"email": email})
    return serialize_document_list(all_results)


# ____________________________________________________________________________

# Raw search submit handler
@router.get('/query')       
# @router.get('/query/{passed_variable}')       # This can be used to get the passed variable but search already takes care of that.
async def raw_search_handler(search: str = None):
    """ handles the submit that is NOT the drop down suggestion. So just willy nilly taking
    the organic search submit handlling it here by converting to a form that is acceptable in details.jsx"""
    si = SearchInterface()
    return si.submit_handler(collection_weather=collection_weather,search=search)

# ___________________________________________________________________________

# flight data returns

@router.get("/ajms/{flightID}")
async def aws_jms(flightID, mock=False):
    # TODO HP: ***CAUTION values of the dictionary may not be a string. it may be returned in a dict form {'ts':ts,'value':value}. This is due to jms redis duplcates anomaly
            # still needs work to address dict returns and arrival and destinationAirport mismatch.
    # TODO Test: Mock testing and data validation is crucial. Match it with pattern matching at source such that outlaws are detected and addressed using possibly notifications.

    # qc = QueryClassifier()
    # TODO: This airlinecode parsing is dangerous. Fix it. 
    if flightID:
        value = qc.parse_query(flightID).get('value')
        ac = value.get('airline_code')
        fn = value.get('flight_number')
        if ac =='UA':
            flightID = "UAL"+fn
        elif ac == 'DL':
            flightID = "DAL"+fn
        elif ac == 'AA':
            flightID = "AAL"+fn

    returns = {}
    try:
        if mock:
            data = mock
            print('test data', data)
        else:
            data = requests.get(f'http://3.146.107.112:8000/flights/{flightID}?days_threshold=1')
            data = json.loads(data.text)
        mongo,latest = data.get('mongo'),data.get('latest')
        # This is throughly sought! if mongo and latest both not availbale just return. if either is available just fix them!
        # Data is flowing in popularity increments - latest is the best, mongo is second best
        if not mongo and not latest:
            print('No mongo or latest found')
            return {}
        
        elif mongo:     # if mongo availbalem, temporarily fix that cunt first! process it later
            # TODO HP: This needs fixing. mongo base that is a list type is redundant. just pass the insider dict instead of dict inside of the list since theres only one dict with `flightID` and `matching_versions` for its keys. 
            # Check all areas that it reachs and account for all areas. 
            mongo:dict =  mongo[0]['matching_versions']            # mongo is a list type at the base that has only one dict with keys `flightID` and `matching_versions`. hence magic number 0 to get rid of the base list.
            
        # TODO HP: Again hazardous!! ****CAUTION*** FIX ASAP! clearance subdoc may not reflect the same as the secondary flight data subdoc..
        if not latest:      # Idea is to get clearance and if found in latest return that and mongo
            # print('no latest w mongo')
            latest_mogno = mongo[-1]
            if latest_mogno.get('towerAircraftID') and len(mongo)>=2:
                # ('mongo clearance found')
                second_latest_mongo = mongo[-2]
                merged_dict = {**latest_mogno,**second_latest_mongo}
                returns = merged_dict
            else:
                # print('no latest, no clearance found in mongo, returinng latest mongo only')
                returns = latest_mogno
            # print('found mongo but not latest')
        elif latest:
            # print('found latest checking if it has clearance')
            if not latest.get('clearance'):
                # print('Latest doesnt have clearance, returning it as is')
                returns = latest
            else:
                # print('found clearance in latest')
                if mongo:
                    # print('have clearance from latest now updating latest mongo to it')
                    latest_mogno = mongo[-1]
                    if not latest_mogno.get('clearance'):
                        merged_dict = {**latest,**latest_mogno}
                        # print('latest', latest)
                        returns =  merged_dict
                    else:
                        # print('!!! found clearance in latest as well as latest_mongo')
                        # TODO Test: log this data for inspection and notification later on.
                        second_latest_mongo = mongo[-2] if len(mongo)>=2 else {}
                        # print('second_latest_mogno',second_latest_mongo)

                        returns = {**latest, **second_latest_mongo}
                elif not mongo:
                    print('NOMAD,No old mongo data for this flight, just latest!, investigate!')

                    # This shouldn't exist unless a flight has never had a history in mongo and flight data has very recently been born and put into latest.
                    returns =  latest
                    
    except Exception as e:
        print(e)

    route = returns.get('route')
    print('returns', returns)
    if returns.get('route'):
        print('route found', route)
        origin = returns.get('departure')
        destination = returns.get('arrival')
        split_route = route.split('.')
        split_route = split_route[1:-1]
        rh=[]
        if len(split_route)>1:
            for i in split_route:
                rh.append(f"%20{split_route[split_route.index(i)]}")
            rh = ''.join(rh[1:])
            sv = f"https://skyvector.com/?fpl=%20{origin}{rh}%20{destination}"
            returns['faa_skyvector'] = sv
    return returns


@router.get("/flightViewGateInfo/{flightID}")
async def ua_dep_dest_flight_status(flightID):
    # dep and destination id pull
    flightID = flightID.upper()

    flt_info = Pull_flight_info()
    airline_code, flightID_digits = qc.prepare_flight_id_for_webscraping(flightID=flightID)

    united_dep_dest = flt_info.flight_view_gate_info(airline_code=airline_code,flt_num=flightID_digits, departure_airport=None)
    # united_dep_dest = flt_info.united_departure_destination_scrape(airline_code=airline_code,flt_num=flightID, pre_process=None)
    # print('depdes united_dep_dest',united_dep_dest)
    return united_dep_dest


@router.get("/flightStatsTZ/{flightID}")
async def flight_stats_url(flightID):      # time zone pull
    flightID = flightID.upper()

    flt_info = Pull_flight_info()
    airline_code, flightID_digits = qc.prepare_flight_id_for_webscraping(flightID=flightID)
    
    fs_departure_arr_time_zone = flt_info.flightstats_dep_arr_timezone_pull(
        airline_code=airline_code,flt_num_query=flightID_digits,)

    return fs_departure_arr_time_zone


@router.get("/aviationStack/{flight_number}")
async def aviation_stack(flight_number):
    fm = Fetching_Mechanism(flt_num=flight_number)
    sl = Source_links_and_api()
    flt_info = Pull_flight_info()

    link = sl.aviation_stack(flight_number)
    link = sl.flight_aware_w_auth(flight_number)
    resp_dict: dict = await fm.async_pull([link])
    # TODO: This data returns need to handpicked for aviation stack. similar to flt_info.fa_data_pull(pre_process=fa_return)
    return list(resp_dict.values())[0]['data'] 


@router.get("/flightAware/{flight_number}")
async def flight_aware_w_auth(flight_number, mock=False):
    if mock:
        md = Mock_data()
        md.flight_data_init(html_injected_weather=False)
        print('mock flight aware data', md.flightAware)
        return md.flightAware
    
    # sl.flight_stats_url(flight_number_query)
    fm = Fetching_Mechanism(flt_num=flight_number)
    sl = Source_links_and_api()
    flt_info = Pull_flight_info()

    link = sl.flight_aware_w_auth(flight_number)
    resp_dict: dict = await fm.async_pull([link])
    # return resp_dict
    resp = response_filter(resp_dict, "json",)
    fa_return = resp['flights']
    flight_aware_data = flt_info.fa_data_pull(pre_process=fa_return)

    # Accounted for gate through flight aware. gives terminal and gate as separate key value pairs.
    return flight_aware_data


@router.get("/EDCTLookup/{flightID}")
async def get_edct_info(flightID: str, origin: str, destination: str):  # Default page and page size
    # WIP.
    return el.extract_edct(flightID=flightID, origin=origin, destination=destination)


@router.get('/mdbAirportWeather/{airport_id}')       # you can store the airport_id thats coming from the react as a variable to be used here.
async def get_airport_data(airport_id,):

    # TODO VHP Weather: Temp fix. Find better wayto do this. Handle prepend at source find it in celery rabit hole in metar section
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
        # TODO VHP Weather: Need to be able to add the ability to see the departure as well as the arrival datis
        # weather = weather.scrape(weather_query, datis_arr=True)
        weather = Weather_parse()
        weather = weather.processed_weather(weather_raw=res)
        weather.update({'code':code})

        return weather
    else:
        return {}

@router.get("/liveAirportWeather/{airportCode}")
async def liveAirportWeather(airportCode):
    # TODO Test: - check if Datis is N/A for 76 of those big airports, if unavailable fire notifications. 

    fm = Fetching_Mechanism()
    rsl = Root_source_links

    def link_returns(weather_type, airport_id):
        wl = rsl.weather(weather_type,airport_id)
        return wl

    wl_dict = {weather_type:link_returns(weather_type,airportCode) for weather_type in ('metar', 'taf','datis')}
    resp_dict: dict = await fm.async_pull(list(wl_dict.values()))
    weather_dict = raw_resp_weather_processing(resp_dict=resp_dict, airport_id=airportCode, html_injection=True)
    return weather_dict

@router.get("/NAS")
async def nas(
    airport: Optional[str]  = None,
    departure: Optional[str] = None,
    destination: Optional[str] = None
):
    pfi = Pull_flight_info()
    if airport:
        nas_returns = pfi.nas_final_packet(airport=airport)
    else:
        nas_returns = pfi.nas_final_packet(departure=departure,destination=destination)
    return nas_returns


@router.get("/gates/{gate_id}")
async def gate_returns(gate_id):

    return_crit = {'_id':0}
    find_crit = {"_id": ObjectId(gate_id)}
    res = collection_gates.find_one(find_crit, return_crit)
    # code = res.get('code') if res else None
    if res:
        return res


@router.get("/testDataReturns")
async def test_flight_deet_data(airportLookup: str = None):
    md = Mock_data()
    if not airportLookup:
        # Sends compolete test flight data
        md.flight_data_init(html_injected_weather=True)
        return md.collective()
    else:
        # Sends for test data for airport lookups only -- returns test weather and nas data.
        md.flight_data_init(html_injected_weather=True)
        return {'weather': md.weather, 'NAS': md.nas_singular_mock}

# _____________________________________________________________________

# Post 
@router.post("/storeLiveWeather")
async def store_live_weather(
    mdbId: Optional[str] = None,
    rawCode: Optional[str] = None,
):
    """ fetches and saves weather based on airport code provided from frontend. Is called at user request to update old data in mongo if it exists."""
    ICAO_code_to_fetch = None           # I could use rawCode here but code wont be as readable.
    if mdbId:
        find_crit = {"_id": ObjectId(mdbId)}
        # Check if the mdbId exists in the collection
        mdb_weather_data = collection_airports.find_one(find_crit, {"code": 1})
        print('mdb_weather_data', mdb_weather_data)
        if mdb_weather_data:
            ICAO_code_to_fetch = 'K' + mdb_weather_data.get('code')
        else:
            # Throw a python error if the mdbId is not found
            print("Error: Airport ID not found in the weather collection.")
    elif rawCode:
        # TODO: This section is intentionally left blank to handle the case where mdbId is not provided.
            # If saved in the db, it will interfere with celery task since it uses 3 char airport code.
            # This will probably require either a separate collection or meticulous manipulating legacy code(interferers with celery task)
            # Better with a separate collection. Since airport collection will be primary containing popular US airports.
        # If mdbId is not found, use the rawCode to fetch the ICAO code
        # ICAO_code_to_fetch = rawCode
        return

    fm = Fetching_Mechanism()
    rsl = Root_source_links

    def link_returns(weather_type, airport_id):
        wl = rsl.weather(weather_type,airport_id)
        return wl

    wl_dict = {weather_type:link_returns(weather_type,ICAO_code_to_fetch) for weather_type in ('metar', 'taf','datis')}
    resp_dict: dict = await fm.async_pull(list(wl_dict.values()))
    
    weather_dict = raw_resp_weather_processing(resp_dict=resp_dict, airport_id=ICAO_code_to_fetch, html_injection=False)

    cwaid = collection_weather.find_one({'code': mdb_weather_data.get('code')},{'airport_id':1,'_id':0})
    if cwaid and cwaid.get('airport_id'):
        if str(cwaid.get('airport_id')) == mdbId:
            print('Already in the database, updating it')
            collection_weather.update_one(
                {'code': mdb_weather_data.get('code')},
                {'$set': {'weather': weather_dict},}
            )

    # result = collection_weather.bulk_write(update_operations)
    return {"status": "success"}
