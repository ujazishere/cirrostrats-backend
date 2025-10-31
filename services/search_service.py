from config.database import collection_flights, collection_airports, db_UJ
from core.search.fuzz_find import fuzz_find
from core.search.search_interface import SearchInterface
from core.search.query_classifier import QueryClassifier
from models.model import SearchData
from bson import ObjectId
from schema.schemas import serialize_document_list
try:        # This is in order to keep going when collections are not available
    from config.database import collection_airports, collection_searchTrack
    from config.database import collection_flights, db_UJ
except Exception as e:
    print('Mongo collection(Luis) connection unsuccessful\n', e)


qc = QueryClassifier()
sic_docs = qc.initialize_search_index_collection()
print('Search Index Collection initialized with documents:', len(sic_docs))



async def get_search_suggestions_service(email: str, query: str, limit=500):  # Default page and page size
    """Cached fuzzy search to improve performance for repeated queries.
        The Idea is to have some sort of a cache that holds the initial popular fetches of upto 500 items(of the total 3500 sti) in suggestions and display only upto 5 in the drop-down.
        If the suggestions(display dropdown items) drop below 5 items then it should fetch the backend with the `latest query` to see if it returns any matches.
        Current state: Upto 2nd alphabet from `latest query` can match upto maybe <10 items of the 3500 for this cache and return those to the frontend exhausting the 3500 items.

        The interface is designed such that it has pre existing values from search index collection
        these dont currently update with new raw submits. also older submits may be intensive on processing during /st route on frontend lookup
        """

    # TODO VHP:
    """ 
        The suggestions dont show(need it) canadian airports.
        Primarily and necessicity:
            The frontend data structure that processes collections across flights, airports, gates, sic is flawed and inconsistent
            You need this to properly implement track search in its entirity-> match and track raw submits, integrate popularity hits,  
            caching and morphing search index collection.

        Additionally:
        data flow - use raw submit to *___ query the collection ___*  based on parseQuery:
        save in search-index collection and send it to the frontend for fetching just like search suggestions dropdowns.
            ***___ Minimize the ability for user to have raw searches- match all raw searches to appropriate item in collections ___***

            Current issue with search interface:
            Raw query submits cause and effect:

            Solution: - This possibly is already account for in the frontend - but need same for backend in case top5 suggestions are exhausted/unavailable.
                if raw submit matches flight number to its entirity then select the dropdown to send 
                if raw submit matches airport code to its entirity then select the dropdown
                    Feature: Currently Newark and chicago works but what if there are multiple airports in a city like chicago?
                if raw submit partially matches flight number then do not send the first drop select
    """
    sint = SearchInterface()
    # TODO VHP: This maybe it! just flip - do fuzzfind first then do the formatting?
    search_suggestions_frontend_format = sint.search_suggestion_frontned_format(c_docs=sic_docs)
    suggestions_match = fuzz_find(query=query, data=search_suggestions_frontend_format, qc=qc, limit=limit)
    if not suggestions_match and len(query)>=3:        # Exhaustion criteria
        print('suggestions running out', len(suggestions_match))
        # TODO: *****CAUTION**** Bad code exists here. this was a quick fix to account for exhaustion of search suggestions.
        # At exhaustion it will search the extended collections(flight,airport,etc) based on the 'type of query as follows.
        parsed_query = qc.parse_query(query=query)
        print('Exhausted sic docs, parsed query',parsed_query)
        # Attempt to parse the query and do dedicated formating to pass it again to the fuzz find since these collections will be different to search index collection.
        query_field,query_val,query_type = sint.query_type_frontend_conversion(doc=parsed_query)
        if query_type == 'flight':
            # TODO: This is a temporary fix, need to implement a better way. this wont work not ICAO prepended lookups maybe?
            if query_val[:2] == 'DL':       # temporary fix for delta flights
                query_val = 'DAL'+query_val[2:]
            elif query_val[:2] == 'AA' and query_val[:3]!='AAL':       # temporary fix for american flights
                query_val = 'AAL'+query_val[2:]
            # N-numbers returns errors on submits.
            return_crit = {'flightID': 1}
            flight_docs = collection_flights.find({'flightID': {'$regex':query_val}}, return_crit).limit(10)
            search_index = []
            for i in flight_docs:
                x = {
                    'id': str(i['_id']),
                    query_field: i['flightID'],  # Use the field name dynamically
                    'display': i['flightID'],        # Merge code and name for display
                    'type': 'flight',
                }
                search_index.append(x)
            return search_index

        elif query_type == 'airport':
            # TODO: This is a temporary fix, need to implement a better way to handle airport search since it wont look up the airport code.
            # Plus its ugly -- abstract this away since flight ID is using the same logic.
            # TODO: integrate this with searchindex such that it secures it inthe popular hits and moves the submits up the ladder.
            # TODO weather: Fix IATA/ICAO issue - WIP -- collection_airports documents gotta be migrated to uj collection with appropriate IATA/ICAO
            return_crit = {'name': 1, 'code':1}
            case_insensitive_regex_find = {'$regex':query_val, '$options': 'i'}
            
            airport_docs = list(collection_airports.find({'code': case_insensitive_regex_find}, return_crit).limit(10))
            search_index = []
            for i in airport_docs:
                x = {
                    'r_id': str(i['_id']),      # This r_id is used in frontend to access code and weather from mdb
                    query_field: i['code'],     # Use the field name dynamically
                    'display': f"{i['code']} - {i['name']}",        # Merge code and name for display
                    'type': 'airport',
                }
                search_index.append(x)
            if len(search_index) < 2:
                airport_docs = list(collection_airports.find({'name': case_insensitive_regex_find}, return_crit).limit(10))
                for i in airport_docs:
                    x = {
                        'r_id': str(i['_id']),      # This r_id is used in frontend to access code and weather from mdb
                        query_field: i['code'],     # Use the field name dynamically
                        'display': f"{i['code']} - {i['name']}",        # Merge code and name for display
                        'type': 'airport',
                    }
                    search_index.append(x)
            return search_index

    else:
        print('Suggestions found in sic docs', len(suggestions_match))
        return suggestions_match

async def track_search_service(data: SearchData):
    """ Save searches to the DB for tracking and analytics. saves to search index collection
    for preset serarches and rst collection for raw search term"""

    # TODO: Current bug: not tracking searches outside of the sic collection. need to account for all searches.
        # Need to save raw items properly to the sic with proper format and also account for duplicated if it already exists.
    # NOTE: It this good at all to save to search index collection since were using it for suggestions?
            # Maybe returning sic without submits is good for suggestions, and since its 
            # a light weight collection(upto 3000 items) it shouldnt make a huge difference?
            # TODO: But submits can blow up out of proportions ovevrtime?
    
    sic = db_UJ['search_index']   # create/get a collection
    ctrs = db_UJ['test_rst']   # create/get a collection

    # quick view of the search term. dropdown selection or raw search term
    # quick_view_st = data.submitTerm if data.submitTerm else sic.find_one({"_id": ObjectId(data.stId)}, {"_id": 0, "ph": 0, "r_id": 0})
    # 
    # TODO: query should be saved by user.
    update_query = {
        "$setOnInsert": {"email": data.email},  # Only set email on document creation
        "$set": {"lastUpdated": data.timestamp},  # Update timestamp
    }

    oid = {"_id": ObjectId(data.stId)}
    if data.stId:       # if submission with dropdown selection
        doc = sic.find_one(oid)
        if doc:
            if "submits" in doc:
                # If submits exists, just push the new timestamp -- append to the submits array
                sic.update_one(
                    {"_id": ObjectId(data.stId)},
                    {"$push": {"submits": data.timestamp}}
                )
            else:
                # If submits doesn't exist, set it as new array with the timestamp
                sic.update_one(
                    {"_id": ObjectId(data.stId)},
                    {"$set": {"submits": [data.timestamp]}}
                )
        doc = sic.find_one(oid)
    # TODO: This wont account for uniques. Every store is a new store.
    elif data.submitTerm:       # if submission with raw search term
        ctrs.update_one(
            {"rst": data.submitTerm},
            {"$push": {"submits": data.timestamp}},
            upsert=True
        )
    else:
        print("Impossible return!")

async def get_search_timeline_service():
    # Returns a timeline of all searches made by users in exploded fashion.

    sic = db_UJ['search_index']   # create/get a collection
    crts = db_UJ['test_rst']   # create/get a collection

    sic_docs =  list(sic.aggregate([
            { "$match": { "submits": { "$exists": True} } },
            { "$unwind": "$submits" },
            { "$addFields": { "timestamp": "$submits" } },
            { "$unset": ["_id", "r_id", "ph", "submits"] }
        ]))
    crts_returns =  list(crts.aggregate([
            { "$unwind": "$submits" },
            { "$project": {
                "_id": 0,
                "rst": 1,
                "timestamp": "$submits"
            }}
        ]))
    returns = sic_docs + crts_returns
    return returns

async def get_all_searches_service():
    
    sic = db_UJ['test_st']   # create/get a collection
    crts = db_UJ['test_rst']   # create/get a collection

    sic_docs = list(sic.find({'submits': {'$exists': True}},{"_id":0,"ph":0,"r_id":0}))
    crts_call_results = list(crts.find({'submits': {'$exists': True}},{"_id":0}))
    all_results = sic_docs + crts_call_results

    # transformed converts `all_results` which is a list of dicts. Conversions are such:
    # [{'fid_st': 1, 'submits': 2}, {'airport_st': 3, 'submits': 4}] --- > [{1: 2}, {3: 4}]
    transformed = [{v1: v2} for d in all_results for v1, v2 in zip(d.values(), list(d.values())[1:])]
    return serialize_document_list(transformed)

async def get_user_searches_service(email):
    # Supposed to show all the searches that have been made by the user.
    all_results = collection_searchTrack.find({"email": email})
    return serialize_document_list(all_results)

async def raw_search_handler_service(search: str = None):
    """ handles the submit that is NOT the drop down suggestion. So just willy nilly taking
    the organic search submit handlling it here by converting to a form that is acceptable in details.jsx"""
    si = SearchInterface()
    return si.raw_submit_handler(search=search)