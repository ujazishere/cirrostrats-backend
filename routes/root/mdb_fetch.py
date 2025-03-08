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

# shows how the data is structured in the mdb collections.
from routes.root.root_class import Root_class, Fetching_Mechanism, Root_source_links, Source_links_and_api
sl = Source_links_and_api()

flight_number_query = '4433'
# sl.ua_dep_dest_flight_status(flight_number_query)
# sl.flight_stats_url(flight_number_query),

from routes.root.root_class import Root_class, Fetching_Mechanism, Root_source_links, Source_links_and_api


# departures and destinations from particular airports. Need another source for redundancy.
# The other one probs can be flightView.com
import requests
from bs4 import BeautifulSoup as bs4
fv_link = 'https://www.flightview.com/airport/ORD-Chicago-IL-(O_Hare)/departures'
airport_code,year,month,date,hour = 'EWR','2024','11','21','0'
fs_link = f'https://www.flightstats.com/v2/flight-tracker/departures/{airport_code}/?year={year}&month={month}&date={date}&hour={hour}'
response = requests.get(fs_link)
soup_fs = bs4(response.content, 'html.parser')
all_text = soup_fs.get_text()

text_to_search = 'American Airlines'
all_div = soup_fs.find_all('div')
for each_div in all_div:
    each_text = each_div.get_text()
    # We also limit the text size so the blown up or too little texts are avoided
    if text_to_search in each_text and len(each_text) < 100 and len(each_text) > 4: 
        print(each_div)
        print(each_text)

all_items = soup_fs.select('[class*="table__TableRowWrapper"]')
