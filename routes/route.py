import re
from fastapi import APIRouter,FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models.model import FlightNumber, Airport
from config.database import collection, collection_weather, collection_flights, collection_gates
from schema.schemas import serialize_document, serialize_document_list, individual_airport_input_data, serialize_airport_input_data
from bson import ObjectId
from .root.test_data_imports import test_data_imports
from .root.gate_checker import Gate_checker
from .root.root_class import Root_class, Fetching_Mechanism, Root_source_links, Source_links_and_api
from .root.weather_parse import Weather_parse
from .root.weather_fetch import Weather_fetch
from .root.dep_des import Pull_flight_info
from .root.flight_deets_pre_processor import resp_initial_returns, resp_sec_returns, response_filter, raw_resp_weather_processing
from time import sleep
import os
import pickle
from decouple import config
from .celery_app import celery_app

# This code is only to run outside of celery in case celery doesnt work with async. This organic async should work outside of celery.
# if config('run_weather_fetch'):
#     print('weather_fetch config',config('run_weather_fetch'))
#     print('Running weather fetch...')
#     wf_thread = Weather_fetch_thread()
#     wf_thread.start()
# else:
#     print('weather_fetch not active: ',config('run_weather_fetch'))
#     print(bool(config('run_weather_fetch')))





current_time = Gate_checker().date_time()

app = FastAPI()

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

@router.get('/airports')
async def get_airports():
    # Returns '_id','name' and 'code' as document field keys and values as its values.
    # print('Triggered /airports')
    all_results = collection.find({})
    return serialize_document_list(all_results)


@router.get('/flightNumbers')
async def get_flight_numbers():
    # TODO VHP: Need to add associated details in this collection-dep/des, STD's, gates, weather. Setup celery scheduler to constantly updatae this data. once sent, look for updated info. 
        # Might want to exclude the gates since it can be delayed.
    all_results = collection_flights.find({})
    return serialize_document_list(all_results)


@router.get('/gates')
async def get_us_concourses():
    all_results = collection_gates.find({})
    return serialize_document_list(all_results)


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
    return parse_query(search)
    # if (passed_variable != "airport"):
    #     print('passed_variable is not airport. It is:', passed_variable)
    #     # TODO: Do something here to process the raw search query and return it to the frontend.
    #     return None

@router.get('/airport/{airport_id}')       # you can store the airport_id thats coming from the react as a variable to be used here.
async def get_airport_data(airport_id, search: str = None):
    # This is a drop down selection item that is an airprot.
    # mdb id for airport is passed from react when user selects a drop down item that is an airport.
    print("airport_id", airport_id)
    # serialized_return = serialize_airport_input_data(res)
    res = collection_weather.find_one(
        {"airport_id": ObjectId(airport_id)})
    res = res['weather']
    return res


@router.get('/fetchandstoreWeather')
async def fetchandstoreWeather():
    # TODO: This Wf is just for testing the big fetch. delete this from here. A route for it alreadt exists. Needs to be schedudled every 55 mins for metar and datis, 4 hours for taf,
        # Find a way to schedule this either through a dedicated route via react or just python multi threading.
    # TODO: Make similar for gate fetch and store into mdb and run a scheduler.
    Wf = Weather_fetch()
    print('Starting the big fetch')

#     To fetch live weather use the x line and access http://127.0.0.1:8000/fetchandstore from the browser. It will automatically fetch and save all weather data into the mongodb
#     Check docker terminal logs for progress on  the fetch.
    x = await Wf.fetch_and_store()
    print("finished fetching")

    return None

@router.get("/weatherDisplay/{airportID}")
def weather_display(airportID):
    # This is used in the parse query.
 
    # remove leading and trailing spaces. Seems precautionary.
    airportID = airportID

    weather = Weather_parse()
    # TODO: Need to be able to add the ability to see the departure as well as the arrival datis
    # weather = weather.scrape(weather_query, datis_arr=True)
    weather = weather.processed_weather(query=airportID, )

    weather_page_data = {}

    weather_page_data['airport'] = airportID

    weather_page_data['D_ATIS'] = weather['D-ATIS']
    weather_page_data['METAR'] = weather['METAR']
    weather_page_data['TAF'] = weather['TAF']

    weather_page_data['datis_zt'] = weather['D-ATIS_zt']
    weather_page_data['metar_zt'] = weather['METAR_zt']
    weather_page_data['taf_zt'] = weather['TAF_zt']
    # weather_page_data['trr'] = weather_page_data
    return weather_page_data


# Do not need this
@router.get("/rawQueryTest/{query}")
async def root(query: str = None):
    # Root_class().send_email(body_to_send=query)
    # TODO: This needs to be a parse query first then goes to the flight_deets.
                # WIP: separation of concern for flight deets
                # First get departure and arrival from the flightstats or  ua_dep and arrival and return it back to react.
                # As soon as setLoading is false send that data back top the
    bulk_flight_deet_returns = await ua_dep_dest_flight_status(query)
    print(bulk_flight_deet_returns)

    return bulk_flight_deet_returns


def parse_query(main_query):
    """
    TODO : Deprecate this! get it from the legacy django codebase. this can be handeled in frontend-react
    """
    # Global variable since it is used outside of the if statement in case it was not triggered. purpose: Handeling Error
    query_in_list_form = []
    # if .split() method is used outside here it can return since empty strings cannot be split.

    # splits query. Necessary operation to avoid complexity. Its a quick fix for a deeper more wider issue.
    query_in_list_form = main_query.split()

    # TODO: Log the extent of query reach deep within this code, also log its occurrances to find impossible statements and frequent searches.
    # If query is only one word or item. else statement for more than 1 is outside of this indent. bring it in as an elif statement to this if.
    if len(query_in_list_form) == 1:

        # this is string form instead of list - Taking the only element(first element) of the query and making it uppercase.
        query = query_in_list_form[0].upper()
        flight_pattern = re.compile(r'^(UAL|UA|GJS)(\d+)$')     # ^ matches only for start of the line. would only match trailing pattern that is at the start of a line.
        gate_pattern = re.compile(r'^(A|B|C)|\d{1,3}$')
        # TODO: find a better way to handle this. Maybe regex. Need a system that classifies the query and assigns it a dedicated function like flight_deet or gate query.
        # Accounting for flight number query with leading alphabets
        flight_pattern_match = flight_pattern.fullmatch(query)
        if flight_pattern_match:
            airline_code, flt_digits = flight_pattern_match.groups()
            print('\nSearching for:', airline_code, flt_digits)
            return {'type': 'flightNumber', 'airlineCode': airline_code, 'flightNumber': flt_digits}
        # flight or gate info page returns
        elif len(query) == 4 or len(query) == 3 or len(query) == 2:
            if query.isdigit():
                query = int(query)
                if 1 <= query <= 35 or 40 <= query <= 136:              # Accounting for EWR gates for gate query
                    return gate_info(main_query=str(query))
                else:                                                   # Accounting for fligh number
                    print("INITIATING flight_deets FUNCTION.")
                    return {'flightNumber': query, 'type': 'flightNumber'}
            else:
                if len(query) == 4 and query[0] == 'K':
                    weather_query_airport = query
                    # Making query uppercase for it to be compatible
                    weather_query_airport = weather_query_airport.upper()
                    return {'code': weather_query_airport, 'type': 'airport'}
                else:           # All others
                    print('Accounting for unkown query.')
                    return {'gate': str(query), 'type': 'gate'}
        # Accounting for 1 letter only. Gate query.
        elif 'A' in query or 'B' in query or 'C' in query or len(query) == 1:
            # When the length of query_in_list_form is only 1 it returns gates table for that particular query.
            gate_query = query
            return {'gate': str(gate_query), 'type': 'gate'}
        else:   # return gate
            print('alast resort')
            gate_query = query
            return {'gate': str(gate_query), 'type': 'gate'}

    # its really an else statement but stated >1 here for situational awareness. This is more than one word query.
    elif len(query_in_list_form) > 1:
        # Making it uppercase for compatibility issues and error handling
        first_letter = query_in_list_form[0].upper()
        if first_letter == 'W':
            weather_query_airport = query_in_list_form[1]
            # Making query uppercase for it to be compatible
            weather_query_airport = weather_query_airport.upper()
            return weather_display(weather_query_airport)
        else:
            return gate_info(main_query=' '.join(query_in_list_form))

    else:
        print('Error in query processing. Last resort.')


def gate_info(main_query):
    gate_query = main_query
    # In the database all the gates are uppercase so making the query uppercase
    gate_query = gate_query.upper()
    current_time = Root_class().date_time()

    # This is a list full of dictionararies returned by err_UA_gate depending on what user requested..
    # Each dictionary has 4 key value pair.eg. gate:c10,flight_number:UA4433,scheduled:20:34 and so on
    gate_data_table = Gate_checker().ewr_UA_gate(gate_query)

    # This can be a json to be delivered to the frontend
    data_out = {'gate_data_table': gate_data_table,
                'gate': gate_query, 'current_time': current_time}

    # showing info if the info is found else it falls back to `No flights found for {{gate}}`on flight_info.html
    if gate_data_table:
        # print(gate_data_table)
        return data_out
    else:       # Returns all gates since query is empty. Maybe this is not necessary. TODO: Try deleting else statement.
        return {'gate': gate_query}


async def flight_deets(airline_code=None, flight_number_query=None, ):
    # You dont have to turn this off(False) running lengthy scrape will automatically enable fa pull
    if config('env') == 'production':
        # to restrict fa api use: for local use keep it False.
        bypass_fa = False
    else:
        bypass_fa = True

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
            flt_num=flight_number_query, airport=fa_data['origin'])
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
            flt_num=flight_number_query, airport=united_dep_dest['departure_ID'])
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





@router.get("/DepartureDestination/{flight_number}")
async def ua_dep_dest_flight_status(flight_number):
    # dep and destination id pull
    flt_info = Pull_flight_info()
    flight_number = flight_number.upper()
    if "UA" in flight_number:
        airline_code = flight_number[:2]
        flight_number = flight_number[2:]
    else:
        airline_code = "UA"
    united_dep_dest = flt_info.united_departure_destination_scrape(airline_code=airline_code,flt_num=flight_number, pre_process=None)

    return united_dep_dest


@router.get("/DepartureDestinationTZ/{flight_number}")
async def flight_stats_url(flight_number):      # time zone pull
    flt_info = Pull_flight_info()

    fs_departure_arr_time_zone = flt_info.fs_dep_arr_timezone_pull(
        flt_num_query=flight_number,)

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


@router.get("/Weather/{airport_id}")
async def Weather_raw(airport_id):
    print('airport_id', airport_id)
    # # returns test weather data if airport type is "test"
    # if airport_id == "test":
    #     test_data = {
    #     "datis": "N/A",
    #     "datis_zt": "N/A",
    #     "metar": "KINL 221954Z AUTO 30010G18KT 10SM <span class=\"red_text_color\">BKN008</span> OVC065 11/09 <span class=\"box_around_text\">A2971</span> RMK AO2 RAE1859B24E41 SLP064 P0000 T01060089 ?\n",
    #     "metar_zt": "21 mins ago",
    #     "taf": "KINL 221727Z 2218/2318 28009G16KT 5SM -SHRA OVC025 \n  TEMPO 2218/2220 <span class=\"red_text_color\">2SM</span> -SHRA <span class=\"red_text_color\">BKN008</span> \n  <br>    FM222300 30011G23KT 6SM -SHRA <span class=\"yellow_highlight\">OVC013</span> \n  <br>    FM230900 31009G17KT 6SM BR BKN035\n",
    #     "taf_zt": "168 mins ago"
    #     }
    #     return test_data

    fm = Fetching_Mechanism()
    rsl = Root_source_links

    def link_returns(weather_type, airport_id):
        wl = rsl.weather(weather_type,airport_id)
        return wl
    
    wl_dict = {weather_type:link_returns(weather_type,airport_id) for weather_type in ('metar', 'taf','datis')}
    resp_dict: dict = await fm.async_pull(list(wl_dict.values()))
    weather_dict = raw_resp_weather_processing(resp_dict, airport_id=airport_id)
    
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
    test_data_imports_tuple = test_data_imports()

    # bulk_flight_deets = dummy_imports_tuple[0]
    bulk_flight_deets = test_data_imports_tuple

    print('test_flight_deet_data, test data is being sent')
    bulk_flight_deet_returns = bulk_flight_deets
    
    test_nas_data = {'nas_departure_affected': {'Airport Closure': {'Departure': 'BOS', 'Reason': '!BOS 10/204 BOS AD AP CLSD TO NON SKED TRANSIENT GA ACFT EXC PPR 617-561-2500 2410081559-2411152359', 'Start': 'Oct 08 at 15:59 UTC.', 'Reopen': 'Nov 15 at 23:59 UTC.'}, 'Ground Stop': {'Departure': 'BOS', 'Reason': 'aircraft emergency', 'End Time': '8:45 pm EDT'}},
     'nas_destination_affected': {'Airport Closure': {'Departure': 'BOS', 'Reason': '!BOS 10/204 BOS AD AP CLSD TO NON SKED TRANSIENT GA ACFT EXC PPR 617-561-2500 2410081559-2411152359', 'Start': 'Oct 08 at 15:59 UTC.', 'Reopen': 'Nov 15 at 23:59 UTC.'}, 'Ground Stop': {'Departure': 'BOS', 'Reason': 'aircraft emergency', 'End Time': '8:45 pm EDT'}}}

    test_weather_data = {
    "datis": """EWR <span class="box_around_text">ATIS INFO E</span> 1951Z. 15006KT 10SM FEW250 28/10 <span class="box_around_text">A3020</span> (THREE ZERO TWO ZERO). <span class="box_around_text">ILS RWY 22L APCH IN USE.</span> DEPARTING RY 22R FROM INT W 10,150 FEET TODA. HI-SPEED BRAVO 4 CLSD. TWY NOTAMS, TWY C CLOSED BTWN TWY P AND TWY B. USE CAUTION FOR BIRDS AND CRANES IN THE VICINITY OF EWR. READBACK ALL RUNWAY HOLD SHORT INSTRUCTIONS AND ASSIGNED ALT. ...ADVS YOU HAVE INFO E.""",
    "datis_zt": "N/A",
    "metar": "KINL 221954Z AUTO 30010G18KT 10SM <span class=\"red_text_color\">BKN008</span> OVC065 11/09 <span class=\"box_around_text\">A2971</span> RMK AO2 RAE1859B24E41 SLP064 P0000 T01060089 ?\n",
    "metar_zt": "21 mins ago",
    "taf": "KINL 221727Z 2218/2318 28009G16KT 5SM -SHRA OVC025 \n  TEMPO 2218/2220 <span class=\"red_text_color\">2SM</span> -SHRA <span class=\"red_text_color\">BKN008</span> \n  <br>    FM222300 30011G23KT 6SM -SHRA <span class=\"yellow_highlight\">OVC013</span> \n  <br>    FM230900 31009G17KT 6SM BR BKN035\n",
    "taf_zt": "168 mins ago"
    }
    
    bulk_flight_deet_returns.update(test_nas_data)
    bulk_flight_deet_returns['dep_weather'] = test_weather_data
    bulk_flight_deet_returns['dest_weather'] = test_weather_data

    # # This is the original django dummy weather without the highlight pre-processing.
    # bulk_flight_deet_returns['dep_weather']['datis'] = bulk_flight_deet_returns['dep_weather']['D-ATIS']
    # bulk_flight_deet_returns['dep_weather']['metar'] = bulk_flight_deet_returns['dep_weather']['METAR']
    # bulk_flight_deet_returns['dep_weather']['taf'] = bulk_flight_deet_returns['dep_weather']['TAF']
    # bulk_flight_deet_returns['dest_weather']['datis'] = bulk_flight_deet_returns['dest_weather']['D-ATIS']
    # bulk_flight_deet_returns['dest_weather']['metar'] = bulk_flight_deet_returns['dest_weather']['METAR']
    # bulk_flight_deet_returns['dest_weather']['taf'] = bulk_flight_deet_returns['dest_weather']['TAF']

    # # These are with the html css tags for highlights but the returns are with D-ATIS and such keys and they are not very well processed by react.
    # wp = Weather_parse()            
    # bulk_flight_deet_returns['dep_weather'] = wp.processed_weather(weather_raw=bulk_flight_deet_returns['dep_weather'])
    # print(bulk_flight_deet_returns['dep_weather'])
    # bulk_flight_deet_returns['dest_weather'] = wp.processed_weather(weather_raw=bulk_flight_deet_returns['dest_weather'])

    # print(bulk_flight_deet_returns.keys())
    # bulk_flight_deet_returns = await parse_query(None, query)

    return bulk_flight_deet_returns


@router.get('/dummy')
async def get_airports():
    return test_flight_deet_data()

@router.get('/test')
async def get_airports():

    # list_serial only returns id
    mdb = (serialize_document_list(collection.find({})))
    print(mdb[:2])
    for i in mdb[:2]:
        id = i['id']
        name = i['name']
        code = i['code']
        # print(1,id,name,code)


    result = collection.find({})

    return serialize_document_list(result)
