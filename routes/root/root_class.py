# from dj.dj_app.root.root_class import Root_class, Fetching_Mechanism
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup as bs4
import datetime as dt
import pytz
import pickle
import smtplib
import asyncio
import aiohttp
from time import sleep

class Root_class():
    
    def __init__(self) -> None:
            pass


    def send_email(self, body_to_send):
        try: 
            from .Switch_n_auth import EC2_location
            full_email = f"Subject: {EC2_location}\n\n{body_to_send}"
        except Exception as e:
            print("error in Switch_n_auth",e)
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


    def load_master(self):
        try:
            with open('gate_query_database.pkl', 'rb') as f:
                return pickle.load(f)
        except:
            with open('dj/gate_query_database.pkl', 'rb') as f:
                return pickle.load(f)


    def dt_conversion(self, data):
        # converts date and time string into a class object 
        return dt.datetime.strptime(data, "%I:%M%p, %b%d")


    def exec(self, input1, multithreader):
    
    # TODO: VVI: Have a solid understanding and extract this blueprint for future use.

    # executor blueprint: In this case input1 argument of this exec funtion are a bunch of flight numbers in list form while,
        # `input1` is the list of all flight numbers that need to be fetched.
        # `multithreaders` is the pool of task. it contails all the flight number and the function that fetches the gate all together ready to go.
            # In this case multithreaders is a function that takes in a flight number and returns its gates.
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
                    # print(f"Error scraping {flt_num}: {e}")
                    troubled.add(flt_num)
        
        # TODO: Check completed data type. If list then its a list of dicts. Its outght to be.
        rets = dict({'completed':  completed, 'troubled': troubled})
        # print(rets)
        return rets
        

class Root_source_links:

    def __init__(self) -> None:
        pass

    def weather(weather_type,airport_id):
        urls = {
            "metar": f"https://aviationweather.gov/api/data/metar?ids={airport_id}",
            "taf": f"https://aviationweather.gov/api/data/taf?ids={airport_id}",
            "datis": f"https://datis.clowd.io/api/{airport_id}",
        }
        return urls.get(weather_type)

        
class Source_links_and_api:
    def __init__(self,):
        pass

    def ua_dep_dest_flight_status(self, flight_number):
        # reeturns a dictionay paid of departure and destination
        return f"https://united-airlines.flight-status.info/ua-{flight_number}"               # This web probably contains incorrect information.
    

    def flight_stats_url(self,flight_number):
        # local time zones. just needs flight number and date as input
        
        date = Root_class().date_time(raw=True)
        
        base_url = "https://www.flightstats.com/v2/flight-tracker/"
        return f"{base_url}UA/{flight_number}?year={date[:4]}&month={date[4:6]}&date={date[-2:]}"


    def aviation_stack(self,airline_code, flight_number):
        # TODO: Fix airline code issue. This is not used yet. Find use case.
        # Aviation Stack api call. 3000 requests per month
        """
        aviation_stack_url = 'http://api.aviationstack.com/v1/flights'
        aviation_stack_params = {
                            'access_key': '65dfac89c99477374011de39d27e290a',
                            'flight_icao': f"{airline_code}{flight_number}"}
        # aviationstack is just like flight_aware
        av_stack_url_w_auth = {aviation_stack_url:aviation_stack_params}
        return  av_stack_url_w_auth
        """
        print('Within av stack sl')
        base_url = "http://api.aviationstack.com/v1/flights"
        access_key = "65dfac89c99477374011de39d27e290a"
        flight_icao = f"{airline_code}{flight_number}"
        
        url = f"{base_url}?access_key={access_key}&flight_icao={flight_icao}"
        
        return {url: {}}  


    def flight_aware_w_auth(self,airline_code, flight_number):
        if not airline_code:
            airline_code = "UA"
        fa_apiKey = "G43B7Izssvrs8RYeLozyJj2uQyyH4lbU"         # New Key from Ismail
        fa_auth_header = {'x-apikey':fa_apiKey}
        fa_base_apiUrl = "https://aeroapi.flightaware.com/aeroapi/"
        fa_url = fa_base_apiUrl + f"flights/{airline_code}{flight_number}"
        fa_url_w_auth = {fa_url:fa_auth_header}
        return fa_url_w_auth


    def nas(self,):
        return  "https://nasstatus.faa.gov/api/airport-status-information"


    def flight_view_gate_info(self,flight_number:str ,departure_airport_id:str):
        date = Root_class().date_time(raw=True)
        base_url = "https://www.flightview.com/flight-tracker/"
        return f"{base_url}UA/{flight_number}?date={date}&depapt={departure_airport_id[1:]}"


    def weather_links(self, dep_airport_id, dest_airport_id, ):
        # This is used for convinience. Consider separating it all out.
        # the functions awc_weather and datis within here is an attempt to reduce code duplication.
        # But that will potentially increate the amount of functions used in views.py/main.py
        # Consider all posibilites.
        
        return {
        "dep_awc_metar_api": f"https://aviationweather.gov/api/data/metar?ids={dep_airport_id}",
        "dep_awc_taf_api": f"https://aviationweather.gov/api/data/taf?ids={dep_airport_id}",
        "dep_datis_api":  f"https://datis.clowd.io/api/{dep_airport_id}",
        "dest_awc_metar_api": f"https://aviationweather.gov/api/data/metar?ids={dest_airport_id}",
        "dest_awc_taf_api": f"https://aviationweather.gov/api/data/taf?ids={dest_airport_id}",
        "dest_datis_api":  f"https://datis.clowd.io/api/{dest_airport_id}",
        }


    def awc_weather(self,metar_or_taf,airport_id):
        # Metar or taf takes in either "metar" or "taf" as required for fetching
        return f"https://aviationweather.gov/api/data/{metar_or_taf}?ids={airport_id}"


    def datis(self, airport_id):
        return f"https://datis.clowd.io/api/{airport_id}"





class Fetching_Mechanism(Root_class):
    # TODO:first rest should account for airline code and flight number, next init of this class needs dep_id
    def __init__(self,airline_code=None,flt_num=None,
                 dep_airport_id=None,dest_airport_id=None):
        super().__init__()
        
        # TODO: need to get rid of this. Search should find the appropriate flight number, w airline code, of all the flight numbers for that day
        if not airline_code:
            airline_code = 'UAL'

        # Flight Aware
        fa_apiKey = "G43B7Izssvrs8RYeLozyJj2uQyyH4lbU"         # New Key from Ismail
        fa_auth_header = {'x-apikey':fa_apiKey}
        fa_base_apiUrl = "https://aeroapi.flightaware.com/aeroapi/"
        fa_url = fa_base_apiUrl + f"flights/{airline_code}{flt_num}"
        self.fa_url_w_auth = {fa_url:fa_auth_header}
        # Old requests code: response = requests.get(url, headers=fa_auth_header) 

        # TODO: Fix airline code issue. This is not used yet. Find use case.
        # Aviation Stack api call. 3000 requests per month
        aviation_stack_url = 'http://api.aviationstack.com/v1/flights'
        aviation_stack_params = {
                            'access_key': '65dfac89c99477374011de39d27e290a',
                            'flight_icao': f"{airline_code}{flt_num}"}
        # aviationstack just like flight_aware
        self.av_stack_url_w_auth = {aviation_stack_url:aviation_stack_params}
        # Old requests code: api_result = requests.get(aviation_stack_url, self.aviation_stack_params)


    def requests_processing(self, 
                        requests_raw_extract: requests.models.Response,
                        json=None,
                        awc=None,
                        bs=None,
                        bs_flight_view=None,
                        ):
        if awc:
            
            awc_raw = requests_raw_extract        # Trying this asraw see if it works
            # awc_raw = requests_raw_extract.text
            # awc_raw = awc_raw.decode("utf-8")
            return awc_raw
        elif json:
            return requests_raw_extract.json()
        elif bs:
            # Might need to change this to requests_raw_extract.content depending on the use case.
            return bs4(requests_raw_extract,'html.parser')
        elif bs_flight_view:
            # Might need to change this to requests_raw_extract.content depending on the use case.
            return bs4(requests_raw_extract.content,'html.parser')


    def weather_links(self, dep_airport_id, dest_airport_id, ):
        
        return {
        "dep_awc_metar_api": f"https://aviationweather.gov/api/data/metar?ids={dep_airport_id}",
        "dep_awc_taf_api": f"https://aviationweather.gov/api/data/taf?ids={dep_airport_id}",
        "dep_datis_api":  f"https://datis.clowd.io/api/{dep_airport_id}",
        "dest_awc_metar_api": f"https://aviationweather.gov/api/data/metar?ids={dest_airport_id}",
        "dest_awc_taf_api": f"https://aviationweather.gov/api/data/taf?ids={dest_airport_id}",
        "dest_datis_api":  f"https://datis.clowd.io/api/{dest_airport_id}",
        }


    def jupyter_interactive_code(self,):

        """
        from dj.dj_app.root.root_class import Root_class, Fetching_Mechanism,Source_links_and_api
        from dj.dj_app.root.flight_deets_pre_processor import resp_initial_returns,resp_sec_returns,response_filter
        from dj.dj_app.root.dep_des import Pull_flight_info

        flight_number_query = 4595
        airline_code = 'UA'

        r = Root_class()
        fm = Fetching_Mechanism(flight_number_query)
        sl = Source_links_and_api()

        all_links = [
        sl.ua_dep_dest_flight_status(flight_number_query),
        sl.flight_stats_url(flight_number_query),
        sl.aviation_stack(airline_code, flight_number_query),
        # LIMIT THE USE FOR THIS FLIGHTAWARE DATA API. YOURE ONLY ALLOWED 1000 REQUESTS A MONTH
        # sl.flight_aware_w_auth(airline_code,flight_number_query),

        ]
        
        resp_dict:dict = await fm.async_pull(all_links)
        resp_initial = resp_initial_returns(resp_dict=resp_dict,airline_code='UA',flight_number_query=flight_number_query)
        fa_data = resp_initial[2]
        gate_returns = Pull_flight_info().flight_view_gate_info(flt_num=flight_number_query,airport=fa_data['origin'])


        
        
        task = asyncio.ensure_future(fm.async_pull(all_links))
        asyncio.gather(task)
        resp = await task       # This is the responsein jupyter that works 

        print(resp)

        # all_items = []
        # for url in all_links:
            # all_items.append(r.request(url))

        """
        pass


    async def async_pull(self, list_of_links:list):
        print('***** async_pull in progress...')
        async def get_tasks(session):
            tasks = []
            for url in list_of_links:
                # TODO: Aviation stack maybe possible here through the auth_headers. Previously auth headers were passed with api might have caused it to not work.
                            # Separate the auth and pass as a dict. 
                if type(url)==dict:         # This is probs for flight aware
                    url,auth_headers = list(url.keys())[0], list(url.values())[0]
                    tasks.append(asyncio.create_task(session.get(url, headers=auth_headers)))
                else:
                    tasks.append(asyncio.create_task(session.get(url)))
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

        print("*** async pull completion")
        #1 Temporary. Works when function calling within jupyter.
        return await main()         

        #2 works for jupyter when copy pasting this whole code within jupyter.
        # link_fetch = await asyncio.ensure_future(main())  
        
        #3 works for external cli use.
        # if __name__ == "__main__":        # if statement seems unnecessary: works when calling from cli, not when importing elsewhere
            # link_fetch = await asyncio.run(main())
            # return await link_fetch
        