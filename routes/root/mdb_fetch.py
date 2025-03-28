from routes.root.weather_parse import Weather_parse
from routes.root.dep_des import Pull_flight_info
from config.database import collection, collection_weather, collection_flights, collection_gates, collection_searchTrack

# TODO: save data on elasticSeach or redis. Once fetched from mongo.
# Fetching raw data from raw functions from the backend.
class Mdb_fetch():
    def __init__(self) -> None:
        super().__init__()

    def popular_fetch(email, query):
        # Shows all the searches that have been made by the user.
        # user_data = collection_searchTrack.find_one({"email": email})
        suggestions = []

        # query = "g"    # Search for predertimined items in pipeline containing "ap"
        # page = 1        # first page
        # page_size = 30  # items per page

        print('\n\n\nTriggered email, query, page, page_size', email, query, page=0, page_size=0)
        collection_merge = [collection, collection_flights] 
        for coll in collection_merge:
            pipeline = [
                    {"$match": {"count": {"$exists": True}}},        # filter documents that have a count field
                    # {"$project": {"_id": {"$toString": "$_id", "count": 1}}},
                    {"$match": {"$or": [
                        {"flightNumber": {"$regex": query, "$options": "i"}},       # matches flightNumber field in flights collection
                        {"name": {"$regex": query, "$options": "i"}}                # matches name field in airport collection
                    ]}},
                    # {"$sort": {"count": -1}},               # sort by popularity - the count field contains popularity rating.
                    # {"$skip": (page - 1) * page_size},    # the page number itself.
                    # {"$limit": page_size}                 # items per page
                ]
        
            suggestions.extend(coll.aggregate(pipeline))
        pass

    def non_popular_fetch():
        pass
