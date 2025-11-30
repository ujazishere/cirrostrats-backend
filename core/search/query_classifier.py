# Claude parse query
from collections import defaultdict
import math
import re
from typing import Dict, List, Optional, Tuple

from config.database import collection_airports_cache_legacy, collection_flights, db_UJ
from core.api.source_links_and_api import Source_links_and_api
# from core.search.search_ranker import RealTimeSearchRanker       #TODO VHP Feature. Integrated with dynamic suggestions cache popularityScore

""" These Collections gets loaded up as soon as the server starts."""
# search_index_collection = db_UJ['search_index']           # OG one
suggestions_cache_collection = db_UJ['suggestions-cache-test-refills']         # New tester

class QueryClassifier:
    """
    A class for classifying search queries into categories like Airports, Flights, etc.
    Will also categorize multiplpe queries with counts of each served as popularity count and spit out normalized output.
    Usage in base popularity hits and route.

    """
    
    def __init__(self):
        """ Initialize the classifier for batch processing and normalization """
        self.classified_suggestions = {}


    def initialize_suggestions_cache_collection(self):
        """ Cache the collections for searchbar dropdown"""
        # search index finds - sorted ph returns from the search index collection.
        count_crit = {'popularityScore':{"$exists":True}}       # return ones with popularity hits
        return_crit = {'submitTimestamps':0}       # We dont need submits since its not used in search interface
        self.scc_docs = list(suggestions_cache_collection.find(count_crit, return_crit).sort('popularityScore',-1))     # Reverse sort
        return self.scc_docs
        # print('initialized.', self.sic_docs[:5])

    def parse_flight_query(self, flight_query) -> Dict:
        """ Used by parse_query to determine the type of flight query - ICAO/IATA with parsed flightID.""" 

        ICAO_IATA_airline_codes = Source_links_and_api().ICAO_to_IATA_airline_code_mapping()
        IATA_ICAO_airline_codes = Source_links_and_api().IATA_to_ICAO_airline_code_mapping()

        ICAO_airline_codes = '|'.join(code for code in ICAO_IATA_airline_codes.keys() if code)
        ICAO_flight_pattern = re.compile(rf"^({ICAO_airline_codes})\s?(\d{{1,5}}[A-Z]?$)")
        ICAO_match = ICAO_flight_pattern.match(flight_query)
        if ICAO_match:
            ICAO_code = ICAO_match.group(1)
            flight_number = ICAO_match.group(2)
            return {'code_type':'ICAO',
                    'ICAO_airline_code': ICAO_code,
                    'IATA_airline_code': ICAO_IATA_airline_codes.get(ICAO_code),
                    'flight_number': flight_number}

        IATA_airline_codes = '|'.join(code for code in ICAO_IATA_airline_codes.values() if code)
        IATA_flight_pattern = re.compile(rf"^({IATA_airline_codes})\s?(\d{{1,5}}[A-Z]?$)")
        IATA_match = IATA_flight_pattern.match(flight_query)
        if IATA_match:
            IATA_code = IATA_match.group(1)
            flight_number = IATA_match.group(2)
            return {'code_type':'IATA',
                    'IATA_airline_code': IATA_code,
                    'ICAO_airline_code': IATA_ICAO_airline_codes.get(IATA_code),
                    'flight_number': flight_number}

    def parse_query(self, query: str) -> Dict:
        """
        Parse and classify a single query. Parses as `flight`, `airport`, 'digits' and 'other'
        
        Args:
            query: Search query string
        
        Returns:
            Dictionary containing classified query type and value
        """
        # TODO search sugggestions:
            # Used at -  get_search_suggestions_service, prepare_flight_id_for_webscraping (flightStats), classify_batch (old bulk query classifier), 
                        #  raw_submit_handler (frontend raw submit), aws_jms_service
            
        query = query.strip().upper()

        flight_match = self.parse_flight_query(flight_query=query)

        US_CANADIAN_ICAO_airport_code_pattern = re.compile(r"^[KkCc][A-Za-z]{3}$")
        US_CA_ICAO_airport_code_match = US_CANADIAN_ICAO_airport_code_pattern.match(query)

        digits_matched = query.isdigit()

        # NOTE: Here would be more appropriate to add fault zone detection if match was both airport and flightID?

        if US_CA_ICAO_airport_code_match:
            return {'type': 'airport', 'value': query}
        
        # Check if it's a flight number
        if flight_match:
            print('flight matched', flight_match)
            return {'type': 'flight', 'value': flight_match}

        if digits_matched:
            print('digits matched', query)
            return {'type': 'digits', 'value': query}

        # TODO search suggestions: Two possiblities- suggestion exhaustion or raw submit - multiple results on raw submit? show those mumtiple items on result and let user choose.

        # Other types of queries - nNumbers, airports and gates go here many a time
        print('other query', query)
        return {'type': 'other', 'value': query}
    

    def classify_batch(self, queries: List[Tuple]) -> Dict:
        """
        Classify a batch of queries.
        
        Args:
            queries: List of query strings or tuples where first element is the query,
                        second the count, served as popularity hit
            
        Returns:
            Dictionary with classified suggestions
        """
        # Reset classifications for batch processing
        # self.classified_suggestions = {}
        
        # tots = {}
        for item in queries:
            query,count = item[0], item[1]
            rets = self.parse_query(query)
            q_cat = rets.get('category')
            q_val = rets.get('value')
            if q_cat == "Flights":
                dict_form = q_val
                q_val = (dict_form['airline_code']+dict_form['flight_number'])
            self.classified_suggestions.setdefault(q_cat, []).append((q_val,count))

    def data_cleaner(self):
        """ Classifier didnt account for duplicate flight numbers. this section takes care of it all.
            Converts tuple to dict as well. Safe and sound! :)) """
        o={}
        for i in ['Airports','Flights', 'Digits', 'Others']:
            data = self.classified_suggestions.get(i)
            if not data:
                continue
            ph = defaultdict(int)           # This is beautiful. Accounts for null keys assigns a false value of 0 avoiding key error.
            for k, p_hits in data:
                ph[k] += p_hits
            o[i] = dict(ph)
        return o

    def compress_sigmoid(self, x, k=1/30, theta=100,cap_height=10):
        """Theta moves func left and right, k is the squeeze stretch spread on x. So higher the x range smaller you want your k to account for higher ranges
        for k=1/30 the func caps hight for vals x>300
        """

        # Calculate original sigmoid value
        # sigmoid_val = math.sqrt(1 / ((1/k) + math.exp(-(x * theta))))       #OG
        sigmoid_val = 1 / (1 + math.exp(-k*(x - theta)))*cap_height
        
        # compressed_val = int(sigmoid_val*3)
        # return compressed_val
        return sigmoid_val

    def normalize(self):
        cc = self.classified_suggestions
        for cat,vals in cc.items():
            sa = {}
            for k,p_hit in vals.items():
                sa[k] = self.compress_sigmoid(p_hit)
            cc[cat] = sa
        return cc


    def temporary_n_number_parse_query(self,query):
        # ********** DEPRECATED ********

        # This is temporary. more robust one is needed.
        print('N number query', query)
        n_pattern = re.compile("^N[a-zA-Z0-9]{5}$")
        
        if n_pattern.match(query):
            return {'type': 'nNumber', 'value': query}

    def prepare_flight_id_for_webscraping(self, flightID: str) -> Optional[Tuple[str, str]]:
        # ********** DEPRECATED **********

        """ Currently Only used at flightStats source - takes flightID, cleans up using parse query
        and accounts for either GJS, UAL, UCA to make it UA, and DL,AA for delta or american since thats what flightstats takes for airline code.
        
        """
        """Prepare a flight ID for webscraping by replacing 'UAL', 'GJS', and 'UCA' with 'UA'."""
        parsed_query = self.parse_query(flightID)
        if parsed_query.get("type") == "flight":
            airline_code = parsed_query["value"]["airline_code"]
            flightID_digits = parsed_query["value"]["flight_number"]
            if airline_code in ["UAL", "GJS", "UCA"]:
                airline_code = "UA"
            elif airline_code == "DAL":
                airline_code = "DL"
            elif airline_code == "AAL":
                airline_code = "AA"
            print('airline_code in qc',airline_code)
            return airline_code, flightID_digits
        print("Error within qc_webscrape. parse_query failed to return categorized data")
        return None,None


        


class QC_base_popularity_hits(QueryClassifier):
    def pickle_loads(self):
        """
        Load pickle data files for query classification and popularity ranking.
        
        PROJECT RESTRUCTURING UPDATE (October 2025):
        All data file paths updated during comprehensive project cleanup.
        
        CHANGES MADE:
        1. publicuj_searches_unique_sorts.pkl: '' -> '../../data/publicuj_searches_unique_sorts.pkl'
        2. ForMDB.pkl -> forMDB.pkl: Fixed filename case AND updated path to '../../data/forMDB.pkl'
        3. unique_icao.pkl: '' -> '../../data/unique_icao.pkl'
        
        WHY THESE CHANGES:
        - Data files were scattered in root directory, making project structure messy
        - Moved all general data files to centralized data/ directory
        - Fixed case-sensitive filename issue (ForMDB.pkl vs forMDB.pkl)
        - Improved project organization following FastAPI best practices
        - Made paths relative and portable across different environments
        
        PATH LOGIC:
        - From: core/search/ directory (this file's location)
        - To: data/ directory (new centralized data location)
        - Relative path: ../../data/ (up 2 levels to root, then into data/)
        """
        import pickle
        
        # RESTRUCTURING UPDATE: Dynamic path resolution for maximum compatibility
        # Files moved from root to data/ directory during project cleanup
        import os
        
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Dynamic paths to data files
        suggestions_path = os.path.normpath(os.path.join(script_dir, '..', '..', 'data', 'publicuj_searches_unique_sorts.pkl'))
        formdb_path = os.path.normpath(os.path.join(script_dir, '..', '..', 'data', 'forMDB.pkl'))  # Fixed filename case
        icao_path = os.path.normpath(os.path.join(script_dir, '..', '..', 'data', 'unique_icao.pkl'))
        
        with open(suggestions_path, 'rb') as f:
            suggestions = pickle.load(f)
        with open(formdb_path, 'rb') as f:
            z = pickle.load(f)
            base_rating = 2
            base_rating = 2
            flightID_batch = [("GJS"+str(flightID),base_rating) for flightID in z['scheduled_flights']]        # Adding count as 1.
            airports_batch = [(a,b) for a,b in z['popularity_raw'].items()]         # aiport ID with popularity counts.
        with open(icao_path, 'rb') as f:
            icao = pickle.load(f)
        icaos = [(icao,count) for icao, count in icao.items()][1:29]

        return(suggestions,flightID_batch,airports_batch,icaos)
    

    def qc_ranker(self):
        from core.search.query_classifier import QueryClassifier

        suggestions, flightID_batch,airports_batch,icaos = self.pickle_loads()
        
        self.classify_batch(suggestions)
        self.classify_batch(airports_batch)
        self.classify_batch(flightID_batch)
        cc = self.classified_suggestions
        bb = self.data_cleaner()
        self.classified_suggestions = bb
        nn = self.normalize()
        
        # total phits items that needs to retrived from collections.
        len(nn['Airports'])+len(nn['Flights'])
        self.nn = nn
        return nn

    def nn_pass_code_share_partners(self,collection_flights):
        nn = self.nn
        """ Look up popular UA code share only and UAL icaos and  using regex in the collection_flights.
            assign default ph, pass through sigmoid and 
                """
        p_icao =  ['UAL','UCA']
        regex_pattern = "|".join(p_icao)
        cfid = list(collection_flights.find({'flightID': {'$regex': f"^({regex_pattern})"}},{'flightID':1,} ))
        
        fids_to_upload = []
        for doc in cfid:
            # phits
            # ph = cfid.get(doc['flightID'])
            ph = self.compress_sigmoid(2)
            fids_to_upload.append({'r_id':doc['_id'],'fid_st':doc['flightID'],'ph':ph})
        
        # len(fids_to_upload)+search_index_collection.count_documents({})
        # search_index_collection.count_documents({})
        # fids_to_upload
        
        # updates the new united docs - 3000+ of them to the search_index_collection collection. !!! Caution.. It will also update the united flights that are already in there - ones like UAL414

        # update_operations = []
        # for doc in fids_to_upload:
        #     flightID = doc['fid_st']
        #     update_operations.append(
        #         UpdateOne({'fid_st': flightID},
        #                   {'$set': doc},
        #                   upsert=True
        #                   )
        #     ),
        # return update_operations
        return fids_to_upload
        # ***CAUTION!!!!
        # result = search_index_collection.bulk_write(update_operations)
        
    def nn_popular_flights_and_airports_sorted(self,collection_flights):
        # returns popular flights and airport returns
        nn= self.nn

        """Flights ratings"""
        flights_phits = nn['Flights']
        fids= flights_phits.keys()
        
        # Mechanism to convert UA into UAL
        processed_flilghts_phits = {}
        for fid,ph in flights_phits.items():
            if fid.startswith("UAL"):
                print('outlaw',fid)
            elif fid.startswith("UA") and fid[2].isdigit():
                converted = 'UAL' + fid[2:]
                processed_flilghts_phits[converted]=ph
            else:
                processed_flilghts_phits[fid] = ph
        
        # Fetch all matching flightIDs in a single query by supplying a list of items to be matched
        cfid = list(collection_flights.find({'flightID': {'$in': list(processed_flilghts_phits.keys())}},{'flightID':1,} ))
        
        fids_to_upload = []
        for doc in cfid:
            # phits
            ph = processed_flilghts_phits.get(doc['flightID'])
            fids_to_upload.append({'r_id':doc['_id'],'fid_st':doc['flightID'],'ph':ph})
        
        # difference btwn requests and collection returns. difference are the unsuccessfull ones.
        print('difference btwn requests and colelction returns',len(fids), len(cfid))
        
        """Airports ratings"""
        airports_p_hits = nn['Airports']
        
        processed_airport_codes = [i[1:] for i in list(airports_p_hits.keys()) if i[0] == 'K']      # removing leading `K`
        # Fetch all matching airports in a single query by supplying a list of items to be matched
        cacodes = list(collection_airports_cache_legacy.find({'code': {'$in': processed_airport_codes}}, {'count':0}))         # collection airport codes
        
        airports_to_upload = []
        for doc in cacodes:
            ph= airports_p_hits.get("K"+doc['code'])
            if doc.get('name'):
                airports_to_upload.append({'r_id':doc['_id'],'airport_st':f"{doc['code']} - {doc['name']}", 'ph':ph})
                
            # print(nn['Airports'].get("K"+a))
        
        # difference btwn requests and returns. difference are the unsuccessfull ones.
        print('difference btwn requests and colelction returns',len(airports_p_hits),len(cacodes))
        
        """ merge flight docs and aiport docs to upload then insert to a new search_index collection """
        all_docs_to_upload = fids_to_upload + airports_to_upload
        all_docs_to_upload = sorted(all_docs_to_upload, key=lambda doc:doc.get('ph',0),reverse=True)
        
        return all_docs_to_upload
        
    def gate_popularity(self,collection_gates):
        nn= self.nn
        
        # include 'C' in match exclude it in returns and discardempty ones.
        gates = [i[1:] for i in nn['Others'].keys() if i.startswith('C') and i[1:]!= '']
        # match from the list provided.
        list_of_items_to_be_matched = gates  # for exmple this  could a list of flight numbers you want to match within the collection.
        reg_pat = "|".join(list_of_items_to_be_matched)
        return_crit = {'Gate':1,'_id':1}
        cgid = list(collection_gates.find({'Gate': {'$regex': reg_pat}}, return_crit ))
        # cgid
        # list(collection_gates.find({}, {'Gate':1}))
        gate_docs_to_upload = []
        count = 1
        for doc in cgid:
            count *=1.182
                
            ph = self.compress_sigmoid(count)
            if '101' in doc['Gate']:
                ph = 3.33333
            if ph<1:
                ph+=0.8
            gate_docs_to_upload.append({'r_id':doc['_id'],'Terminal/Gate':doc['Gate'], 'ph':ph})
        return gate_docs_to_upload
    
        # list(collection_gates.find({}, {'Gate':1}))
    def col_metrics(self):
        # search_index_collection.insert_many(all_docs_to_upload)
        
        # search_index_collection.find_one({})
        # search_index_collection.delete_many({})
        suggestions_cache_collection.count_documents({})
        # list(search_index_collection.find({},{}))
        
        
        

class Trie_structure_WIP:
    def somefunc(self):
        """ Intent here to find if there is a pattern that exists here to forma  trie like data structure for
            Faster indexing and directing query to appropriate areas"""
        
        flightIDs = [i for i in collection_flights.find({},{'flightID':1, '_id':0})]
        fid = [flightID['flightID'] for flightID in flightIDs]
        fid.sort()

        import pickle
        import os
        """ Get 30 most popular icaos """
        # RESTRUCTURING UPDATE: Dynamic path resolution for maximum compatibility
        # File moved from root to data/ directory during project cleanup
        
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Dynamic path to ICAO data file
        icao_path = os.path.normpath(os.path.join(script_dir, '..', '..', 'data', 'unique_icao.pkl'))
        
        with open(icao_path, 'rb') as f:
            icao = pickle.load(f)
        icaos = [icao for icao, count in icao.items()][1:29]
        
        categorized_icao = defaultdict(list)
        # flattened flightID. List full of flightIDs - possibly just digits
        alll = []
        for y in [i for _,i in categorized_icao.items()]:
            alll.extend(y)

        # Categorized_cao icao and their associated flightID's in list form e.g. "{AAL: [AAL132, AAL311], DAL:..}"
        categorized_icao = {}
        count = 0 
        for flightID in fid:
            count+=1
            if flightID.startswith(tuple(icaos)):
                categorized_icao[flightID[:3]] = categorized_icao.get(flightID[:3],list())+[flightID]       # categorizing according to 3 letter airline icao - popular airlines.
            # if flightID.startswith(tuple(icaos)) and flightID[3:].isdigit():          # returns just the digits instead of the leading icao+digits.icao) and flightID[3:].isdigit():
                # categorized_icao[flightID[:3]] = categorized_icao.get(flightID[:3],list())+[int(flightID[3:])]         
            else:
                categorized_icao['other'] = categorized_icao.get('other',list())+[flightID]
        
        # new just gets the digits and cleaner more managable data - 
        new = {}
        for icao,flightIDs in categorized_icao.items():
            if icao != 'other':        # Exclude others since it may contain over 70k+ flightID N numbers and other internations.
                tots = {}
                for eachFlightID in flightIDs:
                    digits = eachFlightID[3:]
                    if digits.isdigit():
                    # if digits.isdigit() and len(digits) == 4:
                        leads = digits[:2]
                        # leads = digits[0]
                        tots[leads] = tots.get(leads,0)+1
                tots = sorted(tots.items(), key=lambda x:x[1], reverse=True)
                new.update({icao:tots})        
                # print(a, flightIDs[:5])
        # Attempt to make a Trie type data sstructure. nn here would be AA [11,12] --? the first two digits are ones to feed into index matrix
            #  this can help with directing query to its appropriate area efficiently.
        nn = {icao:flight_digit_popularity for icao,flight_digit_popularity in new.items() if icao in icaos[:10]}
        for icao,flight_digit_popularity in nn.items():
            associated_digits = [int(i[0]) for i in flight_digit_popularity[:9]]      # upto x amount of top highest count digits
            associated_digits.sort()
            print(icao,associated_digits)
        
        
        
        # graph distribution of flight digits at a particular airline.
        from matplotlib import pyplot as plt
        airline = 'SKW'
        # plt.scatter(range(len(categorized_icao[airline])), sorted(categorized_icao[airline]),s=0.5)
        # plt.xlim(0,100)
        # plt.ylim(1000,1200)
        # plt.show()
        
        # compare flightID with digits or alphanumeric. 
        f=fid
        airline='SKW'
        aa = [aa for aa in f if aa.startswith(airline) and aa[3:].isdigit()]
        bb = [aa for aa in f if aa.startswith(airline) and not aa[3:].isdigit()]
        # len(aa), aa[:10], len(bb), bb[:10]