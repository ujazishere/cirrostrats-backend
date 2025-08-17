import requests
from bs4 import BeautifulSoup as bs4
from .root_class import Root_class
from .flight_aware_data_pull import flight_aware_data_pull
import xml.etree.ElementTree as ET
import re
import pickle
from routes.root.api.flightStats import FlightStatsScraper
from config.database import db_UJ        # UJ mongoDB

'''
This Script pulls the departure and destination when provided with the flight number.
'''
class AirportValidation:
    # TODO: This function probably belongs somewhere in weather? or maybe in rootclass since its validation?
    def __init__(self,):
        self.airport_collection = db_UJ['icao_iata']


    def validate_airport_id(self, airport_id, param_name):
        if isinstance(airport_id, str):
            iata = icao = None
            if len(airport_id) == 3:            # Accounting for flightStats deriveed 3-letter codes
                iata = airport_id
                find_crit = {"iata": iata}  # Example query to find an airport by ICAO code
            elif len(airport_id) == 4:           # This does not work airports outside of us.
                icao = airport_id
                find_crit = {"icao": icao}
            else:
                raise ValueError(f"Invalid {param_name} airport ID: must be 4 or 3 characters. If 4 it should begin with 'K'")
            
            return_crit = {"_id": 0, "iata": 1, "airport": 1}  # Fields to return
            
            result = self.airport_collection.find_one(find_crit,return_crit)  # Example query to find an airport by ICAO code
            return result


class Pull_flight_info(Root_class):

    def __init__(self) -> None:
        # Super method inherits the init method of the superclass. In this case`Root_class`.
        super().__init__()

    def flightstats_dep_arr_timezone_pull(self,airline_code="UA", flt_num_query=None, departure_date:str=None, return_bs4=False):
        
        fss = FlightStatsScraper()
        fs_data = fss.scrape(airline_code=airline_code, flt_num=flt_num_query, return_bs4=return_bs4)
        
        # use this for custom datetime instead 
        # fs_data = fss.scrape(airline_code="UA", flt_num_query="45", departure_date="20250717", return_bs4=False)

        if not fs_data:     # early retur if data isnt found
            return
        
        departure = fs_data.get('fsDeparture')
        arrival = fs_data.get('fsArrival')

        # TODO VHP: Departure and arrival are 3 char returns theyre not ICAO and hence the weathre lookup doesn't work.
        # TODO Test: validation at source - make sure there 3 chars .isalpha mostly but 
                #  can be isnumeric.
                # Flow - return city from fs and fv , match with fuzz find on similarity scale if theyre both same fire up LLM 
        # TODO Test: If this is unavailable, which has been the case latey- May 2024, use the other source for determining scheduled and actual departure and arriavl times
        # TODO VHP: Return Estimated/ Actual to show delay times for the flights.
        bulk_flight_deet = {'flightStatsFlightID': airline_code+flt_num_query,
                            'flightStatsOrigin':departure.get('Code'),
                            'flightStatsDestination':arrival.get('Code'),
                            'flightStatsOriginGate': departure.get('TerminalGate'),
                            'flightStatsDestinationGate': arrival.get('TerminalGate'),
                            'flightStatsScheduledDepartureTime': departure.get('ScheduledTime'),
                            'flightStatsScheduledArrivalTime': arrival.get('ScheduledTime'),
                                            }
        return bulk_flight_deet


    def fa_data_pull(self, airline_code=None,flt_num=None,pre_process=None):
        # """
        # This is just for testing
        # fa_test_path = r"C:\Users\ujasv\OneDrive\Desktop\codes\Cirrostrats\dj\fa_test.pkl"
        # with open(fa_test_path, 'rb') as f:
            # resp = pickle.load(f)
            # fa_resp = json.loads(resp)
        # resp_dict.update({'https://aeroapi.flightaware.com/aeroapi/flights/UAL4433':fa_resp})
        # """
        fa_returns = flight_aware_data_pull(airline_code=airline_code, flt_num=flt_num, pre_process=pre_process)
        return fa_returns


    def nas_final_packet(self,**kwargs):
        """
        Get NAS delay information for airports.
        
        Args:
            airport (str): Single airport ID (4 chars starting with 'K')
            departure (str): Departure airport ID 
            destination (str): Destination airport ID
            
        Usage examples:
            nas_final_packet(airport='KJFK')  # Single airport
            nas_final_packet(departure='KJFK', destination='KLAX')  # Route
        """
    
        # Validate arguments
        valid_keys = {'airport', 'departure', 'destination'}
        provided_keys = set(kwargs.keys())
        if not provided_keys.issubset(valid_keys):
            invalid_keys = provided_keys - valid_keys
            raise ValueError(f"Invalid arguments: {invalid_keys}. Use either 'airport' or 'departure' and 'destination'")
        
        # Determine usage pattern
        if 'airport' in kwargs:
            if 'departure' in kwargs or 'destination' in kwargs:
                raise ValueError("Cannot use 'airport' with 'departure' or 'destination'. Use either single `airport` or `departure` with `destination`.")
            airport_id = kwargs['airport']
            is_single_airport = True
        elif 'departure' in kwargs:
            departure_id = kwargs['departure']
            destination_id = kwargs.get('destination')
            is_single_airport = False
        else:
            raise ValueError("Must provide either 'airport' or 'departure' argument")
        
    
        # Validate airport IDs
        av= AirportValidation()
        if is_single_airport:
            airport_data = av.validate_airport_id(airport_id, 'airport')
            departure_iata_code = airport_data.get('iata')      # Naming singular airport as departure since it feeds through without complications
            destination_iata_code = None
        else:
            airport_data = av.validate_airport_id(departure_id, 'departure')
            departure_iata_code = airport_data.get('iata')
            destination_iata_code = None
            if destination_id:
                airport_data = av.validate_airport_id(destination_id, 'destination')
                destination_iata_code = airport_data.get('iata')
        
        # Get NAS data
        nas_delays = self.nas_pre_processing()
        airport_closures = nas_delays['Airport Closure']
        ground_stop_packet = nas_delays['ground_stop_packet']
        ground_delay_packet = nas_delays['ground_delay_packet']
        arr_dep_del_list = nas_delays['arr_dep_del_list']
    
        def process_airport_data(data_list, airport_code, process_func):
            """Helper function to process airport data"""
            for i, item in enumerate(data_list):
                if item[0] == 'ARPT' and item[1] == airport_code:
                    return process_func(data_list, i, airport_code)
            return None
    
        # Processing functions for each delay type
        def process_closure(data_list, index, airport_code):
            return {
                'Airport Closure': {
                    'Airport': airport_code,
                    'Reason': data_list[index+1][1],
                    'Start': data_list[index+2][1],
                    'Reopen': data_list[index+3][1]
                }
            }
    
        def process_ground_delay(data_list, index, airport_code):
            return {
                'Ground Delay': {
                    'Airport': airport_code,
                    'Reason': data_list[index+1][1],
                    'Average Delay': data_list[index+2][1],
                    'Maximum Delay': data_list[index+3][1]
                }
            }
    
        def process_ground_stop(data_list, index, airport_code):
            return {
                'Ground Stop': {
                    'Airport': airport_code,
                    'Reason': data_list[index+1][1],
                    'End Time': data_list[index+2][1]
                }
            }
    
        def process_arr_dep_delay(data_list, index, airport_code):
            arr_or_dep = data_list[index+2][1]
            return {
                'Arrival/Departure Delay': {
                    'Airport': airport_code,
                    'Reason': data_list[index+1][1],
                    'Type': arr_or_dep.get('Type') if isinstance(arr_or_dep, dict) else arr_or_dep,
                    'Minimum': data_list[index+3][1],
                    'Maximum': data_list[index+4][1],
                    'Trend': data_list[index+5][1]
                }
            }
    
        # Data processing pipeline
        processing_pipeline = [
            (process_closure, airport_closures),
            (process_ground_delay, ground_delay_packet),
            (process_ground_stop, ground_stop_packet),
            (process_arr_dep_delay, arr_dep_del_list)
        ]
    
        def get_airport_delays(airport_code):
            """Get all delay information for a single airport"""
            airport_data = {}
            for process_func, data_list in processing_pipeline:
                result = process_airport_data(data_list, airport_code, process_func)
                if result:
                    airport_data.update(result)
            return airport_data
    
        # Process based on usage pattern
        if is_single_airport:
            # Single airport query
            airport_data = get_airport_delays(departure_iata_code)
            return airport_data if airport_data else {}
        
        else:
            # Route query (departure + optional destination)
            result = {}
            
            # Process departure airport
            departure_data = get_airport_delays(departure_iata_code)
            if departure_data:
                result['nas_affected_departure'] = departure_data
                
            # Process destination airport if provided
            if destination_iata_code:
                destination_data = get_airport_delays(destination_iata_code)
                if destination_data:
                    result['nas_affectred_destination'] = destination_data
            
            return result


    def nas_fetch(self,):
        nas = "https://nasstatus.faa.gov/api/airport-status-information"
        response = requests.get(nas)
        xml_data = response.content
        return xml_data


    def nas_pre_processing(self):

        xml_data = self.nas_fetch()

        root = ET.fromstring(xml_data) 
        update_time = root[0].text

        affected_airports = [i.text for i in root.iter('ARPT')]
        affected_airports = list(set(affected_airports))
        affected_airports.sort()
        # print('dep_des.py nas_pre_processing. NAS affected airports:', affected_airports)

        airport_closures = []
        closure = root.iter('Airport_Closure_List')
        for i in closure:
            for y in i:
                for x in y:
                    airport_closures.append([x.tag, x.text])

        ground_stop_packet = []
        count = 0
        for programs in root.iter('Program'):
            count += 1
            for each_program in programs:
                ground_stop_packet.append([each_program.tag, each_program.text])

        ground_delay_packet = []
        gd = root.iter('Ground_Delay')
        for i in gd:
            for y in i:
                ground_delay_packet.append([y.tag, y.text])

        arr_dep_del_list = []
        addl = root.iter('Arrival_Departure_Delay_List')
        for i in addl:
            for y in i:
                for x in y:
                    if x.tag == 'Arrival_Departure':
                        arr_dep_del_list.append([x.tag, x.attrib])
                    else:
                        arr_dep_del_list.append([x.tag, x.text])
                    for a in x:
                        arr_dep_del_list.append([a.tag, a.text])
        
        # print('dep_des.py Done NAS pull through nas_packet_pull')
        return {'update_time': update_time,
                'affected_airports': affected_airports,
                'ground_stop_packet': ground_stop_packet, 
                'ground_delay_packet': ground_delay_packet,
                'arr_dep_del_list': arr_dep_del_list,
                'Airport Closure': airport_closures
                }


    def aviation_stack_pull(self,):
        return None
    

    def united_departure_destination_scrape(self,airline_code=None, flt_num=None,pre_process=None):         # Depricate. Link doesn't work
        # !!! Deprecated! Link doesn't work
        # print('dep_des.py united_departure_destination_scrape', flt_num, airline_code)
        departure_scheduled_time,destination_scheduled_time = [None]*2
        if not airline_code:
            airline_code = 'UA'
        if pre_process:
            soup = pre_process
        else:
            info = f"https://united-airlines.flight-status.info/{airline_code}-{flt_num}"               # This web probably contains incorrect information.
            # print('info',info)
            soup = self.request(info)
        # Airport distance and duration can be misleading. Be careful with using these. 

        # table = soup.find('div', {'class': 'a2'})
        try: 
            airport_id = soup.find_all('div', {'class': 'a2_ak'})
            airport_id = [i.text for i in airport_id if 'ICAO' in i.text]
            if airport_id:
                departure_ID = airport_id[0].split()[2]
                destination_ID = airport_id[1].split()[2]
                scheduled_times = soup.find_all('div', {'class': 'tb2'})
                scheduled_times = [i.text for i in scheduled_times]
                scheduled_times = [i for i in scheduled_times if 'Scheduled' in i]
                scheduled_times = [match.group() for i in scheduled_times if (match := re.search(r'\d\d:\d\d',i))]
                if scheduled_times: 
                    departure_scheduled_time = scheduled_times[0]
                    destination_scheduled_time = scheduled_times[1]
                # print('dep_des.py united_departure_destination_scrape. Found scheduled times using flight_stats.')
        except Exception as e:
            departure_ID, destination_ID = [None]*2
            print('Error!!! dep_des.py Unable united_departure_destination_scrape', e)
        # print('dep_des.py united_departure_destination_scrape for departure and destination: ', departure_ID, destination_ID)
        return {'departure_ID': departure_ID,
                'destination_ID': destination_ID,
                'departure_scheduled_time': departure_scheduled_time,
                'destination_scheduled_time': destination_scheduled_time
                }


"""
# for use in jupyter
from dep_des import Pull_flight_info

# united scrape mechanism
flt_info = Pull_flight_info()
scrape_all = flt_info.united_departure_destination_scrape(flt_num="4184")

"""