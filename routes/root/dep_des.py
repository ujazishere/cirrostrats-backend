import requests
from bs4 import BeautifulSoup as bs4
from .root_class import Root_class
from .flight_aware_data_pull import flight_aware_data_pull
import xml.etree.ElementTree as ET
import re
import pickle
from routes.root.api.flightStats import FlightStatsScraper
from routes.root.root_class import AirportValidation

'''
This Script pulls the departure and destination when provided with the flight number.
'''

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