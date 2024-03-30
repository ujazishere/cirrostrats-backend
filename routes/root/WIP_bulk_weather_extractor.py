# from dj.dj_app.root.WIP_bulk_weather_extractor import Bulk_weather_extractor
import asyncio
import aiohttp
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import pickle
from bs4 import BeautifulSoup as bs4
import requests

# TODO: TAF is still remianing
# Extracts METARs and TAFs. Heavy pull with 2000+ airport ID and each airport pulls big chunk of data
# DONT USE THIS SCRIPT IF YOU DONT NEED TO. METAR_stack.pkl has the output for it
# Shorten the airport_ID list if you are to use it. Get rid of No_mets and no_tafs. Those consists of airports that return null vals.
# Dont exceed 500 workers. Better 350. It doesn't get much better after 500.


class Bulk_weather_extractor:
    def __init__(self, ) -> None:
        # list all files
        self.pickles_path = r"C:\Users\ujasv\OneDrive\Desktop\pickles"
        self.all_pickle_files = os.listdir(self.pickles_path)            # get all file names in pickles folder
        self.example_bulk_met_path = r"C:\Users\ujasv\OneDrive\Desktop\pickles\BULK_METAR_JAN_END_2024.pkl" 
        self.no_mets_path = r"C:\Users\ujasv\OneDrive\Desktop\pickles\no_mets.pkl"
        self.export_path = r"C:\Users\ujasv\OneDrive\Desktop\pickles"


    def loader(self,example_bulk_met_load=None, big_met_bulk_load=None,
                no_met_airports_load=None, taf_positive_airports=None):
        if  example_bulk_met_load:
            with open(self.example_bulk_met_path, 'rb') as f:
                w = pickle.load(f)
            print(f'file at {self.example_bulk_met_path} \n total metars: {len(w)}. first one: {w[0]}')
            return w
        
        elif big_met_bulk_load:
            self.metar_pickle_files = [i for i in self.all_pickle_files if 'METAR' in i]
            
            all_metar_bulk = []
            for i in self.metar_pickle_files:
                path = self.all_pickle_files+"\\"+ i
                with open(path, 'rb') as f:
                    all_metar_bulk += pickle.load(f)
            print(f'total metar files: {len(self.metar_pickle_files)}', f'total metars: {len(all_metar_bulk)}')
        
        elif no_met_airports_load:
            with open(self.no_mets_path,'rb') as f:
                no_mets = pickle.load(f)
                return no_mets
        
        elif taf_positive_airports:
            with open(r"C:\Users\ujasv\OneDrive\Desktop\pickles\taf_positive_airports.pkl", 'rb') as f:
                id = pickle.load(f)
                return id

        else:
            # 20,296 airport ID in list form. eg ['DAB', 'EWR', 'X50', 'AL44']
            # Load airport ID
            with open(r'dj/dj_app/root/pkl/airport_identifiers_US.pkl', 'rb') as f:
                id = pickle.load(f)
                return id
    

    def airport_ID_separator(self, ):
        new_id = []
        id = self.loader()  # Loads all airport id eg. ['DAB', 'EWR', 'X50', 'AL44']

        # Prepending K to 3 leter codes 
        for i in id:    # Using all airport ID's
            if len(i) == 3:
                prepend = 'K' + i
                new_id.append(prepend)
            else:
                new_id.append(i)
    
        # seperating id's that contain digit since those mostly dont have associated metars/TAFs
        x = set()
        for i in new_id:
            for char in i:
                if char.isdigit():
                    x.add(i)
        self.ids_with_digit = list(x)
        self.ids_without_digit = new_id      # declaring the variable
        for i in self.ids_with_digit:
            self.ids_without_digit.remove(i)

        # This I presume is used for parallel pulling
        # isalpha returns bool for string if the letters are all alphabets eg. EWR, MCO, MLB, etc.
            # and discards airports like 'X50' since its alphanumeric
        airport_ID = [i for i in id if len(i) ==3 and i.isalpha()]      # keeps id 
        print('alphabetic airport ID',len(airport_ID))
        
        no_mets = self.loader(no_met_airports_load=True)
        self.ids_without_digit_with_no_mets_excluded = [i for i in self.ids_without_digit if i not in no_mets]
        
        print(f'returning 3 item tuple, total id with/without/id_without_no_mets:')
        print(f'{len(self.ids_with_digit)}/{len(self.ids_without_digit)}/{len(self.ids_without_digit_with_no_mets_excluded)}')
        
        return self.ids_with_digit, self.ids_without_digit, self.ids_without_digit_with_no_mets_excluded
    

    # Important code. Seemed to take forever to build this to fix taf messed scrape returns
    def fix_taf(self, bulky_taf):
        fixed = []
        bt = bulky_taf
        for i in range(len(bt)):
            initial_two = bt[i][:2]
            trailing = bt[i][-1]
            if initial_two != '  ':      # main bod
                if trailing == ' ':      # last index empty: taf with forecast
                    new_line_break = bt[i][:-1] + '\n'
                elif trailing != ' ':    # main bod wo taf
                    fixed.append(bt[i])
            elif initial_two == '  ' and trailing == ' ':    # associated forecast that continues
                new_line_break += bt[i][:-1] + '\n'
            elif initial_two == '  ' and trailing != ' ':   # forecast ends
                new_line_break += bt[i]
                fixed.append(new_line_break)
        for i in fixed:
            print(i)
        return fixed


    def scraper(self, test=None, taf=None):
        
        def individual_scrape_returns(airport_id,taf=None):
            # Metar gives data upto 15 days ago and TAF gives upto 17 days ago
            if taf:
                awc_taf_api = f"https://aviationweather.gov/api/data/taf?ids={airport_id}&hours=408"
                weather_raw = requests.get(awc_taf_api)
            else:
                awc_metar_api = f"https://aviationweather.gov/api/data/metar?ids={airport_id}&hours=360"
                weather_raw = requests.get(awc_metar_api)
            
            weather_raw = weather_raw.content
            weather_raw = weather_raw.decode("utf-8")

            return weather_raw

        # This is without the concurrent futures threadpool executor. Inefficient but stable
        if taf:
            taf_bool = True
        else:
            taf_bool = False
        count = 0
        bulky_weather = []
        no_weather_id = []
        yes_weather_id = []
        # half_index = int(len(ids_without_digit)/2)     # use this to split pulls into two sections.
        id_without_digits_and_no_mets = self.airport_ID_separator()[2]
        for airport_id in id_without_digits_and_no_mets[:20]:
            count += 1
            weather_raw = individual_scrape_returns(airport_id=airport_id,taf=taf_bool)
            if not weather_raw:
                no_weather_id.append(airport_id)
                print('no_weather_id', airport_id, count)
            else:
                weather_in_list_form = weather_raw.split('\n')    # Delete this for TAF.
                for i_weather in weather_in_list_form:
                    if i_weather:         # since, there are empty metar lines.
                        bulky_weather.append(i_weather)
                yes_weather_id.append(airport_id)
            print(count)
            # use this to test how long it takes to pull and if the pull is even working.
            # Comment it out if you plan to use the whole thing.
            if test:
                if count >5:
                    print('Test done! no_weather_id/yes_weather_id: ', len(no_weather_id),'/', len(yes_weather_id))
                    break
        print('stored bulky_weather in self.bulky_weather')
        self.bulky_weather = bulky_weather
    

    async def parallel_scrape(self,taf_pull=None):
        async def get_tasks(session):
            # async def classification(session,ids_to_pull, type_of_weather, airport_id, time_in_hours):
            if taf_pull:
                ids_to_pull = self.loader(taf_positive_airports=True)
                type_of_weather,time_in_hours="taf","408"
            else:
                ids_to_pull = self.ids_without_digit_with_no_mets_excluded
                type_of_weather,time_in_hours="metar","360"

            tasks = []
            for airport_id in ids_to_pull:
                url = f"https://aviationweather.gov/api/data/{type_of_weather}?ids={airport_id}&hours={time_in_hours}"
                tasks.append(asyncio.create_task(session.get(url)))

            # if taf_pull:
            #     # url = f"https://aviationweather.gov/api/data/taf?ids={airport_id}&hours=408"
            #     ids_to_pull = self.loader(taf_positive_airports=True)
            # else:
            #     # url = f"https://aviationweather.gov/api/data/metar?ids={airport_id}&hours=360"
            #     ids_to_pull = self.ids_without_digit_with_no_mets_excluded
            print('total ID to pull: ', len(ids_to_pull))
            return tasks

        async def main():
            async with aiohttp.ClientSession() as session:
                tasks = await get_tasks(session)
                weather_resp = []
                done = []
                nd = []
                for task in asyncio.as_completed(tasks):
                    try:
                        resp = await task
                        
                        if resp.status == 200:
                            # resp_methods = ['charset', 'close', 'closed', 'connection', 'content', 'content_disposition', 'content_length', 'content_type', 'cookies', 'get_encoding', 'headers', 'history', 'host', 'json', 'links', 'method', 'ok', 'raise_for_status', 'raw_headers', 'read', 'real_url', 'reason', 'release', 'request_info', 'start', 'status', 'text', 'url', 'url_obj', 'version', 'wait_for_close']
                            jj = await resp.text()
                            if jj:
                                weather_resp.append(jj)
                                done.append(str(resp.url)[-14:-10])
                            else:
                                nd.append(str(resp.url)[-14:-10])
                        else:
                            nd.append(str(resp.url)[-14:-10])
                    except:
                        nd.append(str(resp.url)[-14:-10])
                self.nd, self.done = nd,done
                print("done/nd: ", done,nd)
                return weather_resp
        self.weather = await asyncio.ensure_future(main())
        print('saved raw bulky weather return to self.weather')
        
        if taf_pull:
            self.bulky_taf = self.weather
            line_break_fix = []
            for i in self.bulky_taf:
                ia = i.split('\n')
                if ia:
                    line_break_fix+=ia
            line_break_fix = [i for i in line_break_fix if i]
            self.bulky_taf = line_break_fix
            print('saved taf returns in self.bulky_taf')
            # weather_stacked = taf_fix(bulky_taf)
            # return fixed_taf
            pass
        else:
            bulk_metar = self.weather
            line_break_fix = []
            for i in bulk_metar:
                sp = i.split('\n')
                for y in sp:
                    line_break_fix.append(y)
            self.bulky_metar = line_break_fix
            print('Saved in self.bulky_metar')

            
    def hard_write_dumper(self,file_name, bulky_weather):
        currently = datetime.utcnow().strftime("%Y%m%d%H%M")
        # Double slash here because it causes syntax error regardless of r string above since `\` is used as escape char 
        file_name = self.export_path + "\\" + file_name + currently     
        with open(file_name, 'wb') as f:
            pickle.dump(bulky_weather, f)
        print('exported as:', file_name)
        
"""


we = Bulk_weather_extractor()
x = we.airport_ID_separator()
len(we.ids_without_digit_with_no_mets_excluded)

# Do the test first to init necessary items
metar_pull_test = we.scraper(test=True,)



# shows syntax error but works on jupyter. Pulls bulkt metar for last 15 days
async_pull_metar = await we.parallel_scrape()

# Automatically saves bulk_metar file name with current UTC YYYYMMDDHHMM 
we.hard_write_dumper("bulk_metar",we.bulky_metar)

# taf_pull_test = we.scraper(test=True,)
# Pulls taf for last 17 days
async_pull_taf = await we.parallel_scrape(taf_pull=True)

# Automatically saves bulk_taf file name with current UTC YYYYMMDDHHMM 
we.hard_write_dumper("bulk_taf",we.bulky_taf)



# we.hard_write_dumper(we.export_path,we.bulky_metar)


"""



"""

# This is the Unstable efficient version that pulls upto 8 indexes for whatever reason
airport_ID = ids_without_digit
met_taf = []        # This is essentially code_tag. Using a seperate variable to avoid clashes
with ThreadPoolExecutor(max_workers=500) as executor:
    # First argument in submit method is the function without parenthesis. VVI second is each airport ID
    futures = {executor.submit(code_tag, airport): airport for airport in airport_ID}
    # futures .key() is the memory location of the task and the .value() is the airport ID associated with it
    for future in as_completed(futures):
        # Again. future here as well is the memory location.
        airport_id_2 = futures[future]
        result = future.result()    # result is the output of the task of the memory location
        if result:
            cleaned = result.split('\n')
            if cleaned:
                for each_metar in cleaned:
                    met_taf.append(each_metar)


# for each in met_taf(which is essentially a code_tag), if the code_tag is exactly 2 items(one metar and other TAF)
    # then TAF is good if it is only 1 or less item then that item is most probably METAR)
    # This is done to avoid IndedxErrors Since not all airports report TAF.
TAF_stack = [str(list(i)[1].text) for i in met_taf if len(i) == 2]

"""