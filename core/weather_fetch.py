import json
import pickle
from pymongo import UpdateOne
import requests

from config.database import collection_weather_cache,collection_airports_cache_legacy
from core.weather_parse import Weather_parse
from core.root_class import Root_class, Fetching_Mechanism, Source_links_and_api
from services.notification_service import send_telegram_notification_service

class Weather_processor:
    def __init__(self) -> None:
        pass

    def resp_splitter(self, airport_code, resp_dict):
        metar,taf,datis = ['']*3

        for url,resp in resp_dict.items():
            if f"metar?ids={airport_code}" in str(url):
                metar = resp
            elif f"taf?ids={airport_code}" in str(url):
                taf = resp
            elif f"clowd.io/api/{airport_code}" in str(url):
                datis = json.loads(resp)     # Apparently this is being returned within a list is being fed as is. Accounted for.
        return metar,taf,datis

    def raw_resp_weather_processing(self, resp_dict, ICAO_airport_code, html_injection=False):
        # TODO Datis: Why is this here?
        metar,taf,datis = self.resp_splitter(ICAO_airport_code, resp_dict)
        raw_weather_returns = {"datis":datis,"metar":metar,"taf":taf}
        # dep_weather = wp.html_injected_weather(weather_raw=dep_weather)
        
        wp = Weather_parse()            
        if html_injection:
            return wp.html_injected_weather(weather_raw=raw_weather_returns)     # Doing this to avoid nested weather dictionaries
        else:
            datis_raw = wp.datis_processing(datis_raw=raw_weather_returns.get('datis','N/A'))
            raw_weather_returns['datis'] = datis_raw
            return raw_weather_returns


class Bulk_weather_fetch:
    """
    This class is used to bulk fetch weather data - datis, metar and taf
    and save it to mongoDB. Its primary used in celery tasks.

    TODO LP Feature: This link contains abbreviations for weather that can be used to decode coded NOTAMS/Weather. https://asrs.arc.nasa.gov/docs/dbol/ASRS_Abbreviations.pdf
    """

    def __init__(self) -> None:
        self.rc = Root_class()
        self.sl = Source_links_and_api()
        self.fm = Fetching_Mechanism()
        self.weather_returns = {}
        self.weather_links_dict = self.bulk_weather_link_returns()
    
    def bulk_weather_link_returns(self) -> None:
        # Returns weather links for all airports with code.

        # TODO weather: Fix IATA/ICAO issue - WIP -- collection_airports_cache_legacy documents gotta be migrated to uj collection with appropriate IATA/ICAO
        all_mdb_airport_codes = [i['code'] for i in collection_airports_cache_legacy.find({},{'code':1})]

        sla = Source_links_and_api()
        response = requests.get(sla.datis_stations())

        all_datis_ICAO_airport_codes = response.json()
        if not all_datis_ICAO_airport_codes or  not isinstance(all_datis_ICAO_airport_codes,list):        # Check if response is valid list of airport codes
            send_telegram_notification_service(message=f'Error: Datis airport codes fetch failed. returns: {all_datis_ICAO_airport_codes}')
            print('Error: Datis airport codes fetch failed. Returns:', all_datis_ICAO_airport_codes)
            all_datis_ICAO_airport_codes = []
        # all_datis_airports_path = r'c:\users\ujasv\onedrive\desktop\codes\cirrostrats\all_datis_airports.pkl'

        import os
        
        """
        RESTRUCTURING UPDATE: Dynamic path resolution for maximum compatibility
        
        WHAT CHANGED:
        - Path remains in core/pkl/ directory (no directory change)
        - Uses dynamic path resolution instead of current working directory
        - Removed old hardcoded absolute path
        
        WHY NO DIRECTORY CHANGE:
        - taf_positive_airports.pkl contains weather-specific airport codes
        - This data is tightly coupled with weather processing functionality
        - Keeping it in core/pkl/ maintains logical separation:
          * General data files -> data/ directory
          * Core weather functionality data -> core/pkl/ directory
        
        PATH LOGIC:
        - Uses dynamic path resolution from this file's location
        - Works regardless of execution context or import method
        - Path: {script_location}/../pkl/taf_positive_airports.pkl
        """
        
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Dynamic path to TAF positive airports file
        taf_positive_ICAO_airportS_path = os.path.normpath(os.path.join(script_dir, 'pkl', 'taf_positive_airports.pkl'))
        
        with open(taf_positive_ICAO_airportS_path, 'rb') as f:
            taf_positive_airport_codes = pickle.load(f)

        #  All airport codes from mongo db and pickle
        return {
            "datis": self.bulk_list_of_weather_links('datis',all_datis_ICAO_airport_codes),
            "metar": self.bulk_list_of_weather_links('metar',all_mdb_airport_codes),
            "taf": self.bulk_list_of_weather_links('taf',taf_positive_airport_codes),
        }

    def bulk_list_of_weather_links(self,type_of_weather,list_of_airport_codes):
        # Returns datis links from claud.ai and aviation weather links for metar and taf from aviationwather.gov
        # TODO: collection_airports_cache_legacy code issue fix
        # TODO weather: Fix IATA/ICAO issue - WIP -- collection_airports_cache_legacy documents gotta be migrated to uj collection with appropriate IATA/ICAO
        prepend = ""
        if type_of_weather == 'metar':
            prepend = "K"
        
        return [self.sl.weather(weather_type=type_of_weather,ICAO_airport_code=prepend+each_airport_code) for each_airport_code in list_of_airport_codes]

    def bulk_datis_processing(self, resp_dict:dict):
        # TODO Test: a similar function exists in -- weather_parse().datis_processing().

        # print('Processing Datis')
        # datis raw returns is a list of dictionary when resp code is 200 otherwise its a json return as error.
        # This function processess the raw list and returns just the pure datis
        for url,datis in resp_dict.items():
            if not 'error' in datis:
                raw_datis_from_api = json.loads(datis)
                raw_datis = Weather_parse().datis_processing(raw_datis_from_api)
                resp_dict[url]=raw_datis
            else:
                # ending up in this block means the code is broken somewhere.
                # TODO Test: checkpoint here for notification- track how many times the code ends up here.
                send_telegram_notification_service(message=f'Error: Datis processing. URL is: {url} and datis is: {datis}')
                print('Error: Datis processing')

        return resp_dict

    async def bulk_weather_fetch(self,weather_type):
        
        """
        Fetches and processes weather data for a given type and returns a dictionary
        containing the processed weather data. If the type is 'datis', it will
        process the raw datis data and return the processed data.

        Parameters:
        weather_type (str): The type of weather to fetch. Should be either 'datis', 'metar' or 'taf'.

        Returns:
        dict: A dictionary containing the processed weather data.
        """
        resp_dict: dict = await self.fm.async_pull(self.weather_links_dict[weather_type])        

        if weather_type == 'datis':
            resp_dict = self.bulk_datis_processing(resp_dict=resp_dict)

        self.weather_returns[weather_type] = resp_dict
        return self.weather_returns

    async def bulk_fetch_and_store_by_type(self,weather_type):
        # print(f'{weather_type} async fetch in progress..')
        # TODO VHP Weather: Need to make sure if the return links are actually all in list form since the async_pull function processes it in list form. check await link in the above function.

        weather_dict = await self.bulk_weather_fetch(weather_type=weather_type)
        resp_dict = weather_dict[weather_type]

        self.mdb_updates(resp_dict=resp_dict,weather_type=weather_type)

    
    def mdb_unset(self,):
        # Attempt to update the document. In this case remove a field(key value pair).
        weather = {             # This weather dict wouldnt be necessary since the unset operator is removing the whole weather field itself.
            'metar':'',
            'taf':'',
            'datis':''
        }
        for each_d in collection_weather_cache.find():
            airport_code = each_d.get('ICAO')
        
            collection_weather_cache.update_one(
                {'_id':each_d['_id']},            # This is to direct the update method to the apporpriate id to change that particular document
                
                {'$unset': {'weather':weather}},
                # {'$unset': {'weather':''}},        # Use this instead since the whole weather will be removed anyway
                # When you use $unset with the key weather, it removes the entire weather field, not just the contents inside it.
                upsert=True
                )
    
    def mdb_updates(self,resp_dict: dict, weather_type):
        # This function creates a list of fields/items that need to be upated and passes it as bulk operation to the collection.
        # TODO Test: account for new airport codes, maybe upsert or maybe just none for now.
        # print('Updating mdb')
        update_operations = []

        for url, weather in resp_dict.items():
            # TODO VHP: Dangerous! fix magic number and 3 vs 4 char airport code issue.
            # TODO: collection_airports_cache_legacy code issue fix -- thinking about getting rid of the 3 char altogether.
                # This wont fix the issue of needing 3 char airport codes for suggestion mix.
                    # To fix this would need to supply 3 char if its not the same as the 4 char airport code[1:].
            airport_code_trailing = str(url)[-4:]
        
            update_operations.append(
                UpdateOne(
                    {'code': airport_code_trailing[-3:]},      # Finds the document with airport code 
                    {'$set': {
                        f'weather.{weather_type}': weather,
                        'ICAO': airport_code_trailing,      # Finds the document with airport code 
                        }},       # sets the weather subfield of that document
                    upsert=True)
                    # TODO Test: Check if this can work since it has be used to pick out the airports that are not fetched more frequently and notify devs.
                    #   {'$set': {f'weather.timeStamp': 'timestamp here'}},     
            )
        
        result = collection_weather_cache.bulk_write(update_operations)
        # print(result)


class Singular_weather_fetch:
    """ This class is used to fetch weather from different sources and return it as a dictionary.
        Given an airport ID, it will fetch datis, metar and taf.

        Returns:
            ** Mind DATIS as dict since it contains arr/dep/combined data and not a singular string.
            weather_dict: {'datis': {}, 'metar': '', 'taf': ''}
    """

    def __init__(self) -> None:
        pass

    def link_returns(self, weather_type, ICAO_airport_code):
        sla = Source_links_and_api()
        wl = sla.weather(weather_type,ICAO_airport_code)
        return wl

    async def async_weather_dict(self, ICAO_code_to_fetch):

        fm = Fetching_Mechanism()
        wl_dict = {weather_type:self.link_returns(weather_type,ICAO_code_to_fetch) for weather_type in ('metar', 'taf','datis')}
        resp_dict: dict = await fm.async_pull(list(wl_dict.values()))

        wp = Weather_processor()
        weather_dict = wp.raw_resp_weather_processing(resp_dict=resp_dict, ICAO_airport_code=ICAO_code_to_fetch, html_injection=False)

        return weather_dict

    def synchronous_weather_fetch(self, airport_code):    # Deprecated
        """ 
        deprecated! use async weather fetch instead. 
        Only use this when async is not working and you need a reliable synchronous code to return weather
        """
        
        wl_dict = {weather_type:self.link_returns(weather_type,airport_code) for weather_type in ('metar', 'taf','datis')}
        weather: dict = {}
        for weather_type, url in wl_dict.items():
            resp = requests.get(url)
            if weather_type == 'datis':
                datis = resp.json()
                wp = Weather_parse()
                datis = wp.datis_processing(datis_raw=datis)
                weather[weather_type] = datis
            else:
                resp = resp.content
                resp = resp.decode("utf-8")
                weather[weather_type] = resp
        return weather




"""
For use in jupyter

test datis returns:
from core.weather_fetch import Bulk_weather_fetch
bwf = Bulk_weather_fetch()

bwf.bulk_fetch_and_store_by_type(weather_type='datis')
datis = bwf.datis_returns

bwf.bulk_fetch_and_store_by_type(weather_type='metar')
bwf.bulk_fetch_and_store_by_type(weather_type='taf')

"""