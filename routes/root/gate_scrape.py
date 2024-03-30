import threading
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
        self.outlaws_reliable = dict()

    
    def pick_flight_data(self, flt_num):
        # refer to activator()
        
        # This function returns a dict with value of list that contains 3 items. Refer to the `return` item
        airline_code = flt_num[:2]      # first 2 characters of airline code eg. UA, DL
        flight_number_without_airline_code = flt_num[2:]
        
        eastern = pytz.timezone('US/eastern')
        now = datetime.now(eastern)
        raw_date = now.strftime('%Y%m%d')           # formatted as YYYYMMDD
        
        flight_view = f"https://www.flightview.com/flight-tracker/{airline_code}/{flight_number_without_airline_code}?date={raw_date}&depapt=EWR"
        soup = self.request(flight_view, timeout=5)
        raw_bs4_scd2 = soup.find_all('td')


        # Schedule and terminal information with a lot of other garbage:
        scd = []
        [scd.append(i.text.strip()) for i in raw_bs4_scd2 if i != '']

        scheduled = scd[2].replace('\xa0', '')
        actual = scd[3].replace('\xa0', '')
        
        gate = scd[4]
        
        # Flight.objects.
        
        reliable_flt_num = re.match(r'[A-Z]{2}\d{2,4}', flt_num)
        if reliable_flt_num and gate and scheduled and actual:
            if "Terminal" in gate and scheduled != 'Not Available' and actual != 'Not Available':
                # The "Not Available" should also be displayed on the web since it contains atleast the flight number
                # and maybe even the scheduled time of departure.
                scheduled = self.dt_conversion(scheduled)
                actual = self.dt_conversion(actual)
                
                return {flt_num: [gate, scheduled, actual]}
            else:
                print('g',gate, 'f', flt_num)
                # TODO: Have to deal with these outlaws and feed it back into the system.
                    # Sometimes gate goes into scheduled or actual. Beware of that kind of data.
                self.outlaws_reliable.update({
                    'flight_number': flt_num,
                    'gate': gate,
                    'scheduled': scheduled,
                    'actual': actual,
                })

        # This is a format that resembles more to the format in the final output.
        # return {'flight_num': flt_num, 'gate': gate, 'scheduled': scheduled, 'actual': actual}


    def tro(self):

        # Reopening master to check troubled flights within it.
        
        # TODO:There is a probelm with opening the gate_query_database.pkl file as is.
            # Troubled items will already be in this master from old data so they wont be checked and updated
            # one way to fix it is to check date and time and overwrite the old one with the latest one
        master = self.load_master()
        
        # feeding self.troubled into the executor using for loop for a few times to restrict infinite troubles, if any. 
        # In a while loop a troubled item may not convert creating endless loop. Hence a for loop(max 5 attempts to minimize excessive waits)
        for i in range(3):
            if self.troubled:
                time.sleep(3)
                ex = self.exec(self.troubled, self.pick_flight_data)
                master.update(ex['completed'])
                self.troubled = set(ex['troubled'])     # emptying out troubled and refilling it with new troubled items

                # Following code essentially removes troubled items that are already in the master.
                # logic: if troubled items are not in master make a new troubled set with those. Essentially doing the job of removing master keys from troubled set
                self.troubled = {each for each in self.troubled if each not in master}
                
                # Here we check how many times we've looped so far and how many troubled items are still remaining.
                print(f'{i}th trial- troubled len:', len(self.troubled) )
            elif not self.troubled:
                print('all self.troubled completed')
                # breaking since troubled is probably empty
                break
        
        # Refer to the activator() master dump. This dump is updated after..
        # Investigate. This one I suppise was only reaading then I changedd it to write
        # But i realised it would overright the old master so I switcheed it back to rb.
        # However. Master is loaded earlier using load_master. so master seems retained so it can be a write file.
        with open('gate_query_database.pkl', 'wb') as f:
            pickle.dump(master, f) 
        
        print(self.date_time(), f'Troubled: {len(self.troubled)}, Master : {len(master)}')


    def temp_fix_to_remove_old_flights(self):
        
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
        
        # Purpose of this file is to dump gate_query_database.pkl file.

        # Extracting all United flight numbers in list form to dump into the exec func
        ewr_departures_UA = Newark_departures_scrape().united_departures()

        # Dmping all flight numbers for newark united departures.
        # with open('ewr_departures_UA.pkl', 'wb') as f:
            # pickle.dump(ewr_departures_UA, f)
        
        # VVI Check exec func for notes on how it works. It takes in function as its second argument without double bracs.
        exec_output = self.exec(ewr_departures_UA, self.pick_flight_data)    # inherited from root_class.Root_class
        completed_flights = exec_output['completed']
        troubled_flights = exec_output['troubled']
        
        # Cant decide if master should be called or kept empty. When kept empty it saves disk space. When called it keeps track of old information.
        # master = self.load_master()
        master = {}
        master.update(completed_flights)
        self.troubled.update(troubled_flights)
        
        # get all the troubled flight numbers
        # print('troubled:', len(self.troubled), self.troubled)

        # Dumping master dict into the root folder in order to be accessed by ewr_UA_gate func later on.
        with open('gate_query_database.pkl', 'wb') as f:
            pickle.dump(master, f) 

        # Redo the troubled flights
        if self.troubled:
            self.tro()
        
        
# Mind the threading. Inheriting the thread that makes the code run concurrently
# TODO: Investigate and master this .Thread sorcery
class Gate_scrape_thread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.gate_scrape = Gate_Scrape()

    
    # run method is inherited through .Thread; It gets called as
    def run(self):
        
        # self.gc.activator()
        while True:
            print('Lengthy Scrape  in progress...')
            # TODO: Investigate this async sorcery
            self.gate_scrape.activator()
            
            eastern = pytz.timezone('US/eastern')           # Time stamp is local to this Loop. Avoid moving it around
            now = datetime.now(eastern)
            latest_time = now.strftime("%#I:%M%p, %b %d.")
            print('Pulled Gate Scrape at:', latest_time, eastern)
            
           # TODO: Requires stops between 11:55pm and 4am while also pulling flights from morning once. 
            time.sleep(1800)        
# flights = Gate_checker('').ewr_UA_gate()


