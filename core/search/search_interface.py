import re
import requests
from core.weather_fetch import Singular_weather_fetch
from models.model import AirportCache
from core.api.source_links_and_api import Source_links_and_api
from core.search.query_classifier import QueryClassifier

from config.database import airport_bulk_collection_uj, collection_flights, gate_rows_collection, new_airport_cache_collection
from routes.weather_routes import get_mdbAirportWeatherByAirportCode

class SearchInterface(QueryClassifier):

    def __init__(self):
        """ An interface for collection search suggestions and query submission and processing between frontend and backend."""
        super().__init__()          # get QueryClassifier as base for this class


    async def raw_submit_handler(self, search):
        """ the raw submit is supposed to return frontend formatted reference_id, display and type for
            /details.jsx to fetch appropriately based on the type formatting, whereas dropdown suggestions
            contain similar format with display field for display and search within fuzzfind"""

        # TODO search suggestions: raw submit handler still needs to be accounted for - for now just replicate/duplicate whats being done for suggestions handler with single return.
                # Worry later about the ambigous multiple results. check extended_flight_suggestions todo for abstraction and reusability
        parsed_query = self.parse_query(query=search)
        
        exhaust = ExhaustionCriteria()

        # fot exact matches return exact ones, for partial multiple matches return partial ones.
        # for airport return dmb if found and update with live?
        # or just return it as suggestion and navigate it to details?
        query_type = parsed_query.get('type')
        if query_type in ['flight', 'digits', 'nNumber']:
            flight_category = parsed_query.get('value')
        
        # if type is airport:
            # airport_weather = await get_mdbAirportWeatherByAirportCode(airportCode=ICAO_airport_code)
            # if airport_weather:
            #     return airport_weather
        
        
        return self.suggestions_exhaustion_handler(parsed_query=parsed_query)
        

    def suggestions_exhaustion_handler(self, parsed_query):
        
        exhaust = ExhaustionCriteria()

        query_type = parsed_query.get('type')
        if query_type in ['flight', 'digits', 'nNumber']:
            flight_category = parsed_query.get('value')
            return exhaust.extended_flight_suggestions_formatting(flight_category)
        elif query_type == 'airport':       # only for US and Canadian ICAO airport codes.
            ICAO_airport_code = parsed_query.get('value')
            # TODO search suggestions extension: This returns airport suggestions but with IATA code for display and wont show up in suggestions since query is ICAO.
                    # e.g CYOW will return ottawa suggestion format from backend but frontend display is OTW - Ottawa hence dropdown wont
                    # show up since it wont match Cyow query with yow display..
            
            return exhaust.extended_ICAO_airport_suggestions_formatting(ICAO_airport_code)
        elif parsed_query.get('type') == 'other':       # for other queries we search airport collection.
            # nNumbers, airports and gates go here many a time
            other_query = parsed_query.get('value')
            print('other q', other_query)

            gate_docs = exhaust.extended_gate_suggestions(gate_query=other_query)
            if gate_docs:
                return gate_docs

            airport_suggestions = exhaust.extended_airport_suggestions(airport_query=other_query)
            if airport_suggestions:
                print('airport sug', airport_suggestions)
                return airport_suggestions

            n_pattern = re.compile("^N[a-zA-Z0-9]{1,5}$")
            if n_pattern.match(other_query):
                print('N number found')
                flightID = parsed_query.get('value')
                return exhaust.extended_flight_suggestions_formatting(flightID)


    def qc_frontend_conversion(self, parsed_query_cat_field, pq_val):   # **** DEPRECATED ****
        """ *****   DEPRECATED ****** """

        query_field = query_val = query_type = None
        if parsed_query_cat_field == 'airport':
            query_field, query_val, query_type = 'airport', pq_val, 'airport'
        elif parsed_query_cat_field == 'flight':
            if isinstance(pq_val,dict):
                fid_st = pq_val.get('airline_code') + pq_val.get('flight_number')
                query_field, query_val, query_type = 'flightID', fid_st, 'flight'
            else:
                self.temporary_n_number_parse_query(query=pq_val)       # ****** DEPRECATED *****
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


    def query_type_frontend_conversion(self,doc):                       # **** DEPRECATED ****
        """ *****   DEPRECATED ****** """

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


    def search_suggestion_frontned_format(self, c_docs):                # **** DEPRECATED ****
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

    
    def parse_aviation_weather_airport_info_response(self, api_data):
        """
        Parses the text-based API response from aviationweather.gov's airport info endpoint
        for use in the airport_cache_collection.

        See also: `faa_airport_info_fetch` for fetching FAA airport info directly.
        """

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
                # TODO weather: Add elevation, runways, latitude and longitude to the airport_cache_collection?
                # elif key == 'Elevation':
                #     parsed['elevation'] = value
                # elif key == 'Latitude':
                #     parsed['latitude'] = value
                # elif key == 'Longitude':
                #     parsed['longitude'] = value
        
        parsed['weather']= {}
        return parsed
    
    
    async def faa_airport_info_fetch_w_weather(self, ICAO_airport_code):
        """ Suggestions cache format for airport search suggestions fetched directly from FAA for both airport info itself and weather """

        # TODO search suggestions: refac these top three functions away into weather files since its not supposed to be used in suggestions exhaustions or suggestions at all..
                # since it only supposed to be used for suggestion submits and raw submits not for dropdown suggestions display format/
        # TODO search: This probably doesn't belong here  maybe abstract this and faa fetch to some other file or maybe within searchInterface?
            # Idea for it to ack as a fallback for airport cache collection and weather fetch when theres none available in bulk airport collection.
            # TODO extended: account for variations in lookup - 'airport info {ICAO}` `airport info {IATA}` `airport info {airportName}` `airport info {city, state, country}` etc.
            # or `DATIS/weather/taf/metar ?(for/info) {ICAO}` `weather/taf/metar ?(for/info) {IATA}` `weather/taf/metar ?(for/info) {airportName}` `weather/taf/metar ?(for/info) {city, state, country}` etc.

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
    
        AirportCache(**update_doc)
    
        return update_doc
    

    async def airport_cache_insertion(self, ICAO_airport_code):
        """ Inserts airport cache format doc into the new_airport_cache_collection
            currently only queries bulk collection for ICAO code and inserts into new_airport_cache_collection.
            # TODO search suggestions: This should only work for search submits and not for suggestions.
                # Should this fetch using faa weather api and then insert that into bulk doc??
        """

        weather_doc = None
        # TODO search suggestions: New airport Cache collection is not accounted for in broad_test weather test. Need to change from legacy collection to new collection there.
        new_airport_cache_doc = new_airport_cache_collection.find_one({'ICAO': ICAO_airport_code})
        if new_airport_cache_doc:
            print('New airport cache doc found in new airport cache collection for ICAO', ICAO_airport_code)
            weather_doc = new_airport_cache_doc

        else:
            bulk_doc = airport_bulk_collection_uj.find_one({'icao': ICAO_airport_code})
            # What if the doc in this bulk collection is outdated? maybe we can catch each code on airport lookup and validate it?

            if not bulk_doc:
                print('No bulk doc found for ICAO. Fetching from FAA weather API...', ICAO_airport_code)
                # TODO weather: This is a fallback for when the bulk doc is not found.
                weather_doc = await self.faa_airport_info_fetch_w_weather(ICAO_airport_code)
                swf  = Singular_weather_fetch()
                weather_dict = await swf.async_weather_dict(weather_doc['ICAO'])
                weather_doc['weather'] = weather_dict
        
            IATA_airport_code = bulk_doc.get('iata')
            airportName = bulk_doc.get('airport')
            regionName = bulk_doc.get('region_name')
            countryCode = bulk_doc.get('country_code')
        
            new_airport_cache_doc = {
                'IATA': IATA_airport_code,
                'ICAO': ICAO_airport_code,       
                'airportName': airportName,
                'regionName': regionName,
                'countryCode': countryCode,
                'weather': {}
            }
            weather_doc = new_airport_cache_doc
            # # TODO weather: Insert new airport cache doc into new airport cache collection if not already there.
            # new_airport_cache_collection.insert_one(new_airport_cache_doc)
            # weather_doc = new_airport_cache_collection.find_one({'ICAO': ICAO_airport_code})
            # # TODO weather: Add elevation, runways, latitude and longitude to the airport_cache_collection?
            # # TODO weather: consider removing airports when going over certain threshold to keep it lean?

        
        return weather_doc


    def extended_ICAO_airport_suggestions_formatting(self, ICAO_airport_code):
        """ Takes in (possibly random) US/CA ICAO airports parsed through parse_query and formats them for suggestions collection insertion."""
        
        # Idea is if you found it insert it in airports cache,
        doc = airport_bulk_collection_uj.find_one({'icao': ICAO_airport_code})
        if not doc:
            print('No airport doc found in airport bulk collection for ICAO', ICAO_airport_code)
            return []

        IATA_airport_code = doc.get('iata')
        airportName = doc.get('airport')

        if doc:
            formatted_return = [{
                # 'referenceId': str(ObjectId()),
                'type': 'airport',
                'display': f"{IATA_airport_code} - {airportName}",        # Merge code and name for display
                'displaySimilarity': [f"{IATA_airport_code} - {airportName}"],
                'popularityScore': 1.0,
                'metadata': {
                    'ICAOAirportCode': ICAO_airport_code,
                }
            }] 
            print('formatted',formatted_return)
            return formatted_return

    def extended_flight_suggestions_formatting(self, parsed_flight_category: str|dict):
        """ Extensive and impressive flightID suggestions formatting for frontend delivery check comments for more details.
            User selects a dropdown - its ICAO matches straight with JMS
            display format: ICAO/digits (Associated major IATA/digits) - IATA airline code only known US carriers - GJS, UCA, EDV, ENY, JIA, PDT and so on.
                e.g
                    GJS4433 (UA4433) - G7
                    UCA4938 (UA4938) - C5
                    EDV4628 (DL4628) - 9E
        """
        # TODO search suggestion: 
            # flightstats IATA for all airlines e.g SKW9887 should go to UA, DL and AA altogether to compare dep and dest with times.
            # code duplication alert - possibly could abstract some of it away and reuse it for raw_submits_handler.

        """ Parsing the flight category into a regex for flightID lookup """
        if isinstance(parsed_flight_category, str):       # accounts for type as nNumber,digits and internationals codes as fallback - value is string
            regex_flight_lookup = parsed_flight_category
            if regex_flight_lookup.isdigit():           # accounts for digits as flightID for matching exact digits within flightID.
                regex_flight_lookup = r'^[A-Z]{2,3}' + regex_flight_lookup + r'(?![0-9])[A-Z]?$'
        elif isinstance(parsed_flight_category, dict):        # type as flight - value is dicts for US based IATA and ICAO and major associated ICAO handling
            derived_code_type = parsed_flight_category.get('code_type') 
            IATA_airline_code = parsed_flight_category.get('IATA_airline_code') 
            flight_number = parsed_flight_category.get('flight_number') 
            if derived_code_type == 'IATA' and IATA_airline_code in ['UA','DL','AA']:       # major associated
                # This section assigns regionals to associated major 
                major = Source_links_and_api().regional_ICAO_to_associated_major_IATA()
                major_associated_ICAO_codes = major.get(IATA_airline_code)
                regex_flight_lookup = f"({'|'.join(major_associated_ICAO_codes)}){flight_number}"
            elif derived_code_type == 'IATA' or derived_code_type == 'ICAO':        # fallback to all others
                ICAO_flightID = parsed_flight_category.get('ICAO_airline_code') + parsed_flight_category.get('flight_number')
                regex_flight_lookup = ICAO_flightID
            

        """ Querying the collection_flights collection for flightID matches using the previously parsed regex_flight_lookup """
        find_crit = {
            "versions.version_created_at": {"$exists": True},
            "flightID": {"$regex": regex_flight_lookup}
        }
        return_crit = {'flightID':1,'_id':0}
            # TODO search suggestions: See here we can add fields with ICAO/IATA airline codes as customary so for commuteair, gojet can do UA and endevor can do DL and so on?
                # Skywest crit: Ua6000

        flight_docs = collection_flights.find(find_crit, return_crit).limit(5)

        suggestions_cache = []
        for each_flight_doc in flight_docs:
            fetched_ICAO_flightID = each_flight_doc['flightID']
            IATA_flightID = associated_major_IATA_airline_code = None
            display = fetched_ICAO_flightID         # preset it as is first so we can account for all extra ICAO possible returns - nNumbers and internationals
            # displaySimilarity = []        # TODO search suggestion: account for this for digit matching? low priority for now account major ones
            # NOTE: Doing this again as this seems more robust than reusing the parse_flight_query since it will only validate ICAO/IATA instead of digits and nNnumbers
            parsed_flight_category = QueryClassifier().parse_flight_query(flight_query=fetched_ICAO_flightID)
            if parsed_flight_category:
                derived_code_type = parsed_flight_category.get('code_type') 
                IATA_airline_code = parsed_flight_category.get('IATA_airline_code') 
                ICAO_airline_code = parsed_flight_category.get('ICAO_airline_code') 
                flight_number = parsed_flight_category.get('flight_number') 
                major = Source_links_and_api().regional_ICAO_to_associated_major_IATA()
                if derived_code_type == 'ICAO' and ICAO_airline_code in major.keys():       # major associated ICAO to IATA conversion for display assignment
                    major_associated_IATA_code = major.get(ICAO_airline_code)
                    IATA_flightID = major_associated_IATA_code + flight_number
                    display = f"{fetched_ICAO_flightID} ({IATA_flightID}) - {IATA_airline_code}"
                else:
                    IATA_flightID = IATA_airline_code + flight_number
                    display = f"{fetched_ICAO_flightID} ({IATA_flightID}) - {IATA_airline_code}"

            suggestions_cache.append({
                'type': 'flight',
                'display': display,        # Merge code and name for display
                # 'referenceId': str(i['_id']),
                'metadata': {
                    'ICAOFlightID': fetched_ICAO_flightID,
                    'IATAFlightID': IATA_flightID,
                    'majorFlightID': associated_major_IATA_airline_code,
                }
            })

        return suggestions_cache

        
    def extended_airport_suggestions(self, airport_query):
        """ Airport suggestions formatter for frontend delivery -
        Queries airport bulk collection for US and CA airports, matches them using airport name, ICAO and IATA codes """

        case_insensitive_regex_find = {'$regex':airport_query, '$options': 'i'}
        
        # Looking for the query in airportName, icao, iata from the aiport bulk collection.
        airport_docs = list(airport_bulk_collection_uj.find({
            "$or": [
                {"airport": case_insensitive_regex_find},
                {"icao": case_insensitive_regex_find},
                {"iata": case_insensitive_regex_find}
            ],
            "country_code": {"$in": ["US", "CA"]}
        }).limit(5))

        suggestions_cache = []
        if not airport_docs:
            print('No airport docs found in airport bulk collection for query',airport_query)
            return []
            """
            TODO search suggestion: This is an unneessary call to the faa api just for suggestion.
                find a way to integrate this into raw submits and available matches. its gotta be integrated with key stroke submits eventually
                to determine patterns and extend query classifier based on raw submits and key strokes.
                Check query classifier's TODO search suggestions for more details.
            # if len(airport_query) == 4:
                # pass
                airport_docs_faa_weather = await self.faa_airport_info_fetch_w_weather(ICAO_airport_code=airport_query)
                if not airport_docs_faa_weather:
                    print('No airport docs found in FAA weather API for query',airport_query)
                    return []
                IATA_airport_code = airport_docs_faa_weather.get('IATA') 
                ICAO_airport_code = airport_docs_faa_weather.get('ICAO')
                airportName = airport_docs_faa_weather.get('airportName')
                # # To be used in case weather needs to be fetched for the airport.
                # swf  = Singular_weather_fetch()
                # weather_dict = await swf.async_weather_dict(ICAO_airport_code)
                # airport_docs['weather'] = weather_dict
                # a workaround to add the airport docs to the airport_docs list since this is the bulk collection format
                airport_docs.append({
                    'iata': IATA_airport_code,
                    'icao': ICAO_airport_code,
                    'airport': airportName,
                    # 'weather': {}
                })
            """

        for i in airport_docs:
            print('i airport docs',i)
            IATA_airport_code = i.get('iata')
            ICAO_airport_code = i.get('icao')
            airportName = i.get('airport')

            airportCode = IATA_airport_code if IATA_airport_code else ICAO_airport_code
            # All these cannot be nan/null/None
            if not airportCode or not airportName:
                print('Skipping airport doc because something is None')
                continue
                # Note: Some airport values have null/nan/None values and those are discarded. But what if we want to show them? for example iata: OTT has not ICAO code what if we want to show? but why? we cant even get weather for it if theres no ICAO,
            suggestions_cache.append({
                # 'referenceId': str(ObjectId()),
                'type': 'airport',
                'display': f"{airportCode} - {airportName}",        # Merge code and name for display
                'displaySimilarity': [f"{airportCode} - {airportName}"],
                'popularityScore': 1.0,
                'metadata': {
                    'ICAOAirportCode': ICAO_airport_code,
                }
            })
        return suggestions_cache
    
    def extended_gate_suggestions(self, gate_query):
        """ Gate suggestions formatter for frontend delivery -
        Queries gate_rows_collection for gate matches using gate itself for e.g C101 """

        find_crit = {'Gate': {'$regex': gate_query}}
        gates = gate_rows_collection.distinct('Gate', find_crit)
        print('within gates', gates)
        if gates:
            suggestions_cache = []
            for gate in gates:
                display = f"EWR - {gate} Departures"
                suggestions_cache.append(
                    {
                        'type': 'gate',
                        'display': display,
                        'displaySimilarity': [],
                        'popularityScore': 1.0,
                        'metadata': {
                            'gate': gate,
                        }

                    }
                )
            return suggestions_cache


