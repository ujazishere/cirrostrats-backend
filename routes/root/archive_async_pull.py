import asyncio, aiohttp
# from dj.dj_app.root.root_class import Root_class
import requests
from .root_class import Root_class

class pull_stack:
    def __init__(self, ) -> None:
        pass

    def weather(self, ):
        pass

    def nas(self, ):
        pass

    def flight_aware(self, ):
        pass

class async_pull:
    def __init__(self) -> None:
        self.date = Root_class().date_time(raw=True)     # Root_class format yyyymmdd. Targetted call instead of expensive inheritance.

    def creating_tasks(self, session,url):
        asyncio.create_task(session.get(url))


    def pulling(self, flt_num, query):

        async def get_tasks(session):
            tasks = []
            # dep_des.py fs_dep_arr timezone pull through dep_des.py
            # bulk_flight_deets.update(flt_info.fs_dep_arr_timezone_pull(flight_number_query))
            fs_base_url = "https://www.flightstats.com/v2/flight-tracker/UA/"
            flight_stats_url = fs_base_url + f"{flt_num}?year={date[:4]}&month={date[4:6]}&date={date[-2:]}"
            tasks.append(asyncio.create_task(session.get(fs_base_url)))
            
            # fa_data_pull
            # bulk_flight_deets.update(flt_info.fa_data_pull(airline_code,flight_number_query))
            apiKey = "G43B7Izssvrs8RYeLozyJj2uQyyH4lbU"         # New Key from Ismail
            apiUrl = "https://aeroapi.flightaware.com/aeroapi/"
            auth_header = {'x-apikey':apiKey}
            if not airline_code:
                airline_code = 'UAL'
                url = apiUrl + f"flights/{airline_code}{query}"
                # response = requests.get(url, headers=auth_header) 
                tasks.append(asyncio.create_task(session.get(url,headers=auth_header)))

            # United departure and destination scrape
            # bulk_flight_deets.update(flt_info.united_departure_destination_scrape(flight_number_query))
            ua_info_url = f"https://united-airlines.flight-status.info/ua-{flt_num}"               # This web probably contains incorrect information.
            # soup = self.request(info)
            tasks.append(asyncio.create_task(session.get(ua_info_url)))

            # Departure and destination weather
            bulk_flight_deets['dep_weather'] = weather.processed_weather(UA_departure_ID)
            airport_id = query
            awc_metar_api = f"https://aviationweather.gov/api/data/metar?ids={airport_id}"
            metar_raw = requests.get(awc_metar_api)
            metar_raw = metar_raw.content
            metar_raw = metar_raw.decode("utf-8")
            awc_taf_api = f"https://aviationweather.gov/api/data/taf?ids={airport_id}"
            taf_raw = requests.get(awc_taf_api)
            taf_raw = taf_raw.content
            taf_raw = taf_raw.decode("utf-8")
            datis_api =  f"https://datis.clowd.io/api/{airport_id}"
            datis = requests.get(datis_api)
            datis = json.loads(datis.content.decode('utf-8'))
            datis_raw = 'N/A'
            tasks.append(asyncio.create_task(session.get(awc_metar_api)))
            tasks.append(asyncio.create_task(session.get(awc_taf_api)))
            tasks.append(asyncio.create_task(session.get(datis_api)))

            # nas packet pull dep_des.py file
            bulk_flight_deets.update(flt_info.nas_final_packet(UA_departure_ID, UA_destination_ID))
            nas = "https://nasstatus.faa.gov/api/airport-status-information"
            response = requests.get(nas)
            xml_data = response.content
            
            # flightview gate pull

            bulk_flight_deets.update(flt_info.flight_view_gate_info(flight_number_query, UA_departure_ID))
            date = str(self.date_time(raw=True))     # Root_class inheritance format yyyymmdd
            flight_view = f"https://www.flightview.com/flight-tracker/UA/{flt_num}?date={date}&depapt={airport[1:]}"






    

            self.creating_tasks(session,url)
            for airport_id in all_datis_airports:
                url = f"https://datis.clowd.io/api/{airport_id}"
                tasks.append(asyncio.create_task(session.get(url)))
            return tasks

        async def main():
            async with aiohttp.ClientSession() as session:
                tasks = await get_tasks(session)
                # Upto here the tasks are created which is very light.

                # Actual pull work is done using as_completed 
                datis_resp = []
                for task in asyncio.as_completed(tasks):        # use .gather() instead of .as_completed for background completion
                    resp = await task 
                    jj = await resp.json()
                    datis_raw = 'n/a'
                    if type(jj) == list and 'datis' in jj[0].keys():
                        datis_raw = jj[0]['datis']
                    datis_resp.append(datis_raw)
                return datis_resp

        # Works regardless of the syntax error. Not sut why its showing syntax error
        all_76_datis = await asyncio.ensure_future(main())

