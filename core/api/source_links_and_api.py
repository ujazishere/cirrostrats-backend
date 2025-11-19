import os
import json
from decouple import config
from core.root_class import Root_class

class Source_links_and_api:
    def __init__(self,):
        pass
        # TODO LP: use this to get status about flights, gate, times and delay status.
        # "https://flyrichmond.com/"

    
    def popular_ICAO_airline_codes(self):
        """ Returns 50 most popular ICAO airline codes. """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print('script_dir', script_dir)
        default_icao_path = os.path.normpath(os.path.join(script_dir, '..', '..','data', 'unique_icao.json'))

        with open(default_icao_path, 'r') as f:
            icao_pops_all = json.load(f)
        icao_list = [icao for icao, count in icao_pops_all.items() if len(icao) == 3]
        ICAO_airline_codes = '|'.join(icao_list[1:50])

        return ICAO_airline_codes

    
    def datis_stations(self) -> str:
        """ Returns datis stations. Theres about 76 datis stations that publish D-ATIS data typically every hour """
        return 'https://datis.clowd.io/api/stations'


    def airport_info_faa(self, ICAO_airport_code) -> str:
        # TODO weather: This needs to be integrated with cache. mind uppercase for airportName.
        """ gives ICAO, IATA, airportName, lat,long, elevation, state, country, runways
        e.g - https://aviationweather.gov/api/data/airport?ids=KEWR
        """
        return f"https://aviationweather.gov/api/data/airport?ids={ICAO_airport_code}"


    def weather(self, weather_type,ICAO_airport_code) -> dict:
        """ given type of weather returns the link for fetching.
        Args:
            - weather_type : metar, taf, datis
        """
        urls = {
            "metar": f"https://aviationweather.gov/api/data/metar?ids={ICAO_airport_code}",
            "taf": f"https://aviationweather.gov/api/data/taf?ids={ICAO_airport_code}",
            "datis": f"https://datis.clowd.io/api/{ICAO_airport_code}",
        }

        url = urls.get(weather_type)
        return url


    def nas_raw_xml_fetch(self):
        return "https://nasstatus.faa.gov/api/airport-status-information"


    def ua_dep_dest_flight_status(self, flight_number):
        # reeturns a dictionay paid of departure and destination
        return f"https://united-airlines.flight-status.info/ua-{flight_number}"               # This web probably contains incorrect information.


    def newark_airport(self):
        return "https://www.flightstats.com/airport/USKN/Newark"


    def flight_stats_url(self,flight_number):
        # TODO refactor: FlightStats URL for pulling flight status. Use this function
        # local time zones. just needs flight number and date as input
        
        date = Root_class().date_time(raw=True)
        
        base_url = "https://www.flightstats.com/v2/flight-tracker/"
        return f"{base_url}UA/{flight_number}?year={date[:4]}&month={date[4:6]}&date={date[-2:]}"


    def aviation_stack(self,flightID):
        # Aviation Stack api call. 3000 requests per month
        base_url = "http://api.aviationstack.com/v1/flights"
        access_key = config("AVIATION_STACK_API_KEY")
        url = f"{base_url}?access_key={access_key}&flight_icao={flightID}"


        """ 
        # TODO: Fix airline code issue. This is not used yet. Find use case.
        # Aviation Stack api call. 3000 requests per month
        aviation_stack_url = 'http://api.aviationstack.com/v1/flights'
        aviation_stack_params = {
                            'access_key': '65dfac89c99477374011de39d27e290a',
                            'flight_icao': f"{airline_code}{flt_num}"}
        # aviationstack just like flight_aware
        self.av_stack_url_w_auth = {aviation_stack_url:aviation_stack_params}
        # Old requests code: api_result = requests.get(aviation_stack_url, self.aviation_stack_params)
        """

        
        return {url: {}}    # Is  the value supposed to serve as auth header?


    def flight_aware_w_auth_url(self,ICAO_flight_number):
        """ Returns flight aware link with auth header
        e.g link: https://aeroapi.flightaware.com/aeroapi/flights/UAL4433 """

        fa_base_apiUrl = "https://aeroapi.flightaware.com/aeroapi/"
        # fa_apiKey = config('FLIGHT_AWARE_API_KEY_ISMAIL')         # Doesn't work - tried in Oct 2025
        fa_apiKey = config("ujazzzmay0525api")      # apple login 
        fa_auth_header = {'x-apikey':fa_apiKey}
        fa_url = fa_base_apiUrl + f"flights/{ICAO_flight_number}"
        fa_url_w_auth = {fa_url:fa_auth_header}
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
        return fa_url_w_auth


    def flight_view_gate_info(self,flight_number:str ,departure_airport_code:str):
        """ Deprecated """
        date = Root_class().date_time(raw=True)
        base_url = "https://www.flightview.com/flight-tracker/"
        return f"{base_url}UA/{flight_number}?date={date}&depapt={departure_airport_code[1:]}"

