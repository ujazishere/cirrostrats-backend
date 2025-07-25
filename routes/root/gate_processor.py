from datetime import datetime, timedelta
import pytz
from config.database import db_UJ        # UJ mongoDB
from .root_class import Root_class
from.api.newark_departures import Newark_departures_scrape
from datetime import datetime
import pytz
import re


class Gate_processor(Root_class):
    def __init__(self) -> None:
        super().__init__()
        self.gates_collection = db_UJ['ewrGates']   # create/get a collection


    def mdb_updates(self, incoming_docs: list):
        """ Clears all existing gates and updates with new ones. """
        self.gates_collection.delete_many({})
        self.gates_collection.insert_many(incoming_docs)

    
    def mdb_gate_fetch(self, gate_request):
        # TODO: Update actual more frequently and scheduled less frequently to get delayed flights info. maybe couple times a day for scheduled.
            # Scheduled ones are usually very much planned. Repo and non-scheduled have been accounted for.
            # Highlight late ones in red
        # TODO LP: Gates - Need mechanism to update flight numbers, scheduled departure and scheduled arrival consistently and more frequently.
            #  Maybeb just link it with google url to avoid own proccessing? 
        find_crit = {'Gate':{'$regex':gate_request}}
        return_crit = {'_id':0}
        flights = list(self.gates_collection.find(find_crit, return_crit))
        flights = sorted(flights, key=lambda x: datetime.strptime(x['Scheduled'], '%B %d, %Y %H:%M'), reverse=True)
        return flights


    def mdb_clear_historical(self,hours=48):
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


    def fetch_and_store(self,):
        
        # Extracting all United flight numbers in list form to dump into the exec func
        nds = Newark_departures_scrape()
        # TODO: Currently fetch is in series and not concurrent.
        flight_rows = nds.gate_scrape_main()

        self.mdb_updates(incoming_docs=flight_rows)
        # THATS IT. WORK ON GETTING THAT DATA ON THE FRONTEND AVAILABLE AND HAVE IT HIGHLIGHTED! WASTED ENOUGH TIME!







# Legacy code.
    # def activator(self):
        # TODO: For concurrency utilize following exec func
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

    #             # TODO VHP: return as list of dictionaries to make the format consistent with gate_checker.py's ewr_UA_gate func's initial parses
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

