from .root_class import Root_class
from core.api.flightStats import FlightStatsScraper

'''
This Script pulls the departure and destination when provided with the flight number.
'''

class Pull_flight_info(Root_class):

    def __init__(self) -> None:
        # Super method inherits the init method of the superclass. In this case`Root_class`.
        super().__init__()


    def flightstats_dep_arr_timezone_pull(self,airline_code="UA", flt_num_query=None, departure_date:str=None, return_bs4=False):
        # TODO Refactor: This function can be refactored to FlightStatsScraper class in core/api
        
        fss = FlightStatsScraper()
        fs_data = fss.scrape(airline_code=airline_code, flt_num=flt_num_query, return_bs4=return_bs4)
        
        # use this for custom datetime instead 
        # fs_data = fss.scrape(airline_code="UA", flt_num_query="45", departure_date="20250717", return_bs4=False)

        if not fs_data:     # early retur if data isnt found
            return
        
        departure = fs_data.get('fsDeparture')
        arrival = fs_data.get('fsArrival')

        # TODO Test: 
                # Flow - return city from fs and fv , match with fuzz find on similarity scale if theyre both same fire up LLM 
        # TODO Test: If this is unavailable, which has been the case lately- May 2024, use the other source for determining scheduled and actual departure and arriavl times
        # TODO VHP: Return Estimated/ Actual to show delay times for the flights.
        bulk_flight_deet = {'flightStatsFlightID': airline_code+flt_num_query,
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
                                            }
        return bulk_flight_deet


    def aviation_stack_pull(self,):
        return None
    