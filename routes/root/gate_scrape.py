import threading
from config.database import collection_gates
from routes.root.gate_fetch import Gate_fetch
from .root_class import Root_class
from .newark_departures_scrape import Newark_departures_scrape
from datetime import datetime
import time
import pickle
import pytz
import re
# from models import Flight       # This doesnt work because models is in the upper directory


class Gate_Scrape(Root_class):
    def __init__(self) -> None:
        super().__init__()

        # troubled is setup here so that it can be accessed locally
        self.troubled = set()
        self.outlaws_reliable = []

    
    def pick_flight_data(self, flt_num):
        # refer to activator()
        
        # This function returns a dict with value of list that contains 3 items. Refer to the `return` item
        airline_code = flt_num[:2]      # first 2 characters of airline code eg. UA, DL
        flight_number_without_airline_code = flt_num[2:]
        
        # TODO: Update actual more frequently and scheduled less frequently to get delayed flights info. maybe couple times a day for scheduled.
            # Scheduled ones are usually very much planned. Repo and non-scheduled have been accounted for.
            # Highlight late ones in red
        eastern = pytz.timezone('US/eastern')
        now = datetime.now(eastern)
        raw_date = now.strftime('%Y%m%d')       # formatted as YYYYMMDD
        flight_view = f"https://www.flightview.com/flight-tracker/{airline_code}/{flight_number_without_airline_code}?date={raw_date}&depapt=EWR"
        
        soup = self.request(flight_view, timeout=5)
        raw_bs4_scd2 = soup.find_all('td')

        # Schedule and terminal information with a lot of other garbage:
        scd = []
        [scd.append(i.text.strip()) for i in raw_bs4_scd2 if i != '']

        scheduled = scd[2].replace('\xa0', '')
        actual = scd[3].replace('\xa0', '')
        gate = scd[4]
        
        reliable_flt_num = re.match(r'[A-Z]{2}\d{2,4}', flt_num)
        if reliable_flt_num and gate and scheduled and actual:
            if "Terminal" in gate and scheduled != 'Not Available' and actual != 'Not Available':
                # The "Not Available" should also be displayed on the web since it contains atleast the flight number
                # and maybe even the scheduled time of departure.
                scheduled = self.dt_conversion(scheduled)
                actual = self.dt_conversion(actual)

                # TODO VHP: return as list of dictionaries to make the format consistent with gate_checker.py's ewr_UA_gate func's initial parses
                return {
                    'flight_number': flt_num,
                    'gate': gate,
                    'scheduled': scheduled,
                    'actual': actual,
                }
                # return {flt_num: [gate, scheduled, actual]} # This is the old and depricated way of doing things.
            else:
                print('unreliable matches:','gate:',gate, 'flt_num:', flt_num)
                # TODO WIP: Have to deal with these outlaws and feed it back into the system. Dont suppose it is being used right now.
                    # Sometimes gate goes into scheduled or actual.
                self.outlaws_reliable.append({
                    'flight_number': flt_num,
                    'gate': gate,
                    'scheduled': scheduled,
                    'actual': actual,
                })


    def tro(self):

        # Reopening master to check troubled flights within it.
        
        # TODO:There is a probelm with opening the gate_query_database.pkl file as is.
            # Troubled items will already be in this master from old data so they wont be checked and updated
            # one way to fix it is to check date and time and overwrite the old one with the latest one
        master = self.load_master()
        
        # feeding self.troubled into the executor using for loop for a few times to restrict infinite troubles, if any. 
        # In a while loop a troubled item may not convert creating endless loop. Hence a for loop(max 5 attempts to minimize excessive waits)
        for i in range(3):      # 3 because if the you want to fetch the troubled only a few more times, they might just not be available if theyre not returned within these 3 attempts.
            if self.troubled:
                time.sleep(3)       # This break may resolve temporare redirect issues with error code response on initial fetch
                ex = self.exec(self.troubled, self.pick_flight_data)
                master.update(ex['completed'])
                self.troubled = set(ex['troubled'])     # emptying out troubled and refilling it with new troubled items

                # Following code essentially removes troubled items that are already in the master.
                # logic: if troubled items are not in master make a new troubled set with those. Essentially doing the job of removing master keys from troubled set
                # This wont be overwritten as the it takes itseld as an argument.
                self.troubled = {each for each in self.troubled if each not in master}
                
                # Here we check how many times we've looped so far and how many troubled items are still remaining.
                print(f'{i}th trial- troubled len:', len(self.troubled) )
            elif not self.troubled:
                print('all self.troubled completed')
                # breaking since troubled is probably empty
                break
        
        # Refer to the activator() master dump. This dump is updated after..
        # Investigate. This one I suppose was only reading then I changedd it to write
        # But i realised it would overright the old master so I switcheed it back to rb.
        # However. Master is loaded earlier using load_master. so master seems retained so it can be a write file.
        with open('gate_query_database.pkl', 'wb') as f:
            pickle.dump(master, f) 
        
        print(self.date_time(), f'Troubled: {len(self.troubled)}, Master : {len(master)}')


    def temp_fix_to_remove_old_flights(self):       # TODO: Should be deprercated
        
        # might want to remove this method. It is destructive. Or just get rid of flights from 2 days ago rather than just 1 day since midnight is too close to previous day.
        
        master = self.load_master()
        to_remove = []

        for flight_num, (gate, scheduled, actual) in master.items():
            scheduled = datetime.strptime(scheduled, "%I:%M%p, %b%d") if scheduled else None
            if scheduled and scheduled.date() < datetime.now().date():
                to_remove.append(flight_num)
            else:
                pass
        
        for i in to_remove:
            del master[i]

        with open('gate_query_database.pkl', 'wb') as f:
            pickle.dump(master, f)


    def activator(self):
        
        # Purpose of this function is to dump gate_query_database.pkl file.

        # Extracting all United flight numbers in list form to dump into the exec func
        ewr_departures_UA = Newark_departures_scrape().united_departures()

        # ewr_departures = Newark_departures_scrape().all_newark_departures()
        
        # VVI Check exec func for notes on how it works. It takes in function as its second argument without double bracs.
        exec_output = self.exec(ewr_departures_UA, self.pick_flight_data)    # inherited from root_class.Root_class
        completed_flights = exec_output['completed']
        troubled_flights = exec_output['troubled']
        
        # TODO: This is where the results are returned. since its the `update` method its {flt_num:[gate,sch,act]} 
            # TODO: you want to change it to the format thats being used by gate_checker 
        # TODO: Change name and use case from master to- gate_query_database collection update.
        master = {}
        master.update(completed_flights)        # Master is a complete overwrite whereas troubled is a read master and update it kind.
        self.troubled.update(troubled_flights)  # This is a safer write since it will load the master first and then update with the new data then dump write.
        
        # get all the troubled flight numbers
        # print('troubled:', len(self.troubled), self.troubled)
        
        # if self.troubled:
            # self.tro()

        # Dumping master dict into the root folder in order to be accessed by ewr_UA_gate func later on.
        # TODO: Need to add mdb collection here. maybe instead of the gate collection it should be the flight collection. since the flight number is primary one here.
        # gf = Gate_fetch()

        # gf.mdb_updates(master, 'ewr_united').
        # with open('gate_query_database.pkl', 'wb') as f:
            # pickle.dump(master, f) 

        # Redo the troubled flights

        return master

# Mind the threading. Inheriting the thread that makes the code run concurrently
# TODO: Investigate and master this Thread sorcery
class Gate_scrape_thread(threading.Thread):
    def __init__(self):
        # Super method inherits the init method of the superclass. In this case`Root_class`.
        super().__init__()
        self.gate_scrape = Gate_Scrape()

    
    # run method is inherited through .Thread; It gets called as
    def run(self):
        
        # self.gc.activator()
        while True:
            print('Lengthy Scrape  in progress...')
            # The activator here will scrape and save data into the gate_query_database.pkl file.
            self.gate_scrape.activator()
            
            eastern = pytz.timezone('US/eastern')           # Time stamp is local to this Loop. Avoid moving it around
            now = datetime.now(eastern)
            latest_time = now.strftime("%#I:%M%p, %b %d.")
            print('Pulled Gate Scrape at:', latest_time, eastern)
            
           # TODO: Requires stops between 11:55pm and 4am while also pulling flights from morning once. 
            time.sleep(1800)        
# flights = Gate_checker('').ewr_UA_gate()


