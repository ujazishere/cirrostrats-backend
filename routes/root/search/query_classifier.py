# Claude parse query
from collections import defaultdict
import math
import re
import pickle
from typing import Dict, List, Union, Optional, Tuple
from config.database import collection_airports, collection_flights, db_UJ
from routes.root.search.search_ranker import RealTimeSearchRanker       #TODO

""" These Collections gets loaded up as soon as the server starts."""
cts = db_UJ['test_st']   # create/get a collection
# cta = db['test_airports']   # create/get a collection
# cta = collection_airports
# ctf = collection_flights


class QueryClassifier:
    """
    A class for classifying search queries into categories like Airports, Flights, etc.
    """
    
    def __init__(self, icao_file_path: Optional[str] = None):
        """
        Initialize the classifier with ICAO airline codes.
        
        Args:
            icao_file_path: Path to the pickle file containing ICAO codes and their counts
        """
        self.classified_suggestions = {}
        self.icao_codes_separated = "UA|AA|DL|G7|GJS|UAX"  # Default common codes

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
            if flight_number[0] == '4' and len(flight_number) == 4:
                airline_code = 'GJS'
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
            # TODO: Right now my basic concern is to make it work locally for UA and GJS only. Let digits go this direction forn now.
                # once the complexity increases more digits can be accounted for.
        # elif for gate
        #     self.classified_suggestions.setdefault('Gates', []).append(query)
        #     return {'category': 'Gates', 'value': query}
        
        # Other types of queries
        else:
            return {'category': 'Others', 'value': query}
    

    def classify_batch(self, queries: List[Tuple]) -> Dict:
        """
        Classify a batch of queries.
        
        Args:
            queries: List of query strings or tuples where first element is the query
            
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
        
