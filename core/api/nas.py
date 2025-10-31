from logging import Logger
import xml.etree.ElementTree as ET
from pymongo import ReplaceOne, UpdateOne
import requests
from core.root_class import AirportValidation

class NASExtracts:

    def nas_xml_fetch(self,):
        nas = "https://nasstatus.faa.gov/api/airport-status-information"
        response = requests.get(nas)
        xml_data = response.content
        return xml_data


    def nas_xml_processor(self):

        xml_raw_data = self.nas_xml_fetch()

        root = ET.fromstring(xml_raw_data) 
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


class NAS:
    def __init__(self) -> None:
        pass


    def mdb_updates(self, ):
        """ Update collecion """
        ne = NASExtracts()
        update_operations = []
        data = ne.nas_xml_processor()
        update_operations.append(
                UpdateOne()
        )

        result = self.gates_collection.bulk_write(update_operations)
        # Logger.info(f"Updated {result.modified_count} documents in the collection, on {update_type}") #


    def nas_airport_matcher(self,**kwargs):
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
            airport_data = av.validate_airport_code(airport_code=airport_id, iata_return=True, supplied_param_type='NAS IATA airport')
            departure_iata_code = airport_data.get('iata')      # Naming singular airport as departure since it feeds through without complications
            destination_iata_code = None
        else:
            airport_data = av.validate_airport_code(departure_id, iata_return=True, supplied_param_type='NAS IATA departure')
            departure_iata_code = airport_data.get('iata')
            destination_iata_code = None
            if destination_id:
                airport_data = av.validate_airport_code(destination_id, iata_return=True, supplied_param_type= 'NAS IATA destination')
                destination_iata_code = airport_data.get('iata')
        
        # Get NAS data
        nas_delays = NASExtracts().nas_xml_processor()
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
            """Get all NAS information pertaining to an airport"""
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
