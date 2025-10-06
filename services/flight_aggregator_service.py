import json
from core.EDCT_Lookup import EDCT_LookUp
import requests
from core.tests.mock_test_data import Mock_data
from core.dep_des import Pull_flight_info
from core.flight_deets_pre_processor import response_filter
from core.root_class import Fetching_Mechanism, Source_links_and_api
from core.search.query_classifier import QueryClassifier
from models.model import FlightStatsResponse

qc = QueryClassifier(icao_file_path="unique_icao.pkl")
sic_docs = qc.initialize_search_index_collection()



async def aws_jms_service(flightID, mock=False):
    # TODO HP: ***CAUTION values of the dictionary may not be a string. it may be returned in a dict form {'ts':ts,'value':value}. This is due to jms redis duplcates anomaly
            # still needs work to address dict returns and arrival and destinationAirport mismatch.
    # TODO Test: Mock testing and data validation is crucial. Match it with pattern matching at source such that outlaws are detected and addressed using possibly notifications.

    # TODO VHP: Can this not be handled in the frontend in ts or nodejs itself to avoid an extra call?
                # parse_query possibly can be written in ts/node but regardlesss this func would have to be called the same amount?
                #  So better let backend handle it since its server side(reduces frontend processing?) and secure?
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


async def flight_stats_url_service(flightID):      # time zone pull
    flightID = flightID.upper()

    flt_info = Pull_flight_info()
    airline_code, flightID_digits = qc.prepare_flight_id_for_webscraping(flightID=flightID)
    
    fs_departure_arr_time_zone = flt_info.flightstats_dep_arr_timezone_pull(
        airline_code=airline_code,flt_num_query=flightID_digits,)
    if fs_departure_arr_time_zone:
        validated_data = FlightStatsResponse(**fs_departure_arr_time_zone)
        return validated_data.model_dump()
    return fs_departure_arr_time_zone


async def aviation_stack_service(flight_number):
    fm = Fetching_Mechanism(flt_num=flight_number)
    sl = Source_links_and_api()

    link = sl.aviation_stack(flight_number)
    link = sl.flight_aware_w_auth(flight_number)
    resp_dict: dict = await fm.async_pull([link])
    # TODO: This data returns need to handpicked for aviation stack. similar to flt_info.fa_data_pull(pre_process=fa_return)
    return list(resp_dict.values())[0]['data'] 


async def flight_aware_w_auth_service(flight_number, mock=False):
    if mock:
        md = Mock_data()
        md.flight_data_init()
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

async def get_edct_info_service(flightID: str, origin: str, destination: str):
    el = EDCT_LookUp()
    edct_info = el.extract_edct(call_sign=flightID, origin=origin, destination=destination)
    print(edct_info)
    return edct_info