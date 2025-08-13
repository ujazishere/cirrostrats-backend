from .root_class import Root_class
from .api.newark_departures import Newark_departures_scrape
from config.database import db_UJ        # UJ mongoDB
from datetime import datetime, timedelta
import logging
from pymongo import ReplaceOne
import pytz
import re

""" The idea is to keep the processing separate from the scrapes so scrapes can be reused elsewhere if needed.
    This will keep all api and scrapes separate from the processings.
"""
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


class Gate_processor(Root_class):
    def __init__(self) -> None:
        super().__init__()
        self.gates_collection = db_UJ['ewrGates']   # create/get a collection


    def mdb_updates(self, incoming_docs: list, update_type=None):
        """ Update collecion based on flight id - replace old with new. """

        update_operations = []
        for doc in incoming_docs:
            update_operations.append(
                ReplaceOne({"FlightID": doc["FlightID"]}, doc, upsert=True)
            )

        result = self.gates_collection.bulk_write(update_operations)
        logger.info(f"Updated {result.modified_count} documents in the collection, on {update_type}") #

    
    def mdb_gate_fetch(self, gate_request):
        find_crit = {'Gate':{'$regex':gate_request}}
        return_crit = {'_id':0}
        flights = list(self.gates_collection.find(find_crit, return_crit))
        flights = sorted(flights, key=lambda x: datetime.strptime(x['Scheduled'], '%B %d, %Y %H:%M'), reverse=True)
        return flights


    def mdb_clear_historical(self,hours=30):
        """ Clears docs with Scheduled times prior to 48 hours before the scheduled time """
        et = pytz.timezone('US/Eastern')
        current_time = datetime.now(et)
        
        delete_crit = {'Scheduled': {'$lt': (current_time - timedelta(hours=hours)).strftime('%B %d, %Y %H:%M')}}
        # for i in d:
            # print(i)
        # Delete documents that are prior to 48 hours of scheduled time
        result = self.gates_collection.delete_many(delete_crit)
        print('Delete crit:', delete_crit)
        print(f"Deleted {result.deleted_count} documents")


    def recurrent_updater(self):
        """ flights around current eastern time are updated. """
        
        # Define the Eastern Time zone
        eastern = pytz.timezone('US/Eastern')
        
        # Get the current time in Eastern Time zone
        current_time = datetime.now(eastern)
        
        # Define the time range in this case between 1/2 hour past the current time and 2 post from the current time
        start_time = current_time - timedelta(hours=0.5)
        end_time = current_time + timedelta(hours=2)
        
        # Convert start_time and end_time to string format
        start_time_str = start_time.strftime('%B %d, %Y %H:%M')
        end_time_str = end_time.strftime('%B %d, %Y %H:%M')
        
        # Define the filter
        filter = {
            "Scheduled": {"$gte": start_time_str, "$lte": end_time_str},
            # Exclude scrapes for flights that have already departed
            "Departed": {"$exists": False}
        }
        
        # Define the projection
        projection = {
            "_id": 0,
            # "Scheduled": 1,
            "FlightID": 1
        }
        
        # Now execute the find and return the docs
        docs = list(self.gates_collection.find(filter, projection))

        nds = Newark_departures_scrape()
        flight_rows = []
        for doc in docs:
            flight_id = doc.get('FlightID')
            if not flight_id:
                continue
            link = "/newark-flight-status?departure="+flight_id

            if flight_id[:2] == "UA" and link:          # Fail safe
                # time.sleep(1)  # Respectful scraping delay
                scrape_extract = nds.gate_scrape_per_flight(flight_id,link)
                flight_rows.append(scrape_extract)

        self.mdb_updates(incoming_docs=flight_rows, update_type='light recurrent scrape save')


    def scrape_and_store(self,):
        
        nds = Newark_departures_scrape()
        flight_rows = nds.gate_scrape_main()

        self.mdb_updates(incoming_docs=flight_rows,update_type='initial scrape save')







# Legacy code.
    # def activator(self):
        # exec_output = self.exec(self.ewr_departures_UA, self.pick_flight_data)    # inherited from root_class.Root_class
        # completed_flights = exec_output['completed']
        # pass


    # def mdb_unset(self,field_to_unset:str):
    #     # Remove entire field from the document.
    #     collection_gates.update_many(
    #         {},     # Match all documents
    #         {'$unset': {field_to_unset: ''}}        # unset/remove the entire flightStatus field including the field itself.
    #     )


    # def pick_flight_data(self, flt_num):            # *** Depricated ***
    #     eastern = pytz.timezone('US/eastern')
    #     now = datetime.now(eastern)
    #     raw_date = now.strftime('%Y%m%d')       # formatted as YYYYMMDD
    #     flight_view = f"https://www.flightview.com/flight-tracker/{airline_code}/{flight_number_without_airline_code}?date={raw_date}&depapt=EWR"
        

    #     reliable_flt_num = re.match(r'[A-Z]{2}\d{2,4}', flt_num)
    #     if reliable_flt_num and gate and scheduled and actual:
    #         if "Terminal" in gate and scheduled != 'Not Available' and actual != 'Not Available':
    #             # The "Not Available" should also be displayed on the web since it contains atleast the flight number
    #             # and maybe even the scheduled time of departure.

    #             return {
    #                 'flight_number': flt_num,
    #                 'gate': gate,
    #                 'scheduled': scheduled,
    #                 'actual': actual,
    #             }
    #             # return {flt_num: [gate, scheduled, actual]} # This is the old and depricated way of doing things.
    #         else:
    #             print('unreliable matches:','gate:',gate, 'flt_num:', flt_num)
    #             self.outlaws_reliable.append({
    #                 'flight_number': flt_num,
    #                 'gate': gate,
    #                 'scheduled': scheduled,
    #                 'actual': actual,
    #             })

