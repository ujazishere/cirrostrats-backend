import requests
from core.weather_fetch import Singular_weather_fetch
from models.model import AirportCache
from core.api.source_links_and_api import Source_links_and_api
from core.search.query_classifier import QueryClassifier

from config.database import airport_bulk_collection_uj, collection_flights, new_airport_cache_collection

class SearchInterface(QueryClassifier):
    def __init__(self):
        """ An interface for collection search suggestions and query submission and processing between frontend and backend."""
        super().__init__()
        pass


    def standardize_types(self, val_type):
        """Ensure consistent type naming across platform"""
        TYPE_STANDARDS = {
            'Flight': 'flight',
            'FLIGHT': 'flight', 
            'flightNumbers': 'flight',
            'flightId': 'flight',
            'Airport': 'airport',
            'AIRPORT': 'airport',
            'Terminal/Gate': 'terminal',
            'gate': 'terminal',
            'Gate': 'terminal'
        }

        return TYPE_STANDARDS.get(val_type, val_type.lower())


    def raw_submit_handler(self, search):
        """ the raw submit is supposed to return frontend formatted reference_id, display and type for
            /details.jsx to fetch appropriately based on the type formatting, whereas dropdown suggestions
            contain similar format with display field for display and search within fuzzfind"""
        parsed_query = self.parse_query(query=search)
        query_field, query_val, query_type = self.query_type_frontend_conversion(doc=parsed_query)

        formatted_data = { 
            f"{query_field}":query_val,         # attempt to make a key field/property for an object in frontend.
            'label': query_val,
            'display': query_val,             # This is manipulated later hence the duplicate.
            'type': query_type,
            # 'fuzz_find_search_text': val.lower()
            }
        print('SUBMIT: Raw search submit:', 'search: ', search,'pq: ', parsed_query,'formatted-data', formatted_data)
        return formatted_data


    def qc_frontend_conversion(self, parsed_query_cat_field, pq_val):

        query_field = query_val = query_type = None
        if parsed_query_cat_field == 'airport':
            query_field, query_val, query_type = 'airport', pq_val, 'airport'
        elif parsed_query_cat_field == 'flight':
            if isinstance(pq_val,dict):
                fid_st = pq_val.get('airline_code') + pq_val.get('flight_number')
                query_field, query_val, query_type = 'flightID', fid_st, 'flight'
            else:
                self.temporary_n_number_parse_query(query=pq_val)
                query_field, query_val, query_type = 'nnumber', pq_val, 'flight'
        
        elif parsed_query_cat_field == 'digits':
            # Digits are usually flight numbers,
            query_field, query_val, query_type = 'flightID', pq_val, 'flight'

        elif parsed_query_cat_field == 'others':
            # ** YOU GOTTA FIX PARSE ISSUE AT CORE OR SUFFER -- NOTE FOR FUTURE YOU Discovered on June 4 2025!
            # account for N numbers here! this is dangerous but can act as a bandaid for now. 
            # TODO VHP: Account for parsing Tailnumber - send it to collection_flights database with flightID or registration...
                # If found return that, if not found request on flightAware - e.g N917PG
            if pq_val.isalpha():
                query_field, query_val, query_type = 'airport', pq_val, 'airport'
            else:
                print('pq_val', pq_val, 'is not alpha, assuming flightID')
                query_field, query_val, query_type = 'others', pq_val, 'others'

        return query_field, query_val, query_type


    def query_type_frontend_conversion(self,doc):

        # TODO serach suggestions:
            # Parse query in exhaustion uses this function on top section.
            # raw submit also uses this function

        """ suggestions delivery """


        """
        Legacy:
        format inconsistencies from backend/mongoDB collection data to frontend were handled here.
        for example: search_index_collection `airportDisplayTerm` is convertd to airport, `fid_st` to flight, etc.
        Typically 3 types of queries - airport, flight or gate
        
        """

        # TODO VHP: Account for parsing Tailnumber - send it to collection_flights database with flightID or registration...
            # If found return that, if not found request on flightAware - e.g N917PG
        query_type = doc.get('type')
        parsed_query_type = doc.get('type')
        parsed_query_value = doc.get('value')

        if parsed_query_type:
            query_field, query_val, query_type = self.qc_frontend_conversion(parsed_query_type,parsed_query_value)

        # TODO search suggestions: These need to deliver frontend formatted data for suggestions collection insertion.
        
        # gate = doc.get('metadata.gate') if query_type == 'gate' else None
        # ICAOAirportCode = doc.get('metadata.ICAO') if query_type == 'airport' else None
        # flightID = doc.get('metadata.flightID') if query_type == 'flight' else None
        gate = ICAOAirportCode = flightID = None        # temporary diversion to avoid error.

        # logic to separaate out flightID from airport and terminal/gates.
        if gate:
            
            query_field,query_val,query_type = 'gate', "EWR - " + gate + " Departures", 'gate'
        elif ICAOAirportCode:
            query_field,query_val,query_type = 'airport', ICAOAirportCode, 'airport'
        elif flightID:
            query_field,query_val,query_type = 'flight', flightID, 'flight'
        # QueryClassifier's parse_query format handeling.
        return query_field, query_val, query_type


    def search_suggestion_frontned_format(self, c_docs):            # **** DEPRECATED ****
        """ *****   DEPRECATED ****** """
        # This function is nolonger used it used to process docs from collections and parsed query and convert data structure for frontend use.

        """ 
        Legacy:
        Suggestions formatter for frontend compatibility. Takes in sic docs as is,
            It first goes to the fuzzfind then to frontend which is processed again.
            There's quite a bit of unnecessary formatting and processing during this three way process

            Arguments:
                c_docs: search index collection documents from mongoDB
        """

        # create unified search index
        search_index = []

        for doc in c_docs:
            pass
            """
            # Converting the search index collection format to a suitable format that can be processed in the frontend.
            query_field,query_val,query_type = self.query_type_frontend_conversion(doc=doc)

            # passed_data is the format that is sent to the frontend after being passed to the fuzzfind for search_text matching.
            passed_data = { 
                'stId': str(doc['_id']),
                f"{query_field}":query_val,         # attempt to make a key field/property for an object in frontend.

                'display': query_val,             # This is manipulated later hence the duplicate. TODO: investigate.
                'type': query_type,

                'ph': doc.get('ph', 0),     # ***********Only available in  search index collection
                'fuzz_find_search_text': query_val.lower()        # matched within fuzz_find func
                }


            # *** airportCacheReferenceId meaning reference id - only available in search index collection.
            if doc.get('airportCacheReferenceId'):
                passed_data.update({'airportCacheReferenceId': str(doc['airportCacheReferenceId'])})

            # terminal/gate doesn't use airportCacheReferenceId, it uses regex for finding associated data.
            gate = doc.get('Terminal/Gate')
            if doc.get('Terminal/Gate'):
                passed_data.update({'gate': gate})
            
            search_index.append(passed_data)
            """
        # sort by popularity (count), it obv comes in sorted. this is just an extra precautionary step.
        search_index.sort(key=lambda x: x['ph'], reverse=True)

        return search_index


class ExhaustionCriteria():
    def __init__(self) -> None:
        pass

    # Aviation weather response parsing for airport_cache_collection
    
    def parse_aviation_weather_airport_info_response(self, api_data):
        """Parse the text-based API response from aviationweather.gov"""
        parsed = {}
        
        lines = api_data.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse key-value pairs (looking for specific keys)
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key == 'IATA':
                    parsed['IATA'] = value if value != '-' else None
                elif key == 'ICAO':
                    parsed['ICAO'] = value
                elif key == 'Name':
                    parsed['airportName'] = value
                elif key == 'State':
                    parsed['regionName'] = value
                elif key == 'Country':
                    parsed['countryCode'] = value
                # elif key == 'Elevation':
                #     parsed['elevation'] = value
                # elif key == 'Latitude':
                #     parsed['latitude'] = value
                # elif key == 'Longitude':
                #     parsed['longitude'] = value
        
        parsed['weather']= {}
        return parsed
    
    
    async def faa_airport_info_fetch(self, ICAO_airport_code):
        # TODO: This probably doesn't belong here  maybe abstract this and faa fetch to some other file?

        # bulk_doc = airport_bulk_collection_uj.find_one({'icao':ICAO_airport_code})
        # if not bulk_doc:
        faa_weather_link = Source_links_and_api().airport_info_faa(ICAO_airport_code)
        response = requests.get(faa_weather_link)
        
        data = response.content.decode('utf-8')
        if not data:
            return
        if isinstance(data,dict) and data.get('status') == 'error':
            print(data['status'])
            return
        if 'error' in data:
            print('error in faa_airport_info_fetch data', data)
            return
        update_doc = self.parse_aviation_weather_airport_info_response(api_data=data)
    
            # print(json.loads(response.content))
        # else:
        #     update_doc = {
        #         'IATA': bulk_doc['iata'],
        #         'ICAO': bulk_doc['icao'],
        #         'airportName': bulk_doc['airport'],
        #         'regionName': bulk_doc['region_name'],
        #         'countryCode': bulk_doc['country_code'],
        #         'weather': {}
        #     }
        AirportCache(**update_doc)
    
        swf  = Singular_weather_fetch()
        weather_dict = await swf.async_weather_dict(update_doc['ICAO'])
        update_doc['weather'] = weather_dict
        return update_doc
    # await faa_weather_fetch('KSMQ')
    # await faa_weather_fetch('C-29')
    

    def airport_cache_insertion(self, ICAO_airport_code):
        # TODO search suggestions: This should only work for search submits and not for suggestions.

        bulk_doc = airport_bulk_collection_uj.find_one({'icao': ICAO_airport_code})
        # What if the doc in this bulk collection is outdated? maybe we can catch each code on airport lookup and validate it?

        if not bulk_doc:
            print('No bulk doc found in airport bulk collection for ICAO', ICAO_airport_code)
            # TODO search suggestions: Should this fetch using faa weather api and then insert that into bulk doc??
            return None
        
        IATA_airport_code = bulk_doc.get('iata')
        airportName = bulk_doc.get('airport')
        regionName = bulk_doc.get('region_name')
        countryCode = bulk_doc.get('country_code')
        
        new_airport_cache_doc = new_airport_cache_collection.find_one({'ICAO': ICAO_airport_code})
        if new_airport_cache_doc:
            return new_airport_cache_doc
        else:
            new_airport_cache_doc = {
                'IATA': IATA_airport_code,
                'ICAO': ICAO_airport_code,       
                'airportName': airportName,
                'regionName': regionName,
                'countryCode': countryCode,
                'weather': {}
            }
            # new_airport_cache_collection.insert_one(new_airport_cache_doc)
            return new_airport_cache_collection.find_one({'ICAO': ICAO_airport_code})
        
        
    def ICAO_airport_suggestions_format(self, ICAO_airport_code):
        """ Takes in US/CA ICAO airports parsed through parse_query and formats them for suggestions collection insertion."""
        
        # Idea is if you found it insert it in airports cache,
        doc = airport_bulk_collection_uj.find_one({'icao': ICAO_airport_code})
        if not doc:
            print('No airport doc found in airport bulk collection for ICAO', ICAO_airport_code)
            return []

        IATA_airport_code = doc.get('iata')
        airportName = doc.get('airport')

        if doc:
            return {
                # 'referenceId': str(ObjectId()),
                'type': 'airport',
                'display': f"{IATA_airport_code} - {airportName}",        # Merge code and name for display
                'displaySimilarity': [f"{IATA_airport_code} - {airportName}"],
                'popularityScore': 1.0,
                'metadata': {
                    'ICAO': ICAO_airport_code,
                }
            }

    def backend_flight_query(self, flightID: str):
        find_crit = {
            "versions.version_created_at": {"$exists": True},
            "flightID": {"$regex": "your_regex_pattern"}
        }
        return_crit = {'flightID':1,'_id':0}
        
        flightIDs = list(collection_flights.find(find_crit, return_crit))

        
        # TODO: This is a temporary fix, need to implement a better way. this wont work not ICAO prepended lookups maybe?
        if flightID[:2] == 'DL':       # temporary fix for delta flights
            flightID = 'DAL'+flightID[2:]
        elif flightID[:2] == 'AA' and flightID[:3]!='AAL':       # temporary fix for american flights
            flightID = 'AAL'+flightID[2:]
        # N-numbers returns errors on submits.
        return_crit = {'flightID': 1}


        flight_docs = collection_flights.find({'flightID': {'$regex':flightID}}, return_crit).limit(10)
        search_index = []
        for i in flight_docs:
            search_index.append({
                'type': 'flight',
                'display': i['flightID'],        # Merge code and name for display
                'referenceId': str(i['_id']),
                'metadata': {
                    'flightID': i['flightID'],
                }
            })
        return search_index

        