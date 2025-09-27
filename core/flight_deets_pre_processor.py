import bs4
from .weather_parse import Weather_parse
from .dep_des import Pull_flight_info
import json


flt_info = Pull_flight_info()

def resp_splitter(airport_code, resp_dict):
    metar,taf,datis = ['']*3

    for url,resp in resp_dict.items():
        if f"metar?ids={airport_code}" in str(url):
            metar = resp
        elif f"taf?ids={airport_code}" in str(url):
            taf = resp
        elif f"clowd.io/api/{airport_code}" in str(url):
            datis = json.loads(resp)     # Apparently this is being returned within a list is being fed as is. Accounted for.
    return metar,taf,datis

def raw_resp_weather_processing(resp_dict, airport_id, html_injection=False):
    metar,taf,datis = resp_splitter(airport_id, resp_dict)
    raw_weather_returns = {"datis":datis,"metar":metar,"taf":taf}
    # dep_weather = wp.html_injected_weather(weather_raw=dep_weather)
    
    wp = Weather_parse()            
    if html_injection:
        return wp.html_injected_weather(weather_raw=raw_weather_returns)     # Doing this to avoid nested weather dictionaries
    else:
        datis_raw = wp.datis_processing(datis_raw=raw_weather_returns.get('datis','N/A'))
        raw_weather_returns['datis'] = datis_raw
        return raw_weather_returns

    
def response_filter(resp_dict:dict,*args,):
    """ converts response to appropriate format given either json bs4 or beautiful soup"""

    for url,resp in resp_dict.items():
        # if soup then this
        if "json" in args:
            return json.loads(resp)
        elif "awc" in args:
            return resp
        elif "bs4":
            return bs4(resp,'html.parser')