import json
import logging
from core.EDCT_Lookup import EDCT_LookUp
import requests
from core.api.flightStats import FlightStatsScraper
from core.flight_aware_data_pull import Flight_aware_pull
from core.tests.mock_test_data import Mock_data
from core.flight_deets_pre_processor import response_filter
from core.api.source_links_and_api import Source_links_and_api
from core.root_class import Fetching_Mechanism
from core.search.query_classifier import QueryClassifier
from models.model import FlightStatsResponse
from services.notification_service import send_telegram_notification_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

qc = QueryClassifier()

async def aws_jms_service(flightID, mock=False):

    """ 
    This section parses the flightID to get the proper ICAO airline code and flight number for JMS fetching.
    Many frontend users are used to 2 char IATA airline designator code
        for e.g - UA, AA, DL, B6, -- United, American, Delta, Jet Blue
        Their associated 3 char ICAO is UAL, AAL, DAL, JBU

    So if flightID is UA1234, it will parse to  UAL1234 since
    data in JMS is saved with 3 char ICAO airline designator
    """
    # TODO reliability: ***CAUTION values of the dictionary may not be a string. it may be returned in a dict form {'ts':ts,'value':value}. This is due to jms redis duplcates anomaly
            # still needs work to address dict returns and arrival and destinationAirport mismatch within JMS.
    # TODO Test: Mock testing and data validation is crucial. Match it with pattern matching at source such that outlaws are detected and addressed using possibly notifications.

    # TODO search suggestion:
        # This functing may be called straight from frontend with IATA code? -- need to verify this
        # VHP: This is error prone such that UA can be GJS, UCA, SKY, RPA and such from flightstats.
            # could be (GJS/G7), (UCA/C5), SKY, RPA or mesa(ASH/YV) flights. 
            # try to look for AAL, ENY, JIA, PDT - for Envoy, PSA and Piedmont flights. Could also be Skywest or republic flights.
        # One way to present multiple result is through scroll right below the searchbar for multiple digits.
            # if found more than one flightID then let user select the correct one from multiple chouse on search submit.
        # What about part 91 repo flights? those show as UA but use flightStats?
    if flightID:
        # Whole point of this condition is to get associated ICAO using IATA
        parsed_flight_category = qc.parse_flight_query(flightID)
        code_type = parsed_flight_category.get('code_type')
        IATA_airline_code = parsed_flight_category.get('IATA_airline_code')         # Not sure yet how this is appropriate yet but seems like it is - one IATA with multiple regionals ICAO.
        ICAO_airline_code = parsed_flight_category.get('ICAO_airline_code') 
        flight_number = parsed_flight_category.get('flight_number') 

        flightID = ICAO_airline_code+flight_number          # This will account for UA, DL and AA along with all others
        if code_type and code_type == 'IATA':
            codes = Source_links_and_api().IATA_to_ICAO_airline_code_mapping()
            if IATA_airline_code in codes.keys():
                ICAO_airline_code = codes.get(IATA_airline_code)
                flightID = ICAO_airline_code + flight_number
    else:
        return

    # print('flightID ICAO', flightID)



    """ Once the flightID is cleaned up its sent to the JMS API to get flight data.
        JMS saves data into mongoDB as well - collection_flights 
        NOTE: Only reason JMS is used instead of collection_flights is because
            Redis data in JMS is realtime vs jms->collection is saved every few minutes so data in JMS is more current compared to collection.
        The returns from this API has a lot of complexity and this section cleans up to return only the essential/appropriate data.

    """
    returns = {}
    try:
        if mock:
            data = mock
            print('test data', data)
        else:
            data = requests.get(f'http://3.146.107.112:8000/flights/{flightID}?days_threshold=1')
            # This could be used to fetch data from collection_flights insteas of the jms API but it wont be as current.
            # data = collection_flights.find_one({'flightID':flightID})
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


async def flight_stats_frontend_format_service(flightID, return_bs4=None):
    """
    Fetches and validates FlightStats data for a given flight ID.

    Args:
        flightID (str): The flight identifier for e.g UA4433.

    Returns:
        dict or None: Returns a dictionary of validated FlightStats flight information if available and valid,
        otherwise returns None. The dictionary includes keys such as 'flightStatsFlightID', 'flightStatsDelayStatus',
        'flightStatsOrigin', 'flightStatsDestination', 'flightStatsOriginGate', 'flightStatsDestinationGate',
        'flightStatsScheduledDepartureDate', 'flightStatsScheduledDepartureTime', 
        'flightStatsEstimatedDepartureTime', 'flightStatsActualDepartureTime', 
        'flightStatsScheduledArrivalTime', 'flightStatsActualArrivalTime', etc.

    Side Effects:
        Sends a telegram notification and logs validation errors if required data is missing.

    Notes:
        - Attempts to match major ICAO to IATA codes for raw submits.
        - Falls back to error handling/reporting if the necessary data is unavailable.
    """
    flightID = flightID.upper()
    
    # flightStatsData = flt_info.flightStats_data_frontend_format(flightID)
    fss = FlightStatsScraper()
    fs_data = fss.scrape(flightID, return_bs4=return_bs4)
    
    if not fs_data:     # early return if data isnt found
        return
    
    departure = fs_data.get('fsDeparture')
    arrival = fs_data.get('fsArrival')

    # TODO Test: If this is unavailable, which has been the case in - May 2024, use the other source for determining scheduled and actual departure and arriavl times
    flightStatsData = {
        'flightStatsFlightID': flightID,
        'flightStatsDelayStatus': fs_data.get('fsDelayStatus'),
        'flightStatsOrigin':departure.get('Code'),
        'flightStatsDestination':arrival.get('Code'),
        'flightStatsOriginGate': departure.get('TerminalGate'),
        'flightStatsDestinationGate': arrival.get('TerminalGate'),
        # departure date and time
        'flightStatsScheduledDepartureDate': departure.get('ScheduledDate'),    # Date
        'flightStatsScheduledDepartureTime': departure.get('ScheduledTime'),    # Scheduled Time
        'flightStatsEstimatedDepartureTime': departure.get('EstimatedTime'),    # Estimated Time
        'flightStatsActualDepartureTime': departure.get('ActualTime'),          # Actual Time
        # arrival times
        'flightStatsScheduledArrivalTime': arrival.get('ScheduledTime'),        # Scheduled arrival time
        'flightStatsActualArrivalTime': arrival.get('ActualTime'),              # Actual arrival time
        # Multiple flights for same day
        # TODO flight descrepency: add a date befor eand date after as well.
        'flightStatsMultipleFlights': fs_data.get('multipleFlights')
    }

    if flightStatsData:
        try : 
            validated_data = FlightStatsResponse(**flightStatsData)
            return validated_data.model_dump()
        except Exception as e:
            # Accounting for Validation error in case Scheduled date or time is unavailable but most else is available.
            message=f"Flightstats validation error: Flightstats necessary field data not found for {flightID}, Error: {e}, \n data: {flightStatsData}"
            send_telegram_notification_service(message=message)
            logger.error(message)


async def aviation_stack_service(flight_number):
    fm = Fetching_Mechanism(flt_num=flight_number)
    sl = Source_links_and_api()

    link = sl.aviation_stack(flight_number)
    resp_dict: dict = await fm.async_pull([link])
    # TODO: This data returns need to handpicked for aviation stack. similar to flt_info.fa_data_pull(pre_process=fa_return)
    return list(resp_dict.values())[0]['data'] 


async def flight_aware_w_auth_service(ICAO_flight_number, mock=False):
    if mock:
        md = Mock_data()
        md.flight_data_init()
        print('mock flight aware data', md.flightAware)
        return md.flightAware

    sl = Source_links_and_api()
    link = sl.flight_aware_w_auth_url(ICAO_flight_number)

    fm = Fetching_Mechanism(flt_num=ICAO_flight_number)
    resp_dict: dict = await fm.async_pull([link])
    
    resp = response_filter(resp_dict, "json")
    fa_flights = resp.get('flights')
    
    if not fa_flights:         # Return early if no flightdata found.
        # TODO flightAware: consider logging error here instead?
        logger.info('UNSUCCESSFUL!! flight_aware_data_pull.pull FLIGHT_AWARE_DATA, no `flights` available')
        return

    fap = Flight_aware_pull()
    flight_aware_data = fap.extract_flight_aware_data(flights=fa_flights)

    return flight_aware_data


async def get_edct_info_service(flightID: str, origin: str, destination: str):
    el = EDCT_LookUp()
    edct_info = el.extract_edct(call_sign=flightID, origin=origin, destination=destination)
    print(edct_info)
    return edct_info