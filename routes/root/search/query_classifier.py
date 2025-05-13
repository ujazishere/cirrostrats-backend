# Claude parse query
from collections import defaultdict
import math
import re
import pickle
from typing import Dict, List, Union, Optional, Tuple

from pymongo import UpdateOne
from config.database import collection_airports, collection_flights, db_UJ
from routes.root.search.search_ranker import RealTimeSearchRanker       #TODO HP Feature.

""" These Collections gets loaded up as soon as the server starts."""
cts = db_UJ['test_st']   # create/get a collection
# cta = db['test_airports']   # create/get a collection
# cta = collection_airports
# ctf = collection_flights


class QueryClassifier:
    """
    A class for classifying search queries into categories like Airports, Flights, etc.
    Will also categorize multiplpe queries with counts of each served as popularity count and spit out normalized output.
    """
    
    def __init__(self, icao_file_path: Optional[str] = None):
        """
        Initialize the classifier with ICAO airline codes and regex pattern
        Args:
            icao_file_path: Path to the pickle file containing ICAO codes and their counts
        """
        self.classified_suggestions = {}
        self.icao_codes_separated = "UA|AA|DL|G7|GJS|UCA|UAX"  # Default common codes

        # Load ICAO codes if provided
        if icao_file_path:
            self.load_icao_codes(icao_file_path)

        # Compile regex patterns for better performance
        self.airport_pattern = re.compile(r"^[KkCc][A-Za-z]{3}$")
        self.flight_pattern = re.compile(rf"^({self.icao_codes_separated})\s?(\d{{1,5}}[A-Z]?$)")


    def initialize_collections(self,test_suggestions=True):
        limit = 100
        if test_suggestions:
            with open('sti_test.pkl', 'rb') as f: 
                print("loading csti test from pickle")
                self.c_sti_docs = pickle.load(f)
        else:
            # search index finds - sorted ph returns from the sti.
            self.count_crit = {'ph':{"$exists":True}}       # return ones with popularity hits
            self.c_sti_docs = list(cts.find(self.count_crit).sort('ph',-1))     # Reverse sort
        # print('initialized.', self.c_sti_docs)

        # self.lcf = list(ctf.find(self.count_crit,{'flightID':1, 'count':1}).limit(limit))
        # print('loaded', len(lcf))
        # self.lca = list(cta.find({'count':{"$exists":True}},{'code':1, 'name':1, 'count':1}))
        # self.lca = list(cta.find({},{'code':1, 'name':1, 'count':1}).limit(limit))

    
    def load_icao_codes(self, file_path: str) -> None:
        """
        Load ICAO codes from a pickle file.
        
        Args:
            file_path: Path to the pickle file
        """
        try:
            with open(file_path, 'rb') as f:
                icao_pops_all = pickle.load(f)
            
            icao_list = [icao for icao, count in icao_pops_all.items()]
            additional_codes = '|'.join(icao_list[1:29])
            
            # Update the pattern with more codes
            if additional_codes:
                self.icao_codes_separated = self.icao_codes_separated + "|"+ additional_codes
                # Recompile the flight pattern with updated codes
                self.flight_pattern = re.compile(rf"^({self.icao_codes_separated})\s?(\d{{1,5}}[A-Z]?$)")
            return self.icao_codes_separated
        except Exception as e:
            print(f"Error loading ICAO codes: {e}")
    

    def parse_query(self, query: str) -> Dict:
        """
        Parse and classify a single query.
        
        Args:
            query: Search query string
        
        Returns:
            Dictionary containing classified suggestions updated with this query
        """
        if not query:
            return self.classified_suggestions
            
        query = query.strip().upper()
        flight_match = self.flight_pattern.match(query)
        # Check if it's an airport code
        if self.airport_pattern.match(query):
            # self.classified_suggestions.setdefault('Airports', []).append(query)
            return {'category': 'Airports', 'value': query}
        
        # Check if it's a flight number
        elif flight_match:
            airline_code = flight_match.group(1)
            flight_number = flight_match.group(2)
            flight_info = {'airline_code': airline_code, 'flight_number': flight_number}
            # self.classified_suggestions.setdefault('Flights', []).append(flight_info)
            return {'category': 'Flights', 'value': flight_info}
        elif query.isdigit():
            if query[0] == '4' and len(query) == 4:
                airline_code = 'GJS'
                flight_number = query
                flight_info = {'airline_code': airline_code, 'flight_number': flight_number}
                # self.classified_suggestions.setdefault('Flights', []).append(flight_info)
                return {'category': 'Flights', 'value': flight_info}
            else:
                # self.classified_suggestions.setdefault('Digits', []).append(query)
                return {'category': 'Digits', 'value': query}
            # TODO VHP Feature: Right now my basic concern is to make it work locally for UA and GJS only. Let digits go this direction forn now.
                # once the complexity increases more digits can be accounted for.
        # elif for gate
        #     self.classified_suggestions.setdefault('Gates', []).append(query)
        #     return {'category': 'Gates', 'value': query}
        
        # Other types of queries
        else:
            return {'category': 'Others', 'value': query}
    

    def prepare_flight_id_for_webscraping(self, flightID: str) -> Optional[Tuple[str, str]]:
        """Prepare a flight ID for webscraping by replacing 'UAL', 'GJS', and 'UCA' with 'UA'."""
        parsed_query = self.parse_query(flightID)
        if parsed_query.get("category") == "Flights":
            airline_code = parsed_query["value"]["airline_code"]
            flightID_digits = parsed_query["value"]["flight_number"]
            if airline_code in ["UAL", "GJS", "UCA"]:
                airline_code = "UA"
            return airline_code, flightID_digits
        print("Error within qc_webscrape. parse_query failed to return categorized data")
        return None


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
        


class QC_base_popularity_hits(QueryClassifier):
    def pickle_loads(self):
        import pickle
        
        with open('publicuj_searches_unique_sorts.pkl', 'rb') as f:
            suggestions = pickle.load(f)
        with open('ForMDB.pkl', 'rb') as f:
            z = pickle.load(f)
            base_rating = 2
            base_rating = 2
            flightID_batch = [("GJS"+str(flightID),base_rating) for flightID in z['scheduled_flights']]        # Adding count as 1.
            airports_batch = [(a,b) for a,b in z['popularity_raw'].items()]         # aiport ID with popularity counts.
        with open('unique_icao.pkl', 'rb') as f:
            icao = pickle.load(f)
        icaos = [(icao,count) for icao, count in icao.items()][1:29]

        return(suggestions,flightID_batch,airports_batch,icaos)
    

    def qc_ranker(self):
        from routes.root.search.query_classifier import QueryClassifier

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
        
        # len(fids_to_upload)+cts.count_documents({})
        # cts.count_documents({})
        # fids_to_upload
        
        # updates the new united docs - 3000+ of them to the cts collection. !!! Caution.. It will also update the united flights that are already in there - ones like UAL414

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
        # result = cts.bulk_write(update_operations)
        
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
        print(len(fids), len(cfid))
        
        """Airports ratings"""
        airports_p_hits = nn['Airports']
        
        processed_airport_codes = [i[1:] for i in list(airports_p_hits.keys()) if i[0] == 'K']      # removing leading `K`
        # Fetch all matching airports in a single query by supplying a list of items to be matched
        cacodes = list(collection_airports.find({'code': {'$in': processed_airport_codes}}, {'count':0}))         # collection airport codes
        
        airports_to_upload = []
        for doc in cacodes:
            ph= airports_p_hits.get("K"+doc['code'])
            if doc.get('name'):
                airports_to_upload.append({'r_id':doc['_id'],'airport_st':f"{doc['code']} - {doc['name']}", 'ph':ph})
                
            # print(nn['Airports'].get("K"+a))
        
        # difference btwn requests and returns. difference are the unsuccessfull ones.
        print(len(airports_p_hits),len(cacodes))
        


        """ merge flight docs and aiport docs to upload then insert to a new csti collection """
        all_docs_to_upload = fids_to_upload + airports_to_upload
        all_docs_to_upload = sorted(all_docs_to_upload, key=lambda doc:doc.get('ph',0),reverse=True)
        
        return all_docs_to_upload
        
    def gate_popularity(self,collection_gates):
        nn= self.nn
        
        gates = [i[1:] for i in nn['Others'].keys() if i.startswith('C') and i[1:]!= '']        # include 'C' in match exclude it in returns and discardempty ones.
        # match from the list provided.
        list_of_items_to_be_matched = gates  # for exmple this  could a list of flight numbers you want to match within the collection.
        reg_pat = "|".join(list_of_items_to_be_matched)
        cgid = list(collection_gates.find({'Gate': {'$regex': reg_pat}},{'Gate':1,'_id':1} ))
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
        # cts.insert_many(all_docs_to_upload)
        
        # cts.find_one({})
        # cts.delete_many({})
        cts.count_documents({})
        # list(cts.find({},{}))
        
        
        

class Trie_structure_WIP:
    def somefunc(self):
        """ Intent here to find if there is a pattern that exists here to forma  trie like data structure for
            Faster indexing and directing query to appropriate areas"""
        
        flightIDs = [i for i in collection_flights.find({},{'flightID':1, '_id':0})]
        fid = [flightID['flightID'] for flightID in flightIDs]
        fid.sort()

        import pickle
        """ Get 30 most popular icaos """
        with open('unique_icao.pkl', 'rb') as f:
            icao = pickle.load(f)
        icaos = [icao for icao, count in icao.items()][1:29]
        
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