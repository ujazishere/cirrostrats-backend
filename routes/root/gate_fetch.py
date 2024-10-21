from config.database import collection_gates
from bson import ObjectId
try:
    from .root_class import Root_class, Fetching_Mechanism, Source_links_and_api, Root_source_links
except:
    print('jupyter import for root_class')
    from routes.root.root_class import Root_class, Fetching_Mechanism, Source_links_and_api, Root_source_links
import datetime as dt
import json
import pickle
from pymongo import UpdateOne
from routes.root.weather_parse import Weather_parse

"""
 Check test_weather.py for set and unset operation.
"""
class Gate_fetch:


    def __init__(self) -> None:
        self.rc = Root_class()
        self.sl = Source_links_and_api()
        self.fm = Fetching_Mechanism()
        self.rsl = Root_source_links

    def mdb_unset(self,):
        # Attempt to update the document. In this case remove a field(key value pair).
        weather = {             # This weather dict wouldnt be necessary since the unset operator is removing the whole weather field itself.
            'metar':'',
            'taf':'',
            'datis':''
        }
        for each_d in collection_gates.find():
            airport_id = "K"+each_d['code']
        
            collection_gates.update_one(
                {'_id':each_d['_id']},            # This is to direct the update method to the apporpriate id to change that particular document
                
                {'$unset': {'weather':weather}},
                # When you use $unset with the key weather, it removes the entire weather field, not just the contents inside it.
                upsert=True
                )
    

    def mdb_updates(self,resp_dict: dict, weather_type):
        # This function creates a list of fields/items that need to be upated and passes it as bulk operation to the collection.
        # TODO: account for new airport codes, maybe upsert or maybe just none for now.
        print('Updating mdb')
        update_operations = []
    
        for url, weather in resp_dict.items():
            airport_code_trailing = str(url)[-3:]
            
            update_operations.append(
                UpdateOne({'code': airport_code_trailing},
                          {'$set': {f'weather.{weather_type}': weather}})
            )

        result = collection_weather.bulk_write(update_operations)
        print(result)


    def flight_mdb_updates(self, flightNumbers, scheduledDeparture, scheduledArrival,):
        # TODO: account for new airport codes for scheduled departure/arriva, maybe upsert or maybe just none for now.
        print('Updating flights mdb')
        update_operations = []
    
        for flightNumber in  flightNumbers:
            
            update_operations.append(
                UpdateOne({'flightNumber': flightNumber},
                          {'$set': {'flightNumber': flightNumber}}
                          )
            )

        result = collection_weather.bulk_write(update_operations)
        print(result)


    def datis_processing(self, resp_dict:dict):
        print('Processing Datis')
        # datis raw returns is a list of dictionary when resp code is 200 otherwise its a json return as error.
        # This function processess the raw list and returns just the pure datis
        for url,datis in resp_dict.items():
            if not 'error' in datis:
                raw_datis_from_api = json.loads(datis)
                raw_datis = Weather_parse().datis_processing(raw_datis_from_api)
                resp_dict[url]=raw_datis
   
        return resp_dict


    async def fetch_and_store(self,):
        print('Initiating the weather fetch.')
        for weather_type, weather_links in self.weather_links_dict.items():
            # This is one way to do it in the terminal. Or rather outside of the jupyter. Might need dunder name == main for it tho. -check bulk_datis_extrator
            # Check datis bulk extract and bulk weather extract for help on this.
            print(weather_type)
            if weather_type == 'taf':
                print(f'For {weather_type}...')
                resp_dict: dict = await self.fm.async_pull(list(weather_links))
                
                # Datis needs special processing before you put into collection. This bit accomplishes it
                if weather_type == 'datis':
                    resp_dict = self.datis_processing(resp_dict)
                
                self.mdb_updates(resp_dict,weather_type)
                # THATS IT. WORK ON GETTING THAT DATA ON THE FRONTEND AVAILABLE AND HAVE IT HIGHLIGHTED.
        
