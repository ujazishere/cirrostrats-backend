# Part 1: Normalize popularity counts
import math
from datetime import datetime, timedelta

from pymongo import UpdateOne

class RealTimeSearchRanker:
    # def __init__(self, decay_per_hour=0.1, k=0.5, theta=3, recency_bonus=2):          # OG
    def __init__(self, decay_per_hour=0.1, k=100, theta=2/3, recency_bonus=2):
        self.decay_per_second = 1 - (1 - decay_per_hour) ** (1/3600)  # Convert hourly decay to per-second
        self.k = k                  # caps highest rate. 100 caps it to 10
        self.theta = theta          # for increase in theta the curve steepens goof for giving popularity boost for lower conts
        self.recency_bonus = recency_bonus      # adds to the count
        self.searches = {}  # Format: {'query': {'hits': float, 'last_updated': datetime}}

    def compressed_sigmoid(self, x):
        # sigmoid = 1 / (1 + math.exp(-self.k * (x - self.theta)))              # OG
        sigmoid = math.sqrt(1 / ((1/self.k) + math.exp(-(x * self.theta))))
        return int(sigmoid*3)

    def log_search(self, query):
        now = datetime.now()
        is_new = query not in self.searches

        # Apply exponential decay based on seconds since last update
        if not is_new:
            elapsed_seconds = (now - self.searches[query]['last_updated']).total_seconds()
            decay_factor = math.exp(-self.decay_per_second * elapsed_seconds)
            self.searches[query]['hits'] *= decay_factor
            self.searches[query]['hits'] += 1
        else:       # if new query, add recency bonus and last updated.
            self.searches[query] = {'hits': 1 + self.recency_bonus, 'last_updated': now}

        self.searches[query]['last_updated'] = now
        return self.compressed_sigmoid(self.searches[query]['hits'])

    def get_suggestions(self, prefix="", limit=5):
        """Get suggestions with sub-second precision decay"""
        current_time = datetime.now()
        scored = []
        
        for query, data in self.searches.items():
            if prefix.lower() in query.lower():
                # Recalculate decay for exact current moment
                elapsed_seconds = (current_time - data['last_updated']).total_seconds()
                decayed_hits = data['hits'] * math.exp(-self.decay_per_second * elapsed_seconds)
                scored.append((query, self.compressed_sigmoid(decayed_hits)))
        
        return sorted(scored, key=lambda x: x[1], reverse=True)[:limit]
    



class QC_supplemental:
    def x():
        import pickle
        from routes.root.search.query_classifier import QueryClassifier
        
        with open('publicuj_searches_unique_sorts.pkl', 'rb') as f:
            suggestions = pickle.load(f)
        with open('ForMDB.pkl', 'rb') as f:
            z = pickle.load(f)
            airports_batch = [(a,b) for a,b in z['popularity_raw'].items()]         # aiport ID with popularity counts.
            base_rating = 2
            flightID_batch = [("GJS"+str(flightID),base_rating) for flightID in z['scheduled_flights']]        # Adding count as 1.
        with open('unique_icao.pkl', 'rb') as f:
            icao = pickle.load(f)
        icaos = [(icao,count) for icao, count in icao.items()][1:29]
        
        
        qc = QueryClassifier()
        
        qc.classify_batch(suggestions)
        qc.classify_batch(airports_batch)
        qc.classify_batch(flightID_batch)
        cc = qc.classified_suggestions
        bb = qc.data_cleaner()
        qc.classified_suggestions = bb
        nn = qc.normalize()
        
        # total phits items that needs to retrived from collections.
        len(nn['Airports'])+len(nn['Flights'])
        # icaos

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
            ph = qc.compress_sigmoid(2)
            fids_to_upload.append({'r_id':doc['_id'],'fid_st':doc['flightID'],'ph':ph})
        
        # len(fids_to_upload)+cts.count_documents({})
        # cts.count_documents({})
        # fids_to_upload
        
        # updates the new united docs - 3000+ of them to the cts collection. !!! Caution.. It will also update the united flights that are already in there - ones like UAL414
        update_operations = []
        # docs = list(cts.find({}, {'_id': 0}))  # Exclude `_id` to prevent conflicts
        for doc in fids_to_upload:
            flightID = doc['fid_st']
            update_operations.append(
                UpdateOne({'fid_st': flightID},
                          {'$set': doc},
                          upsert=True
                          )
            ),
        
        # ***CAUTION!!!!
        # result = cts.bulk_write(update_operations)
        



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
        # all_docs_to_upload
        # cts.insert_many(all_docs_to_upload)
        
        # cts.find_one({})
        # cts.delete_many({})
        cts.count_documents({})
        
        # list(cts.find({},{}))
        
        


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