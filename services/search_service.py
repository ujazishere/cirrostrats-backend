import math
import re
from config.database import airport_bulk_collection_uj, collection_flights, collection_airports_cache_legacy, db_UJ
from core.search.fuzz_find import fuzz_find
from core.search.search_interface import ExhaustionCriteria, SearchInterface
from core.search.query_classifier import QueryClassifier
from models.model import SearchData
from bson import ObjectId
from schema.schemas import serialize_document_list
try:
    from config.database import collection_searchTrackUsers
    from config.database import db_UJ
except Exception as e:
    print('Mongo collection(Luis) connection unsuccessful\n', e)


qc = QueryClassifier()
qc.scc_docs = qc.initialize_suggestions_cache_collection()
print('Suggestions Cache Collection initialized with documents:', len(qc.scc_docs))


async def get_search_suggestions_service(email: str, query: str, limit=500):  # Default page and page size
    """ Cached fuzzy search to improve performance for repeated queries.
        The Idea is to have some sort of a cache that holds the initial popular fetches of upto 500 items(of the total 500 cached items curently) in suggestions and display only upto 5 in the drop-down.
        If the suggestions(display dropdown items) drop below 5 items then it should fetch the backend with the `latest query` to see if it returns any matches.
        Current state: Upto 2nd alphabet from `latest query` can match upto maybe <10 items of the total cache collection for this cache and return those to the frontend exhausting all.

        The interface is designed such that it has pre existing values from suggestion_cache_collection
        these dont currently update with new raw submits. also older submits may be intensive on processing during /st route on frontend lookup
        """

    # TODO VHP:
    """ 
        Priority vs necessity:
            The frontend data structure that processes collections across flights, airports, gates, sic is flawed and inconsistent
            You need this to properly implement track search in its entirity-> match and track raw submits, integrate popularity hits,  
            caching and morphing suggestions cache collection.

        Additionally:
        data flow - use raw submit to *___ query the collection ___*  based on parseQuery:
        save in suggestions cache collection in the background(so it doesnt log data delivery) thén send it to the frontend for fetching just like search suggestions dropdowns.
            ***___ Minimize the ability for user to have raw searches- match all raw searches to appropriate item in collections ___***
    """
    suggestions_match = fuzz_find(query=query, data=qc.scc_docs, qc=qc, limit=limit)

    # TODO search suggestions: LAS - harry reid international airport isnt showing up when looking up `las` but shows up when looking up `harry reid`.
    if suggestions_match:
        serialized_suggestions_match = serialize_document_list(suggestions_match)
        return serialized_suggestions_match
    # Exhaustion criteria:
    elif not suggestions_match and len(query)>=3:        # Exhaustion criteria for query length that is at least 3 characters- to reduce backend load.
        print('suggestions cache exhausted, running exhaustion criteria with query length of', len(query), 'and query is', query)
        parsed_query = qc.parse_query(query=query)
        # At exhaustion it will search the extended collections(flight,airport,etc) based on the 'type of query as follows.
        # Attempt to parse the query and do dedicated formating to pass it again to the fuzz find since these collections will be different to search index collection.
        # query_type,query_val,query_type = sint.query_type_frontend_conversion(doc=parsed_query)

        si = SearchInterface()
        return si.exhaustion_criteria_handler(parsed_query=parsed_query)


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