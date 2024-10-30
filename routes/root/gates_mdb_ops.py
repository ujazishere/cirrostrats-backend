from config.database import collection_gates
try:
    from .root_class import Root_class, Fetching_Mechanism, Source_links_and_api, Root_source_links
except:
    print('jupyter import for root_class')
    from routes.root.root_class import Root_class, Fetching_Mechanism, Source_links_and_api, Root_source_links
from pymongo import UpdateOne

"""
#  Check mdb_doc.py for set and unset operation.
#  notebook code:
from config.database import collection_gates, collection_flights,collection, collection_weather
# [i for i in collection_gates.find()][:5]      # Returns first 5 documents for testing - inefficient.
from routes.root.gate_scrape import Gate_Scrape

gs = Gate_Scrape()
rets = gs.activator()

for a,b in rets.items():
    print(a,b)
"""
class Gates_mdb_ops:


    def __init__(self) -> None:
        pass

    def mdb_unset(self,field_to_unset:str):
        # Remove entire field from the document.
        collection_gates.update_many(
            {},     # Match all documents
            {'$unset': {field_to_unset: ''}}        # unset/remove the entire flightStatus field including the field itself.
        )
    

    def mdb_updates(self,incoming_data: list):
        # TODO: WIP to update gates in bulk
        # TODO: Need mechanism to update flight numbers, scheduled departure and scheduled arrival consistently and more frequently.
        
        # This function creates a list of fields/items that need to be upated and passes it as bulk operation to the collection.
        # TODO: account for new airport codes, maybe upsert or maybe just none for now.
        print('Updating mdb')
        update_operations = []

        for i in incoming_data:
            if i:           # i is supposed to be a dict, but is sometimes NoneType
                # TODO 10/29/24 handle this with regex. This can be error prone since there is a magic number.
                i['gate'] = "Terminal " + i['gate'][8:]         # Accounting for no space issue between `Terminal` and trailing data.

                # Neeed to add notes on how to use UpdateOne as arg without the curly braces including identifying the field and what they do.
                update_operations.append(
                    UpdateOne(
                        {'Gate': i['gate']},        # Find the document with gate
                        {'$set': {                  # Set the respective fields in the document as follows
                            f'flightStatus.{i.get("flt_num")}.scheduledDeparture': i.get('scheduled'),
                            f'flightStatus.{i.get("flt_num")}.actualDeparture': i.get('sctual'),
                            },
                        })
                )

        result = collection_gates.bulk_write(update_operations)
        print(result)
