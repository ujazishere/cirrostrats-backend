import pickle
import pickle
from .weather_parse import WeatherParse
from .root_class import Root_class, Pull_class
from .dep_des import Pull_flight_info
import json
import json
flt_info = Pull_flight_info()


def resp_initial_returns(resp_dict: dict, airline_code, flight_number_query,):
    # see use of this function in view.py for document
    # see use of this function in view.py for document
    pc = Pull_class(flight_number_query)
    flight_aware_data = flt_info.fa_data_pull()
    flight_aware_data = flt_info.fa_data_pull()
    for url,resp in resp_dict.items():
        if "flight-status.com" in str(url):
            soup = pc.requests_processing(resp,bs=True)
            united_dep_dest = flt_info.united_departure_destination_scrape(pre_process=soup)
            # print(united_dep_dest)
        elif "flightstats.com" in str(url):
            soup = pc.requests_processing(resp,bs=True)
            flight_stats_arr_dep_time_zone = flt_info.fs_dep_arr_timezone_pull(flt_num_query=flight_number_query,pre_process=soup)
            # print(flight_stats_arr_dep_time_zone)


        elif "flightaware" in str(url):
            fa_return = json.loads(resp)
            fa_return = fa_return['flights']
            flight_aware_data = flt_info.fa_data_pull(airline_code=airline_code, flt_num=flight_number_query,pre_process=fa_return)
            fa_return = json.loads(resp)
            fa_return = fa_return['flights']
            flight_aware_data = flt_info.fa_data_pull(airline_code=airline_code, flt_num=flight_number_query,pre_process=fa_return)
            # print(flight_aware_data)
        elif "aviationstack" in str(url):       #TODO: aviation stack needs work
            pass
            # soup = pc.requests_processing(resp,json=True)
            # aviation_stack_data = flt_info.aviation_stack_pull(airline_code=airline_code, flt_num=flight_number_query)
        elif "aviationstack" in str(url):       #TODO: aviation stack needs work
            pass
            # soup = pc.requests_processing(resp,json=True)
            # aviation_stack_data = flt_info.aviation_stack_pull(airline_code=airline_code, flt_num=flight_number_query)
            # print(aviation_stack_data)
    

    return united_dep_dest, flight_stats_arr_dep_time_zone, flight_aware_data,
            #  aviation_stack_data


    return united_dep_dest, flight_stats_arr_dep_time_zone, flight_aware_data,
            #  aviation_stack_data


def resp_sec_returns(resp_dict,dep_airport_id,dest_airport_id):
    pc = Pull_class(dep_airport_id=dep_airport_id)



    gate_info = None        # Declared this here. in case if gate info is not scraped variable will atleast exist. used to avoid definition error
    dep_metar,nas_data,wpp = [None]*3            # Declaring for use in nas() in views.py
    for url,resp in resp_dict.items():
        if f"metar?ids={dep_airport_id}" in str(url):
            dep_metar = resp
        elif f"taf?ids={dep_airport_id}" in str(url):
            dep_taf = resp
        elif f"clowd.io/api/{dep_airport_id}" in str(url):          # TODO: Need to account for arrival dep vs arrival datis
            dep_datis = resp     # Apparently this is being returned within a list is being fed as is. Accounted for.
        elif f"metar?ids={dest_airport_id}" in str(url):
            dest_metar = resp
        elif f"taf?ids={dest_airport_id}" in str(url):
            dest_taf = resp
        elif f"clowd.io/api/{dest_airport_id}" in str(url):         # TODO: Need to account for arrival datis vs dep
            dest_datis = resp         # Apparently this is being returned within a list and is accounted for.


        elif f"flightview.com" in str(url):
            # Gate fetch
            # This is just for testing
            # fv_test = r"C:\Users\ujasv\OneDrive\Desktop\codes\Cirrostrats\dj\fv_test.pkl"
            # with open(fv_test, 'wb') as f:
            #     resp = pickle.dump(resp,f)
            # gate_info = pc.requests_processing(resp,bs=True)
            pass    # This is just not working. async return is way different than organic requests return.
            # Both are html but different data. Tried different likes, different soup type, bs4.prettify and still no joy!

            
        elif f"faa.gov/api/airport-status-information" in str(url):
            nas_data = resp
            nas_data = flt_info.nas_final_packet(dep_ID=dep_airport_id,dest_ID=dest_airport_id)

            nas_data = flt_info.nas_final_packet(dep_ID=dep_airport_id,dest_ID=dest_airport_id)

            
        else:
            pass

    # All of this should work when only getting weather. check and verify nas() in views.py works
    # Raw weather sent for preprocessing 
    
    
    if dep_metar:
        wp = WeatherParse()            

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
        print('no gate info found')
    


    if nas_data and gate_info_return and wpp:
        return {**wpp,**gate_info_return, **nas_data}       # The ** merges dicts in to a single dict
    elif nas_data:
        return nas_data
    elif wpp:
        return wpp






def response_filter(resp_dict:dict,*args,):
    pc = Pull_class()
    for url,resp in resp_dict.items():
        # if soup then this
        if "json" in args:
            data_return = json.loads(resp)
        elif "awc" in args:
            data_return = resp
        else:
            data_return = pc.requests_processing(resp,bs=True)
        # elif json then this dont need this I suppose. account for json processing within views. I guess.

        # elfi just raw response return then dont even need this
        # print(united_dep_dest)
    return data_return
