from config.database import collection_weather,collection
from bson import ObjectId
from .root_class import Root_class, Fetching_Mechanism, Source_links_and_api, Root_source_links
import asyncio


class Weather_fetch:


    def __init__(self) -> None:
        pass


    async def all_weather_fetch(self,):
        rc = Root_class()
        sl = Source_links_and_api()
        rsl = Root_source_links
        fm = Fetching_Mechanism()

        #TODO: Planning on constructing a mass fetch similar to bulk extracts.
            # get all airport codes, get all links to those airports and create tasks.
            # Then use these tasks to fetch concurrently and save in the database as it becomes available.
            # implement health checks such that 
        all_airport_ids = [i['code'] for i in collection.find({})]

        # TODO: inefficiency-airports that return null consistently should be fetched less frequently.
            # Track airports that are trending frequent updates and update them frequently and ones that dont update much should be fetched less fequently. This will be a milestone in efficiency.
        weather_links = [rsl.weather("metar",airport_id=each_airport_id) for each_airport_id in all_airport_ids]
        resp_dict: dict = await fm.async_pull(list(weather_links))
        

        # This code iters through the airports database and refers the airports to the weeather document. 
        for i in collection.find({}):
            airport_code = i['code']

            collection_weather.insert_one({'airport':ObjectId(i['_id']),
                                            'metar':'some val',
                                            'taf':'some extra'})
        return resp_dict