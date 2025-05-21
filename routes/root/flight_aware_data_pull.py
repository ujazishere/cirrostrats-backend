import requests
import pickle
from time import sleep
try:
    from .root_class import Root_class
except:     # Just so it's easier to import outside of django
    from dj.dj_app.root.root_class import Root_class
# from dj.dj_app.root.root_class import Root_class
import re

# TODO VHP: Fix wrong flights showing up. One way is to make the flight aware data prominent
        # But that will cause utc and local time clashes.  redundancies to cross check and verify and use reliable sources.
        # Maybe crosscheck it with other source as primary rathar than other  way around.

class Flight_aware_pull(Root_class):
    def __init__(self) -> None:
        attrs = ['origin','destination','registration',
                 'scheduled_out','estimated_out','scheduled_in',
                 'estimated_in','route','filed_altitude','filed_ete','sv',]
        
        self.attrs = dict(zip(attrs,[None]*len(attrs)))
        
        self.current_utc = self.date_time(raw_utc=True)
        print("null_flightaware_attrs")

    def initial_pull(self, airline_code=None, flt_num=None):
        # apiKey = "G43B7Izssvrs8RYeLozyJj2uQyyH4lbU"         # New Key from Ismail
        apiKey = "mAcMRTxklbWPhTciyaUD9FtCz88klfxk"         # ujasvaghani
        apiUrl = "https://aeroapi.flightaware.com/aeroapi/"
        auth_header = {'x-apikey':apiKey}
        # TODO LP: Instead of getting all data make specific data requests.(optimize queries). Cache updates.
            # Try searching here use /route for specific routes maybe to reduce pull
            # https://www.flightaware.com/aeroapi/portal/documentation#get-/flights/-id-/map
        """
        airport = 'KSFO'
        payload = {'max_pages': 2}
        auth_header = {'x-apikey':apiKey}
        response = requests.get(apiUrl + f"airports/{airport}/flights",
            params=payload, headers=auth_header)

        # fa_flight_id = ""
        # response = requests.get(apiUrl + f"flights/{fa_flight_id}/route", headers=auth_header)
        
        """
        if not airline_code:
            airline_code = 'UAL'
        response = requests.get(apiUrl + f"flights/{airline_code}{flt_num}", headers=auth_header) 
        
        if response.status_code == 200:
            return response.json()['flights']
        else:
            print('UNSUCCESSFUL!! FLIGHT_AWARE RESPONSE STATUS CODE NOT 200!!!', response.status_code)
            return None    


def flight_aware_data_pull(airline_code=None, flt_num=None,pre_process=None, return_example=None):
    """
    return_example is only to check dummy an example data from flightaware and thats used in jupyter. 
    pre_process data is the raw flightaware data through their api thats delivered from the async function.
    """
    # This returns bypass all and return prefabricated None vals
    # return Flight_aware_pull().attrs
    if not airline_code:
        airline_code = 'UAL'
    
    fa_object = Flight_aware_pull()
    if return_example:
        # Use this to recall a dummy flight packet:
        print('sleeping 4 secs for flight_aware data fetch lag simulation')
        sleep(4)
        print('\n CALLING DUMMY FILE IN flight_aware_data_pull \n')
        with open ('dummy_flight_aware_packet.pkl', 'rb') as f:
            flights = pickle.load(f)
    else:
        if pre_process:
            print('Received flight aware data as pre_process')
            flights = pre_process
        elif flt_num:
            flights = fa_object.initial_pull(airline_code=airline_code,flt_num=flt_num)
        else:
            # Reason here is to return none items when no flight aware data is found. It eventually returns fa_object.attrs that just declares all keys and vals
            print('returning null flight_aware_data')
            flights = None
            pass
    
    current_UTC = Flight_aware_pull().current_utc
    route = None        # Declaring not available unless available through flights
    filed_altitude, filed_ete,  = None, None
    
    # Use this to dump a dummy flight packet:
        # with open('dummy_flight_aware_packet.pkl', 'wb') as f:
        # pickle.dump(flights,f)

    """
    Prototype for reducing the code
        You will need to delete the 'sv' key since its not associated with flight_aware.
        this will associate all keys with associated flight_aware values as long as 
            neither of them are None. if either value is None it'll clean all values back to none 

    for i in range(len(flights)):
        print(i)
        for a, b in flights[i].items():     #looping through each of ~15 dicts within a list
            if a in fa_object.attrs.keys():
                if type(b) == dict:
                    fa_object.attrs[a] = b['code'] 
                else:
                    fa_object.attrs[a] = b
        if not None in  fa_object.attrs.values():
            print(i)
            break
        for keys,vals in fa_object.attrs.items():
            if not vals:
                print(keys, vals)
                print('vals are none')
                for y in fa_object.attrs.keys():
                    fa_object.attrs[y]=None 
        
    """

    """
    # these flights are across 10 days and hence iter across them
    for i in range(len(flights)):
        fa_flight_id = flights[i]['fa_flight_id']
        origin = flights[i]['origin']['code_icao']
        destination = flights[i]['destination']['code_icao']
        scheduled_out = flights[i]['scheduled_out']
        estimated_out = flights[i]['estimated_out']
        actual_out = flights[i]['actual_out']
        scheduled_off = flights[i]['scheduled_off']
        estimated_off = flights[i]['estimated_off']
        actual_off = flights[i]['actual_off']
        scheduled_on = flights[i]['scheduled_on']
        estimated_on = flights[i]['estimated_on']
        actual_on = flights[i]['actual_on']
        scheduled_in = flights[i]['scheduled_in']
        estimated_in = flights[i]['estimated_in']
        actual_in = flights[i]['actual_in']
        
        route = flights[i]['route']
        gate_origin = flights[i]['gate_origin']
        gate_destination = flights[i]['gate_destination']
        terminal_origin = flights[i]['terminal_origin']
        terminal_destination = flights[i]['terminal_destination']
        registration = flights[i]['registration']
        departure_delay = flights[i]['departure_delay']
        arrival_delay = flights[i]['arrival_delay']
        filed_ete = flights[i]['filed_ete']
        filed_altitude = flights[i]['filed_altitude']
    """
    """
        Keys and vals provided by flightaware
        [{'ident': 'UAL1411',
        'ident_icao': 'UAL1411',
        'ident_iata': 'UA1411',
        'actual_runway_off': None,
        'actual_runway_on': None,
        'fa_flight_id': 'UAL1411-1722246510-fa-1082p',
        'operator': 'UAL',
        'operator_icao': 'UAL',
        'operator_iata': 'UA',
        'flight_number': '1411',
        'registration': 'N37554',
        'atc_ident': None,
        'inbound_fa_flight_id': 'UAL2729-1722246555-fa-990p',
        'codeshares': ['ACA3128', 'DLH7805'],
        'codeshares_iata': ['AC3128', 'LH7805'],
        'blocked': False,
        'diverted': False,
        'cancelled': False,
        'position_only': False,
        'origin': {'code': 'KCLE',
        'code_icao': 'KCLE',
        'code_iata': 'CLE',
        'code_lid': 'CLE',
        'timezone': 'America/New_York',
        'name': 'Cleveland-Hopkins Intl',
        'city': 'Cleveland',
        'airport_info_url': '/airports/KCLE'},
        'destination': {'code': 'KEWR',
        'code_icao': 'KEWR',
        'code_iata': 'EWR',
        'code_lid': 'EWR',
        'timezone': 'America/New_York',
        'name': 'Newark Liberty Intl',
        'city': 'Newark',
        'airport_info_url': '/airports/KEWR'},
        'departure_delay': 0,
        'arrival_delay': 0,
        'filed_ete': 4740,
        'foresight_predictions_available': False,
        'scheduled_out': '2024-07-31T21:20:00Z',
        'estimated_out': '2024-07-31T21:20:00Z',
        'actual_out': None,
        'scheduled_off': '2024-07-31T21:30:00Z',
        'estimated_off': '2024-07-31T21:30:00Z',
        'actual_off': None,
        'scheduled_on': '2024-07-31T22:49:00Z',
        'estimated_on': '2024-07-31T22:49:00Z',
        'actual_on': None,
        'scheduled_in': '2024-07-31T22:59:00Z',
        'estimated_in': '2024-07-31T22:59:00Z',
        'actual_in': None,
        'progress_percent': 0,
        'status': 'Scheduled',
        'aircraft_type': 'B39M',
        'route_distance': 404,
        'filed_airspeed': 267,
        'filed_altitude': None,
        'route': None,
        'baggage_claim': None,
        'seats_cabin_business': None,
        'seats_cabin_coach': None,
        'seats_cabin_first': None,
        'gate_origin': 'C24',
        'gate_destination': None,
        'terminal_origin': None,
        'terminal_destination': 'A',
        'type': 'Airline'},
    """

    if flights:     # sometimes flights returns empty list.
        for i in range(len(flights)):      # There are typically 15 of these for multiple dates
            scheduled_out_raw_fa = flights[i]['scheduled_out']
            date_out = scheduled_out_raw_fa[:10].replace('-', '')       # This needs to be checked with current UTC time
            if flights[i]['route']:
                ident_icao = flights[i]['ident_icao']
                origin = flights[i]['origin']['code_icao']
                destination = flights[i]['destination']['code_icao']
                registration = flights[i]['registration']
                terminal_origin = flights[i]["terminal_origin"]
                terminal_destination = flights[i]["terminal_destination"]
                gate_origin = flights[i]["gate_origin"]
                gate_destination = flights[i]["gate_destination"]

                scheduled_out_raw_fa = flights[i]['scheduled_out']
                date_out = scheduled_out_raw_fa[:10].replace('-', '')       # This needs to be checked with current UTC time
                # print('Current_UTC', current_UTC)
                # print('Date_out', date_out)
                
                if current_UTC == date_out:     # zulu time clashes with local time from other source
                    pass
                
                # TODO LP: use the Cirrostrats\dj\dummy_flight_aware_packet.pkl to get the `flights` section then do the pre-processing on this.
                # print("scheduled out Z: ", scheduled_out_raw_fa)
                scheduled_out = re.search(r"T(\d{2}:\d{2})", scheduled_out_raw_fa).group(1).replace(":","") + "Z"
                estimated_out = flights[i]['estimated_out']     # Rename this to date or time or both 
                # print("estimated out Z: ",estimated_out)
                estimated_out = re.search(r"T(\d{2}:\d{2})", estimated_out).group(1).replace(":","") + "Z"

                scheduled_in = flights[i]['scheduled_in']
                scheduled_in = re.search(r"T(\d{2}:\d{2})", scheduled_in).group(1).replace(":","") + "Z"
                estimated_in = flights[i]['estimated_in']
                estimated_in = re.search(r"T(\d{2}:\d{2})", estimated_in).group(1).replace(":","") + "Z"

                route = flights[i]['route']
                filed_altitude =  "FL" + str(flights[i]['filed_altitude'])
                filed_ete = flights[i]['filed_ete']

                rs = route.split()
                if len(rs) > 1:
                    rh = []
                    for i in rs:
                        rh.append(f"%20{rs[rs.index(i)]}")
                    rh = ''.join(rh)
                sv = f"https://skyvector.com/?fpl=%20{origin}{rh}%20{destination}"

                # sv = f"https://skyvector.comi/api/lchart?fpl=%20{origin}{rh}%20{destination}"     # This is for api

                # print('\nSuccessfully fetched and processed Flight Aware data')
                break


    else:
        print('UNSUCCESSFUL!! flight_aware_data_pull.pull FLIGHT_AWARE_DATA, no `flights` available')
        return fa_object.attrs

    try:
        return {
                'ident_icao': ident_icao,
                'origin':origin, 
                'destination':destination, 
                'registration':registration, 
                'date_out': date_out,
                'scheduled_out':scheduled_out, 
                'estimated_out':estimated_out, 
                'scheduled_in':scheduled_in, 
                'estimated_in':estimated_in, 
                "terminal_origin": terminal_origin,
                "terminal_destination": terminal_destination,
                "gate_origin": gate_origin,
                "gate_destination": gate_destination,
                "terminal_origin": terminal_origin,
                'filed_altitude':filed_altitude, 
                'filed_ete':filed_ete,
                'route': route,
                'sv': sv,
                        }
    except Exception as e:
        print('UNSUCCESSFUL!! flight_aware_data_pull.pull FLIGHT_AWARE_DATA, no `flights` available')
        print(e)
        return fa_object.attrs
                        
