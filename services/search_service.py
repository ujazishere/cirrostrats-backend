import math
import re
from config.database import airport_bulk_collection_uj, collection_flights, collection_airports_cache_legacy, db_UJ
from core.search.fuzz_find import fuzz_find
from core.search.search_interface import ExhaustionCriteria, SearchInterface
from core.search.query_classifier import QueryClassifier
from models.model import SearchData
from bson import ObjectId
from schema.schemas import serialize_document_list
try:        # This is in order to keep going when collections are not available
    from config.database import collection_airports_cache_legacy, collection_searchTrackUsers
    from config.database import collection_flights, db_UJ
except Exception as e:
    print('Mongo collection(Luis) connection unsuccessful\n', e)


qc = QueryClassifier()
qc.scc_docs = qc.initialize_suggestions_cache_collection()
print('Suggestions Cache Collection initialized with documents:', len(qc.scc_docs))



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
    suggestions_match = fuzz_find(query=query, data=qc.scc_docs, qc=qc, limit=limit)

    if suggestions_match and len(query)<=3:
        serialized_suggestions_match = serialize_document_list(suggestions_match)
        return serialized_suggestions_match
    # Exhaustion criteria:
    elif not suggestions_match and len(query)>=3:        # Exhaustion criteria for query length that is at least 3 characters.
        # TODO search suggestions: 
                # Aggregate all the collections and search them all at once. found items upto 5 items only should be formatted for frontend.
                # If more than 5 items are found then return the top 5 items only.
                # But what about the airport code search with ICAO code prepended with K for USA and C for Canada?

        print('suggestions running out with query length of', len(query), 'and is less than or equal to 3', len(suggestions_match))
        # At exhaustion it will search the extended collections(flight,airport,etc) based on the 'type of query as follows.
        parsed_query = qc.parse_query(query=query)
        # Attempt to parse the query and do dedicated formating to pass it again to the fuzz find since these collections will be different to search index collection.
        # query_type,query_val,query_type = sint.query_type_frontend_conversion(doc=parsed_query)

        exhaust = ExhaustionCriteria()
        query_type = parsed_query.get('type')
        if query_type in ['flight', 'digits', 'nNumber']:
            flight_category = parsed_query.get('value')
            return exhaust.extended_flight_suggestions_formatting(flight_category)
        elif query_type == 'airport':       # only for US and Canadian ICAO airport codes.
            ICAO_airport_code = parsed_query.get('value')
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
    
    sic = db_UJ['search_index']   # create/get a collection
    crts = db_UJ['test_rst']   # create/get a collection

    sic_docs = list(sic.find({'submits': {'$exists': True}},{"_id":0,"ph":0,"r_id":0}))
    crts_call_results = list(crts.find({'submits': {'$exists': True}},{"_id":0}))
    all_results = sic_docs + crts_call_results

    # transformed converts `all_results` which is a list of dicts. Conversions are such:
    # [{'fid_st': 1, 'submits': 2}, {'airportDisplayTerm': 3, 'submits': 4}] --- > [{1: 2}, {3: 4}]
    transformed = [{v1: v2} for d in all_results for v1, v2 in zip(d.values(), list(d.values())[1:])]
    return serialize_document_list(transformed)

async def get_user_searches_service(email):
    # Supposed to show all the searches that have been made by the user.
    all_results = collection_searchTrackUsers.find({"email": email})
    return serialize_document_list(all_results)

async def raw_search_handler_service(search: str = None):
    """ handles the submit that is NOT the drop down suggestion. So just willy nilly taking
    the organic search submit handlling it here by converting to a form that is acceptable in details.jsx"""
    si = SearchInterface()
    return si.raw_submit_handler(search=search)