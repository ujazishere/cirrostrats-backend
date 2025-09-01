
from core.search.query_classifier import QueryClassifier


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


    def raw_submit_handler(self,collection_weather, search):
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


    def query_type_frontend_conversion(self,doc):
        """
        Typically 3 types of queries - airport, flight or gate
        searchcc
        format inconsistencies from backend/mongoDB collection data to frontend are handled here.
        for example: search_index_collection `airport_st` is convertd to airport, `fid_st` to flight, etc.
        """
        # TODO VHP: Account for parsing Tailnumber - send it to collection_flights database with flightID or registration...
            # If found return that, if not found request on flightAware - e.g N917PG

        #  TODO VHP: It is adament you establish some cross-platform consistency across all platforms with regards to formatting data and using it
        # For e.g someplace type is `Flight` while others is `flight` and other even `flightNumbers` or `flightID` for `flightId`

        terminanl_gate_st = doc.get('Terminal/Gate')
        airport_st = doc.get('airport_st')
        fid_st = doc.get('fid_st')
        parsed_query_cat_field = doc.get('category')
        pq_val = doc.get('value')

        # logic to separaate out flightID from airport and terminal/gates.
        if terminanl_gate_st:
            query_field,query_val,query_type = 'Terminal/Gate', "EWR - " + terminanl_gate_st + " Departures", 'Terminal/Gate'
        elif airport_st:
            query_field,query_val,query_type = 'airport', airport_st, 'airport'
        elif fid_st:
            query_field,query_val,query_type = 'flightID', fid_st, 'flight'
        # QueryClassifier's parse_query format handeling.
        elif parsed_query_cat_field:
            if parsed_query_cat_field == 'Airports':
                query_field, query_val, query_type = 'airport', pq_val, 'airport'
            elif parsed_query_cat_field == 'Flights':
                if isinstance(pq_val,dict):
                    fid_st = pq_val.get('airline_code') + pq_val.get('flight_number')
                    query_field, query_val, query_type = 'flightID', fid_st, 'flight'
                else:
                    self.temporary_n_number_parse_query(query=pq_val)
                    query_field, query_val, query_type = 'nnumber', pq_val, 'flight'
            
            elif parsed_query_cat_field == 'Digits':
                # Digits are usually flight numbers,
                query_field, query_val, query_type = 'flightID', pq_val, 'flight'

            elif parsed_query_cat_field == 'Others':
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


    def search_suggestion_frontned_format(self, c_docs):
        """ Suggestions formatter for frontend compatibility. Takes in sic docs as is,
            It first goes to the fuzzfind then to frontend which is processed again.
            There's quite a bit of unnecessary formatting and processing during this three way process
            TODO: reduce this clutter to improve efficiency.
        """

        # create unified search index
        search_index = []

        for doc in c_docs:

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


            # *** r_id meaning reference id - only available in search index collection.
            if doc.get('r_id'):
                passed_data.update({'r_id': str(doc['r_id'])})

            # terminal/gate doesn't use r_id, it uses regex for finding associated data.
            gate = doc.get('Terminal/Gate')
            if doc.get('Terminal/Gate'):
                passed_data.update({'gate': gate})
            
            search_index.append(passed_data)

        # sort by popularity (count), it obv comes in sorted. this is just an extra precautionary step.
        search_index.sort(key=lambda x: x['ph'], reverse=True)

        return search_index
