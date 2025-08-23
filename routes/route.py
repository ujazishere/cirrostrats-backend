from bson import ObjectId
import bson
from fastapi import APIRouter, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from api.nas import NAS
from models.model import SearchData
import json
from routes.root.EDCT_Lookup import EDCT_LookUp
import requests
from typing import Dict, Optional, Union


try:        # This is in order to keep going when collections are not available
    from config.database import collection_airports, collection_weather, collection_searchTrack
    from config.database import collection_flights, db_UJ
except Exception as e:
    print('Mongo collection(Luis) connection unsuccessful\n', e)

from .root.tests.mock_test_data import Mock_data
from .root.dep_des import Pull_flight_info
from .root.flight_deets_pre_processor import response_filter, raw_resp_weather_processing
from .root.root_class import Fetching_Mechanism, Root_source_links, Source_links_and_api
from .root.root_class import AirportValidation
from .root.search.fuzz_find import fuzz_find
from .root.search.query_classifier import QueryClassifier
from .root.search.search_interface import SearchInterface
from .root.weather_parse import Weather_parse
from schema.schemas import serialize_document_list

app = FastAPI()

""" 
Initializers: These run right as the server starts - scti loads 500 popular suggestions and edct initializes browser.
"""
qc = QueryClassifier(icao_file_path="unique_icao.pkl")
sic_docs = qc.initialize_search_index_collection()      # Caching search index collecion docs;
 

""" Define the origins that are allowed to access the backend --Seems like none of the orgins defined are working. 
TODO CORS: Tried to setup a lightwight ngrok service to host the backend and frontend to host dev operations but
tried and failed - Cors changes on cloudflare(still shows cors issue), adding prints to show origins(doesnt print)
the ip address may have worked but that was throwing http vs https error but even then it wont send the response headers.
Tried nginx changes as well but it did not work. Failed. spin up dev instance on azure just pay small fee for it instead.
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

@router.get('/searches/suggestions/{email}')
# @functools.lru_cache(maxsize=100)         # TODO investigate and check Levenshtein how it supplements fuzzfind
async def get_search_suggestions(email: str, query: str, limit=500):  # Default page and page size
    """Cached fuzzy search to improve performance for repeated queries.
        The Idea is to have some sort of a cache that holds the initial popular fetches of upto 500 items(of the total 3500 sti) in suggestions and display only upto 5 in the drop-down.
        If the suggestions(display dropdown items) drop below 5 items then it should fetch the backend with the `latest query` to see if it returns any matches.
        Current state: Upto 2nd alphabet from `latest query` can match upto maybe <10 items of the 3500 for this cache and return those to the frontend exhausting the 3500 items."""

    ff = SearchInterface()
    # TODO VHP: This maybe it! just flip do fuzzfind first then do the formatting.
    search_suggestions_frontend_format = ff.search_suggestion_frontned_format(c_docs=sic_docs)
    suggestions_match = fuzz_find(query=query, data=search_suggestions_frontend_format, qc=qc, limit=limit)
    if not suggestions_match and len(query)>=3:        # Exhaustion criteria
        # TODO: *****CAUTION**** Bad code exists here. this was a quick fix to account for exhaustion of search suggestions.
        # At exhaustion it will search the extended collections(flight,airport,etc) based on the 'type of query as follows.
        parsed_query = qc.parse_query(query=query)
        print('Exhausted sic docs, parsed query',parsed_query)
        # Attempt to parse the query and do dedicated formating to pass it again to the fuzz find since these collections will be different to search index collection.
        query_field,query_val,query_type = ff.query_type_frontend_conversion(doc=parsed_query)
        if query_type == 'flight':
            # TODO: This is a temporary fix, need to implement a better way. this wont work not ICAO prepended lookups maybe?
            if query_val[:2] == 'DL':       # temporary fix for delta flights
                query_val = 'DAL'+query_val[2:]
            elif query_val[:2] == 'AA' and query_val[:3]!='AAL':       # temporary fix for american flights
                query_val = 'AAL'+query_val[2:]
            # N-numbers returns errors on submits.
            return_crit = {'flightID': 1}
            flight_docs = collection_flights.find({'flightID': {'$regex':query_val}}, return_crit).limit(10)
            search_index = []
            for i in flight_docs:
                x = {
                    'id': str(i['_id']),
                    query_field: i['flightID'],  # Use the field name dynamically
                    'display': i['flightID'],        # Merge code and name for display
                    'type': 'flight',
                }
                search_index.append(x)
            return search_index

        elif query_type == 'airport':
            # TODO: This is a temporary fix, need to implement a better way to handle airport search since it wont look up the airport code.
            # Plus its ugly -- abstract this away since flight ID is using the same logic.
            # TODO: integrate this with searchindex such that it secures it inthe popular hits and moves the submits up the ladder.
            return_crit = {'name': 1, 'code':1}
            case_insensitive_regex_find = {'$regex':query_val, '$options': 'i'}
            
            airport_docs = list(collection_airports.find({'code': case_insensitive_regex_find}, return_crit).limit(10))
            search_index = []
            for i in airport_docs:
                x = {
                    'r_id': str(i['_id']),      # This r_id is used in frontend to access code and weather from mdb
                    query_field: i['code'],     # Use the field name dynamically
                    'display': f"{i['code']} - {i['name']}",        # Merge code and name for display
                    'type': 'airport',
                }
                search_index.append(x)
            if len(search_index) < 2:
                airport_docs = list(collection_airports.find({'name': case_insensitive_regex_find}, return_crit).limit(10))
                for i in airport_docs:
                    x = {
                        'r_id': str(i['_id']),      # This r_id is used in frontend to access code and weather from mdb
                        query_field: i['code'],     # Use the field name dynamically
                        'display': f"{i['code']} - {i['name']}",        # Merge code and name for display
                        'type': 'airport',
                    }
                    search_index.append(x)
            return search_index

    else:
        return suggestions_match



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
    """ Save searches to the DB for tracking and analytics. saves to search index collection"""
    # TODO: Current bug: not tracking searches outside of the sic collection. need to account for all searches.
        # Need to save raw items properly to the sic with proper format and also account for duplicated if it already exists.
    # NOTE: It this good at all to save to search index collection since were using it for suggestions?
            # Maybe returning sic without submits is good for suggestions, and since its 
            # a light weight collection(upto 3000 items) it shouldnt make a huge difference?
            # TODO: But submits can blow up out of proportions ovevrtime?
    
    sic = db_UJ['search_index']   # create/get a collection
    ctrs = db_UJ['test_rst']   # create/get a collection

    # quick view of the search term. dropdown selection or raw search term
    # quick_view_st = data.submitTerm if data.submitTerm else sic.find_one({"_id": ObjectId(data.stId)}, {"_id": 0, "ph": 0, "r_id": 0})
    # 
    # TODO: query should be saved by user.
    update_query = {
        "$setOnInsert": {"email": data.email},  # Only set email on document creation
        "$set": {"lastUpdated": data.timestamp},  # Update timestamp
    }

    oid = {"_id": ObjectId(data.stId)}
    if data.stId:       # if submission with dropdown selection
        doc = sic.find_one(oid)
        if doc:
            if "submits" in doc:
                # If submits exists, just push the new timestamp -- append to the submits array
                sic.update_one(
                    {"_id": ObjectId(data.stId)},
                    {"$push": {"submits": data.timestamp}}
                )
            else:
                # If submits doesn't exist, set it as new array with the timestamp
                sic.update_one(
                    {"_id": ObjectId(data.stId)},
                    {"$set": {"submits": [data.timestamp]}}
                )
        doc = sic.find_one(oid)
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

    sic = db_UJ['search_index']   # create/get a collection
    crts = db_UJ['test_rst']   # create/get a collection

    sic_docs =  list(sic.aggregate([
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
    returns = sic_docs + crts_returns
    return returns


@router.get('/searches/all')
async def get_all_searches():
    
    sic = db_UJ['test_st']   # create/get a collection
    crts = db_UJ['test_rst']   # create/get a collection

    sic_docs = list(sic.find({'submits': {'$exists': True}},{"_id":0,"ph":0,"r_id":0}))
    crts_call_results = list(crts.find({'submits': {'$exists': True}},{"_id":0}))
    all_results = sic_docs + crts_call_results

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
    return si.raw_submit_handler(collection_weather=collection_weather,search=search)

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
async def get_edct_info(flightID: str, origin: str, destination: str):
    el = EDCT_LookUp()
    edct_info = el.extract_edct(call_sign=flightID, origin=origin, destination=destination)
    print(edct_info)
    return edct_info


@router.get('/mdbAirportWeather/{airport_id}')       # you can store the airport_id thats coming from the react as a variable to be used here.
async def get_airport_data(airport_id,):
    """Airport ID can be bson id itself for mongo or a icao/iata airportID code.
        4 letter ICAO codes are converted to 3 letter IATA codes for mdb weather collection.
    """

    # Airport code/bson id validation for find criteria
    if len(airport_id)<=4:   
        # TODO Weather: Refactor weather collection docs `code` field to reflect if its icao or iata
            # Seems a lot more appropriate to do that and might just reduce unnecessary processing for
            # validating the airport from root_class.validate_airport_id
        av = AirportValidation()
        # Since mdb takes iata code as airport_id, we need to validate the airport_id and return the iata code.
        airport_data = av.validate_airport_id(airport_id, iata_return=True, param_name='mdbAirportWeather Route')
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
        weather = wp.processed_weather(weather_raw=res)
        weather.update({'code':code})       # add airport code to the weather dict
        # print('res weather',weather )

        return weather
    else:
        return {}

@router.get("/liveAirportWeather/{airportCode}")
async def liveAirportWeather(airportCode):
    """ Airport code can be either icao or iata. If its iata it will be converted to icao.
        Fetches live weather from source using icao airport code and returns it."""

    # TODO Test: - check if Datis is N/A for 76 of those big airports, if unavailable fire notifications. 

    fm = Fetching_Mechanism()
    rsl = Root_source_links
    av = AirportValidation()

    # Validate airport code and convert to ICAO if IATA is provided.
    airport_data = av.validate_airport_id(airportCode, icao_return=True, param_name='liveAirportWeather route')
    airportCode =  airport_data.get('icao')

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
    # TODO: Canadian airports need to be handled. As of July 2025 throws error in fronend.
    pfi = Pull_flight_info()
    nas = NAS()
    if airport:
        nas_returns = nas.nas_airport_matcher(airport=airport)
    else:
        nas_returns = nas.nas_airport_matcher(departure=departure,destination=destination)
    return nas_returns


@router.get("/gates/{gate}")
async def gate_returns(gate):

    gate_rows_collection = db_UJ['ewrGates']   # create/get a collection
    
    return_crit = {'_id':0}
    find_crit = {'Gate':{'$regex':gate}}
    res = gate_rows_collection.find(find_crit, return_crit)

    ewr_gates = list(res)

    if ewr_gates:
        return ewr_gates


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
