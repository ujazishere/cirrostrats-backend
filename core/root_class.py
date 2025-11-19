import asyncio
import aiohttp
from bs4 import BeautifulSoup as bs4
from concurrent.futures import ThreadPoolExecutor, as_completed

from bson import ObjectId
from config.database import collection_airports_cache_legacy
from config.database import db_UJ        # UJ mongoDB
import datetime as dt
from decouple import config
import pytz
import requests
import smtplib


class Root_class():
    
    def __init__(self) -> None:
            pass


    def send_email(self, body_to_send):
        if config('env') == 'dev':
            return
        else:
            env_type = config('env')
            
            full_email = f"Subject: {env_type}\n\n{body_to_send}"
            print(r'EC2_location within dj\dj_app\root\Switch_n_auth.py was not found. Need the file and the variable as string.')
            full_email = f"Subject: UNKNOWN Local\n\n{body_to_send}"
        smtp_server = "smtp.gmail.com"
        smtp_port = 587  # Use 587 for TLS port
        smtp_user = "publicuj@gmail.com"
        smtp_password = "dsxi rywz jmxn qwiz"
        # Test
        # to_email = ['ujasvaghani@gmail.com',]
        # Actual
        to_email = ['ujasvaghani@gmail.com', 'ismailsakhani879@gmail.com']
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Start TLS for security
            server.starttls()
        
            # Login to the email account
            server.login(smtp_user, smtp_password)
        
            # Send the email
            server.sendmail(smtp_user, to_email, full_email.encode('utf-8'))
        print('SENT EMAIL!!!!!!!!!!!!!:', body_to_send)


    def date_time(self, raw=None, viewable=None, raw_utc=None):
        eastern = pytz.timezone('US/eastern')
        now = dt.datetime.now(eastern)
        latest_time = now.strftime("%#I:%M%p, %b %d.")
        if raw_utc:
            if raw_utc == 'HM':
                yyyymmddhhmm = dt.datetime.now(dt.UTC).strftime("%Y%m%d%H%M")
                return yyyymmddhhmm
            else:
                yyyymmdd = dt.datetime.now(dt.UTC).strftime("%Y%m%d")
                return yyyymmdd
        elif raw:         # format yyyymmdd
            return now.strftime('%Y%m%d')       # date format yyyymmdd
        elif viewable:
            return now.strftime('%b %d, %Y')
        else:
            return latest_time
    

    def request(self, url, timeout=None):
        if timeout:
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.get(url)
        return bs4(response.content, 'html.parser')


    def dt_conversion(self, data):
        # converts date and time string into a class object 
        return dt.datetime.strptime(data, "%I:%M%p, %b%d")


    def exec(self, input1, multithreader):
    
    # TODO: VHP: Have a solid understanding and extract this blueprint for future use.

    # executor blueprint: In this case input1 argument of this exec funtion are a bunch of flight numbers in list form while,
        # `input1` is the list of all flight numbers that need to be fetched.
        # `multithreader` is the pool of task. it contails all the flight number and the function that fetches the gate all together ready to go.
            # In this case multithreader is a function that takes in a flight number and returns its gates.
            # if there are 10 flight numbers the multithreader function will be duplicated 10 times.
        # executor.submit will submit this pool of taks at once to the multithreader function that is the second argument in exec
            # seems like this creates a task list of all functions and all those functions get sent to work at once altogether.
        # this results in all the flight numbers getting sent at once and performing web scrape(`pick_flight_data()`) on all of them simultaneously
    
        completed = []
        troubled = set()
            # VVI!!! The dictionary `futures` .value is the flight number and  key is the the memory location of return from pick_flight_data
            # Used in list comprehension for loop with multiple keys and values in the dictionary. for example:
            # {<Future at 0x7f08f203ec10 state=running>: 'UA123',
                # <Future at 0x7f08f203ed10 state=running>: 'DL789'
                        # }
        with ThreadPoolExecutor(max_workers=150) as executor:
            # First argument in submit method is the lengthy function that needs multi threading
                # second argument is each flt number that goes into that function. Together forming the futures.key()
                #note no parentheses in the first argument
            futures = {executor.submit(multithreader, flt_num): flt_num for flt_num in
                        input1}         # This submit method tasks to do to the executor for concurrent execution.
            # futures .key() is the memory location of the task and the .value() is the flt_num associated with it
            # print('within futures')
            # this forloop is where the tasks are executed is a part of as_completed task
            for future in as_completed(futures):    # as_completed is imported with the ThreadPoolExecutor
                # again, future is the memory location of the task
                flt_num = futures[future]
                try:
                    result = future.result()        # result is the output of the task at that memory location 
                    completed.append(result)
                except Exception as e:
                    print(f"Error scraping {flt_num}: {e}")
                    troubled.add(flt_num)
        
        # TODO: Check completed data type. If list then its a list of dicts. Its outght to be.
        rets = dict({'completed':  completed, 'troubled': troubled})
        # print(rets)
        return rets


class AirportValidation:
    # TODO Refactor: This function probably belongs to core.tests or core validator? or maybe models.model.py ?maybe schema.py ?
    # 
    def __init__(self,):
        """
        icao to iata and vice versa airport code validation will return both iata and icao code.
        others will return singular
        """
        self.airport_bulk_collection_uj = db_UJ['icao_iata']

    def icao_iata_airport_code_validation(self,mdbAirportReferenceId):
        """ 
        Given a MongoDB Airport Reference ID, fetch the corresponding IATA from collection airports and and ICAO using validate airport_code.
        which in turn uses the airport collection to validate the code.
        """
        # TODO VHP - Airports collection
        find_crit = {'_id': ObjectId(mdbAirportReferenceId)}
        return_crit = {'code': 1}
        
        IATA_airport_code = ICAO_airport_code_to_fetch = None
        
        # used collection_airports_cache to get IATA code 
        IATA_airport_code_collection = collection_airports_cache_legacy.find_one(find_crit, return_crit)
        if IATA_airport_code_collection:            # if associated airport in collection_airports_cache_legacy found then get its ICAO code
            av = AirportValidation()
            
            IATA_airport_code = IATA_airport_code_collection.get('code')
            ICAO_airport_code_to_fetch = av.validate_airport_code(airport_code=IATA_airport_code, icao_return=True).get('icao')
        else:           # This is probably an imposible return
            # Throw a python error if the mdbAirportReferenceId is not found
            print('Error: airport_code not found in the weather collection.')
        return IATA_airport_code, ICAO_airport_code_to_fetch


    def validate_airport_code(self, airport_code, iata_return=None, icao_return=None, supplied_param_type=None):
        """ This function validates the airport ID and returns the corresponding IATA or ICAO code.
            Accounting for formats within flightStats derived 3-letter codes, NAS returns, weather input compliance, etc.
            returns:
                iata, icao, airport
        """
        # TODO VHP: Subsequent UNV search from frontend is feeding KUNV. initial search is UNV.
        if isinstance(airport_code, str):
            # TODO VHP: Temporary badaid for UNV IATA issues in collection airport/weather.
            if 'UNV' in airport_code or 'KUNV' in airport_code:
                return {"iata": 'SCE', "icao": 'KUNV'}
            iata_code = icao_code = None
            if len(airport_code) == 3 and iata_return:            # This is for IATA codes returned as is for NAS - prevents unnecessary mdb processing
                return {'iata': airport_code}         # Return the 3-letter IATA code as is
            elif len(airport_code) == 3 and icao_return:
                iata_code = airport_code
                find_crit = {"iata": iata_code}  # Example query to find an airport by IATA code to return its associated ICAO
            elif len(airport_code) == 4 and iata_return:
                icao_code = airport_code
                find_crit = {"icao": icao_code}
            elif len(airport_code) == 4 and icao_return:
                return {'icao': airport_code}         # Return the 4-letter ICAO code as is
            elif len(airport_code) != 3 and len(airport_code) != 4:     # This logic does not make sense fr!
                raise ValueError(f"Invalid {supplied_param_type} airport code: must be 4 or 3 characters")
            else:
                raise ValueError("Supply type of return - iata or icao")
            
            return_crit = {"_id": 0, "iata": 1, "icao": 1, "airport": 1}  # Fields to return

            result = self.airport_bulk_collection_uj.find_one(find_crit,return_crit)  # Example query to find an airport by ICAO code
            return result

class Fetching_Mechanism(Root_class):

    # TODO Refactor: rename this Fetching_Mechanism to Async_fetch and move it to core.async_fetch.py ? or core.api.async_fetch.py ?

    def __init__(self,airline_code=None,flt_num=None,
                 dep_airport_id=None,dest_airport_id=None):
        # TODO refactor: clean up these unused variables
        super().__init__()
        
        # Simplified header that seems to work for most requests for weather
        # self.headers = {
        #     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        # }
        # headers for weather api that seems to work
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/plain,*/*',
        }

        # TODO VHP: need to get rid of this. Search should find the appropriate flight number, w airline code, of all the flight numbers for that day


    async def async_pull(self, list_of_links:list):
        """ Asynchronous data fetching of multiple links."""
        async def get_tasks(session):
            tasks = []
            for url in list_of_links:
                # TODO: Aviation stack maybe possible here through the auth_headers. Previously auth headers were passed with api might have caused it to not work.
                            # Separate the auth and pass as a dict. 
                if isinstance(url, dict):         # This is probs for flight aware
                    url,auth_headers = list(url.keys())[0], list(url.values())[0]
                    tasks.append(asyncio.create_task(session.get(url, headers=auth_headers)))
                else:
                    # This is where the header is needed - since without it weather api fails with 403 Status code.
                    tasks.append(asyncio.create_task(session.get(url, headers=self.headers)))
                    # Prior to header this was:
                    # tasks.append(asyncio.create_task(session.get(url)))
            return tasks
        
        async def main():
            async with aiohttp.ClientSession() as session:
                tasks = await get_tasks(session)
        
                # Actual pull work is done using as_completed 
                resp_return_list = {}
                for resp in asyncio.as_completed(tasks):        # use .gather() instead of .as_completed for background completion
                    resp = await resp
                    content_type = resp.headers.get('Content-Type')
                    if content_type == "application/json":
                        response_output = await resp.json()
                    else:
                        response_output = await resp.text()
                    
                    # print(resp.url,content_type)
                    resp_return_list[resp.url] = response_output
                return resp_return_list

        # print("*** async pull completion")
        #1 Temporary. Works when function calling within jupyter.
        return await main()         

        #2 works for jupyter when copy pasting this whole code within jupyter.
        # link_fetch = await asyncio.ensure_future(main())  
        
        #3 works for external cli use.
        # if __name__ == "__main__":        # if statement seems unnecessary: works when calling from cli, not when importing elsewhere
            # link_fetch = await asyncio.run(main())
            # return await link_fetch
        