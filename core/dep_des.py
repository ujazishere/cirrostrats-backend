from .root_class import Root_class
from .flight_aware_data_pull import flight_aware_data_pull
from core.api.flightStats import FlightStatsScraper

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
                            'flightStatsActualDepartureTime': departure.get('ActualTime'),
                            'flightStatsScheduledArrivalTime': arrival.get('ScheduledTime'),
                            'flightStatsActualArrivalTime': arrival.get('ScheduledTime'),
                            'flightStatsDelayStatus': fs_data.get('fsDelayStatus'),
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
    