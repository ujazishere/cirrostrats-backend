from .weather_parse import Weather_parse
from .root_class import Root_class, Fetching_Mechanism
from .flight_aware_data_pull import Flight_aware_pull as null_flightaware_return
from .dep_des import Pull_flight_info
import json
flt_info = Pull_flight_info()


def resp_initial_returns(resp_dict: dict, airline_code, flight_number_query,):
    # response from the async pull is fed here for cleaning. This function will split all the associated data and return it back to the views.py flight_deet function
    fm = Fetching_Mechanism(flight_number_query)
    flight_aware_data = null_flightaware_return().attrs     # This is to declare empty values for keys in flightaware i.e fa_object.attrs
    united_dep_dest,flight_stats_arr_dep_time_zone = [None]*2       # declaring so it doesn't throw error
    for url,resp in resp_dict.items():
        if "flight-status.com" in str(url):
            print("11.resp_intitial_return flight-status")
            soup = fm.requests_processing(resp,bs=True)
            print("11Sending raw data to unuted_departure_destination_scrape for cleaning")
            united_dep_dest = flt_info.united_departure_destination_scrape(pre_process=soup)
            if not united_dep_dest:
                united_dep_dest = None
            print("11.united_dep_dest",united_dep_dest)
        elif "flightstats.com" in str(url):
            print("22.resp_intitial_return flightstats.com")
            soup = fm.requests_processing(resp,bs=True)
            print("22Sending raw data to fs_dep_arr_timezone_pull for timezone data cleaning")
            flight_stats_arr_dep_time_zone = flt_info.fs_dep_arr_timezone_pull(flt_num_query=flight_number_query,pre_process=soup)
            # print(flight_stats_arr_dep_time_zone)


        elif "flightaware" in str(url):
            print("33.resp_intitial_return flightaware")
            fa_return = json.loads(resp)
            fa_return = fa_return['flights']
            print("33Sending data to fa_data_pull for cleaning.")
            flight_aware_data = flt_info.fa_data_pull(airline_code=airline_code, flt_num=flight_number_query,pre_process=fa_return)
        elif "aviationstack" in str(url):       #TODO: aviation stack needs work. That is another source to cross-check with flightaware and others. Design the logic to cross-check and verify.
            print("resp_intitial_return aviationstack:", resp)
            av_stack = json.loads(resp)
            # soup = fm.requests_processing(resp,json=True)
            # aviation_stack_data = flt_info.aviation_stack_pull(airline_code=airline_code, flt_num=flight_number_query)
    

    return united_dep_dest, flight_stats_arr_dep_time_zone, flight_aware_data,
            #  aviation_stack_data


def raw_resp_weather_processing(resp_dict, airport_id):
    metar,taf,datis = ['']*3

    for url,resp in resp_dict.items():
        if f"metar?ids={airport_id}" in str(url):
            metar = resp
        elif f"taf?ids={airport_id}" in str(url):
            taf = resp
        elif f"clowd.io/api/{airport_id}" in str(url):          # TODO: Need to account for arrival dep vs arrival datis. Its not been working for Philly
            datis = json.loads(resp)     # Apparently this is being returned within a list is being fed as is. Accounted for.

    raw_weather_returns = {"datis":datis,"metar":metar,"taf":taf}
    # dep_weather = wp.processed_weather(weather_raw=dep_weather)
    
    wp = Weather_parse()            
    wpp = wp.processed_weather(weather_raw=raw_weather_returns)     # Doing this to avoid nested weather dictionaries
    return wpp

    
def resp_sec_returns(resp_dict,dep_airport_id,dest_airport_id):
    gate_info = None        # Declared this here. in case if gate info is not scraped variable will atleast exist. used to avoid definition error
    dep_metar,nas_data,wpp = [None]*3            # Declaring for use in nas() in views.py
    for url,resp in resp_dict.items():
        if f"metar?ids={dep_airport_id}" in str(url):
            dep_metar = resp
        elif f"taf?ids={dep_airport_id}" in str(url):
            dep_taf = resp
        elif f"clowd.io/api/{dep_airport_id}" in str(url):          # TODO: Need to account for arrival dep vs arrival datis. Its not been working for Philly
            dep_datis = json.loads(resp)     # Apparently this is being returned within a list is being fed as is. Accounted for.
        elif f"metar?ids={dest_airport_id}" in str(url):
            dest_metar = resp
        elif f"taf?ids={dest_airport_id}" in str(url):
            dest_taf = resp
        elif f"clowd.io/api/{dest_airport_id}" in str(url):         # TODO: Need to account for arrival dep vs arrival datis. Its not been working for Philly
            dest_datis = json.loads(resp)         # Apparently this is being returned within a list and is accounted for.


        elif f"flightview.com" in str(url):
            # Gate fetch
            # This is just for testing
            # fv_test = r"C:\Users\ujasv\OneDrive\Desktop\codes\Cirrostrats\dj\fv_test.pkl"
            # with open(fv_test, 'wb') as f:
            #     resp = pickle.dump(resp,f)
            # gate_info = fm.requests_processing(resp,bs=True)
            pass    # This is just not working. async return is way different than organic requests return.
            # Both are html but different data. Tried different likes, different soup type, bs4.prettify and still no joy! Move on find another way.

            
        elif f"faa.gov/api/airport-status-information" in str(url):
            nas_data = resp
            nas_data = flt_info.nas_final_packet(dep_ID=dep_airport_id,dest_ID=dest_airport_id)

            
        else:
            pass

    
    
    if dep_metar:
        # Raw weather sent for preprocessing 
        wp = Weather_parse()            

        dep_weather = {"datis":dep_datis,"metar":dep_metar,"taf":dep_taf}
        dep_weather = wp.processed_weather(weather_raw=dep_weather)
        
        dest_weather = {"datis":dest_datis,"metar":dest_metar,"taf":dest_taf}
        dest_weather = wp.processed_weather(weather_raw=dest_weather)

        wpp = {"dep_weather":dep_weather,"dest_weather":dest_weather}

        wpp = wp.nested_weather_dict_explosion(wpp)     # Doing this to avoid nested weather dictionaries


    if gate_info:
        gate_info_return = flt_info.flight_view_gate_info(pre_process=gate_info)
        print(gate_info_return)
    else:
        gate_info_return = {'departure_gate': None,
                            'arrival_gate': None, }
        print('resp_sec_returns: no gate info found')
    

    if nas_data and gate_info_return and wpp:
        return {**wpp,**gate_info_return, **nas_data}       # The ** merges dicts in to a single dict
    elif nas_data:
        return nas_data
    elif wpp:
        return wpp


def response_filter(resp_dict:dict,*args,):
    fm = Fetching_Mechanism()
    for url,resp in resp_dict.items():
        # if soup then this
        if "json" in args:
            data_return = json.loads(resp)
        elif "awc" in args:
            data_return = resp
        else:
            data_return = fm.requests_processing(resp,bs=True)
        # elif json then this dont need this I suppose. account for json processing within views. I guess.

        # elfi just raw response return then dont even need this
        # print(united_dep_dest)
    return data_return
