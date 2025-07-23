
from routes.root.search.query_classifier import QueryClassifier


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


    def submit_handler(self,collection_weather, search):
        """ the raw submit is supposed to return frontend formatted reference_id, display and type for
            /details.jsx to fetch appropriately based on the type formatting, whereas dropdown suggestions
            contain similar format with display field for display and search within fuzzfind"""
        parsed_query = self.parse_query(query=search)
        val_field, val, val_type = self.format_conversion_for_frontend(doc=parsed_query)

        formatted_data = { 
            f"{val_field}":val,         # attempt to make a key field/property for an object in frontend.
            'display': val,             # This is manipulated later hence the duplicate.
            'type': val_type,
            # 'fuzz_find_search_text': val.lower()
            }
        print('SUBMIT: Raw search submit:', 'search: ', search,'pq: ', parsed_query,'formatted-data', formatted_data)
        return formatted_data


    def format_conversion_for_frontend(self,doc):
        """
        format inconsistencies from backend/mongoDB collection data to frontend are handled here.
        for example: csti `airport_st` is convertd to airport, `fid_st` to flight, etc.
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
            val_field,val,val_type = 'Terminal/Gate', "EWR - " + terminanl_gate_st + " Departures", 'Terminal/Gate'
        elif airport_st:
            val_field,val,val_type = 'airport', airport_st, 'airport'
        elif fid_st:
            val_field,val,val_type = 'flightID', fid_st, 'flight'
        # QueryClassifier's parse_query format handeling.
        elif parsed_query_cat_field:
            if parsed_query_cat_field == 'Airports':
                val_field, val, val_type = 'airport', pq_val, 'airport'
            elif parsed_query_cat_field == 'Flights':
                if isinstance(pq_val,dict):
                    fid_st = pq_val.get('airline_code') + pq_val.get('flight_number')
                    val_field, val, val_type = 'flightID', fid_st, 'flight'
                else:
                    self.temporary_n_number_parse_query(query=pq_val)
                    val_field, val, val_type = 'nnumber', pq_val, 'flight'
            
            elif parsed_query_cat_field == 'Digits':
                # Digits are usually flight numbers,
                val_field, val, val_type = 'flightID', pq_val, 'flight'

            elif parsed_query_cat_field == 'Others':
                # ** YOU GOTTA FIX PARSE ISSUE AT CORE OR SUFFER -- NOTE FOR FUTURE YOU Discovered on June 4 2025!
                # account for N numbers here! this is dangerous but can act as a bandaid for now. 
                # TODO VHP: Account for parsing Tailnumber - send it to collection_flights database with flightID or registration...
                    # If found return that, if not found request on flightAware - e.g N917PG
                if pq_val.isalpha():
                    val_field, val, val_type = 'airport', pq_val, 'airport'
                else:
                    print('pq_val', pq_val, 'is not alpha, assuming flightID')
                    val_field, val, val_type = 'others', pq_val, 'others'

        return val_field, val, val_type


    def search_suggestion_frontned_format(self, c_docs, limit=1000,):         # cta- collection test airports; ctf- collection test flights
        """ Suggestions formatter for delivery to the frontend. Takes in csti docs as is,
            It first goes to the fuzzfind then to frontend which is processed again.
            There's quite a bit of unnecessary formatting and processing during this three way process
            TODO: reduce this clutter to improve efficiency.
        """

        # create unified search index
        search_index = []

        for doc in c_docs:

            # Converting the search index collection format to a suitable format that can be processed in the frontend.
            val_field,val,val_type = self.format_conversion_for_frontend(doc=doc)

            # passed_data is the format that is sent to the frontend after being passed to the fuzzfind for search_text matching.
            passed_data = { 
                'stId': str(doc['_id']),
                f"{val_field}":val,         # attempt to make a key field/property for an object in frontend.

                'display': val,             # This is manipulated later hence the duplicate. TODO: investigate.
                'type': val_type,

                'ph': doc.get('ph', 0),     # ***********Only available in  csti
                'fuzz_find_search_text': val.lower()        # matched within fuzz_find func
                }

            search_index.append(passed_data)

            # *** r_id meaning reference id - only available in search index collection.
            if doc.get('r_id'):
                passed_data.update({'id': str(doc['r_id'])})

            # terminal/gate doesn't use r_id, it uses regex for finding associated data.
            gate = doc.get('Terminal/Gate')
            if doc.get('Terminal/Gate'):
                passed_data.update({'gate': gate})

        # sort by popularity (count), it obv comes in sorted. this is just an extra precautionary step.
        search_index.sort(key=lambda x: x['ph'], reverse=True)

        return search_index
