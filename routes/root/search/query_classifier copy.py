# Claude parse query
import re
import pickle
from typing import Dict, List, Union, Optional, Tuple
from config.database import collection_airports, collection_flights, db_UJ

""" These Collections gets loaded up as soon as the server starts."""
# ctf = db_UJ['test_es']   # create/get a collection
# cta = db_UJ['test_airports']   # create/get a collection
cta = collection_airports
ctf = collection_flights


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
        self.icao_codes_separated = "UA|AA|DL|G7|UAX"  # Default common codes



        limit = 100
        self.count_crit = {'count':{"$exists":True}}
        lcf = list(ctf.find(self.count_crit,{'flightID':1, 'count':1}).limit(limit))
        print('loaded', len(lcf))
        # lca = list(cta.find({'count':{"$exists":True}},{'code':1, 'name':1, 'count':1}))
        lca = list(cta.find({},{'code':1, 'name':1, 'count':1}).limit(limit))



        # Load ICAO codes if provided
        if icao_file_path:
            self.load_icao_codes(icao_file_path)
            
        # Compile regex patterns for better performance
        self.airport_pattern = re.compile(r"^[KkCc][A-Za-z]{3}$")
        self.flight_pattern = re.compile(rf"^({self.icao_codes_separated})\s?(\d{{1,5}}[A-Z]?$)")
    
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
            self.classified_suggestions.setdefault('Airports', []).append(query)
            return {'category': 'Airports', 'value': query}
        
        # Check if it's a flight number
        elif flight_match:
            airline_code = flight_match.group(1)
            flight_number = flight_match.group(2)
            flight_info = {'airline_code': airline_code, 'flight_number': flight_number}
            self.classified_suggestions.setdefault('Flights', []).append(flight_info)
            return {'category': 'Flights', 'value': flight_info}
        elif query.isdigit():
            self.classified_suggestions.setdefault('Digits', []).append(query)
            # TODO: Right now my basic concern is to make it work locally for UA and GJS only. Let digits go this direction forn now.
                # once the complexity increases more digits can be accounted for.
            return {'category': 'Digits', 'value': query}
        
        # # Check if it's a gate number (4-digit number starting with 4)
        # if query.isdigit() and query[0] == '4' and len(query) == 4:
        #     self.classified_suggestions.setdefault('Gates', []).append(query)
        #     return {'category': 'Gates', 'value': query}
        
        # Other types of queries
        self.classified_suggestions.setdefault('Others', []).append(query)
        return {'category': 'Others', 'value': query}
    
    def classify_batch(self, queries: List[Union[str, Tuple]]) -> Dict:
        """
        Classify a batch of queries.
        
        Args:
            queries: List of query strings or tuples where first element is the query
            
        Returns:
            Dictionary with classified suggestions
        """
        # Reset classifications for batch processing
        self.classified_suggestions = {}
        
        tots = {}
        for item in queries:
            query = item[0].upper() if isinstance(item, tuple) else item.upper()
            self.parse_query(query)
            for i in ['Airports','Flights', 'Digits', 'Others']:
                q = self.classified_suggestions.get(i)
                if q:
                    tots[q] = tots.get(q,0)+1
            self.classified_suggestions = {}
            
        return tots
    
    def get_classifications(self) -> Dict:
        """Get the current classifications."""
        return self.classified_suggestions
    
    def reset_classifications(self) -> None:
        """Reset all classifications."""
        self.classified_suggestions = {}


# Example usage:
if __name__ == "__main__":
    # Example 1: Single query classification
    classifier = QueryClassifier(icao_file_path="unique_icao.pkl")
    result = classifier.parse_query("DAL1231")
    print(f"Single query classification: {result}")
    
    # Example 2: Load ICAO codes and batch process
    classifier = QueryClassifier("unique_icao.pkl")
    
    # For batch processing from pickle file
    with open('publicuj_searches_unique_sorts.pkl', 'rb') as f:
        suggestions = pickle.load(f)
    
    results = classifier.classify_batch(suggestions)
    print(f"Classification categories: {list(results.keys())}")
    print(f"Total classified items: {sum(len(items) for items in results.values())}")

