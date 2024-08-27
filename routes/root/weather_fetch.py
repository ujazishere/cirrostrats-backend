from config.database import collection_weather,collection
from bson import ObjectId
try:
    from .root_class import Root_class, Fetching_Mechanism, Source_links_and_api, Root_source_links
except:
    print('jupyter import for root_class')
    from routes.root.root_class import Root_class, Fetching_Mechanism, Source_links_and_api, Root_source_links
import datetime as dt
import asyncio
import requests
import json


"""
 Check test_weather.py for set and unset operation.
# TODO: user collections - weather.metar if there  is a achange.
"""

class Weather_fetch:


    def __init__(self) -> None:
        # all_airport_codes = [i['code'] for i in collection.find({})]
        pass


    async def all_weather_fetch(self,):
        rc = Root_class()
        sl = Source_links_and_api()
        fm = Fetching_Mechanism()


        rsl = Root_source_links

        # TODO: Works. Just need to make this run every 5 mins. finallu created weather field. 
        for each_d in collection_weather.find():
            weather = {}
            airport_id = "K"+each_d['code']
            # resp_dict: dict = await fm.async_pull(list(weather_links))
            weather = {}
            for weather_type in ['metar', 'taf', 'datis']:
                fetch_link = rsl.weather(weather_type=weather_type,airport_id=airport_id)
                weather_return = requests.get(fetch_link)

                # if its metar or taf it doesn't need json processing, datis does. 
                if weather_type == 'metar' or weather_type =='taf':
                    weather_return = weather_return.content.decode("utf-8")
                    # if fetch is the same as old then keep the og one.
                    # TODO: need to account for new null fetch as well. if new is null keep the og.
                    # TODO: use collections - weather.metar if there  is a achange.
                    if weather_return == each_d['weather'][weather_type]:   
                        weather_return = each_d['weather'][weather_type]

                elif weather_type =='datis':
                    weather_return = json.loads(weather_return.content)
                    if weather_return['error']:
                        weather_return = {}
                    if weather_return == each_d['weather'][weather_type]:
                        weather_return = each_d['weather'][weather_type]

                if weather_return:
                    weather[weather_type] = weather_return
                    print('within here')


            print('final',weather)
            collection_weather.update_one(
                {'_id':each_d['_id']},            # This is to direct the update method to the apporpriate id to change that particular document
                {'$set': {'weather':weather}},
                upsert=True
                )


                # utc_now = dt.datetime.now(dt.UTC)
                # yyyymmddhhmm = utc_now.strftime("%Y%m%d%H%M")



    async def all_weather_fetch_async(self,):
        rsl = Root_source_links
        fm = Fetching_Mechanism()
        all_airport_codes = [i['code'] for i in collection.find({})]
        # weather_links = [rsl.weather(weather_type="metar",airport_id="K"+each_airport_code) for each_airport_code in all_airport_codes]
        # resp_dict: dict = await fm.async_pull(list(weather_links))
        
        test_airports = all_airport_codes[:10]       
        test_weather_links = [rsl.weather(weather_type="metar",airport_id="K"+each_airport_code) for each_airport_code in test_airports]
        resp_dict: dict = await fm.async_pull(list(test_weather_links))
        for a, b in resp_dict.items():
            print(str(a)[-3:])
        


        

        # This code iters through the airports database and refers the airports to the weeather document. 
        for i in collection.find({}):
            airport_code = i['code']

            collection_weather.insert_one({'airport':ObjectId(i['_id']),
                                            'metar':'some val',
                                            'taf':'some extra'})
        return resp_dict