import bs4
from .weather_parse import Weather_parse
from .dep_des import Pull_flight_info
import json
flt_info = Pull_flight_info()


def weather_html_injection(weather_raw):
    """ Figured its important to keep html interjection separatre for reusability."""
    wp = Weather_parse()            
    return wp.processed_weather(weather_raw=weather_raw)     # Doing this to avoid nested weather dictionaries
    

def raw_resp_weather_processing(resp_dict, airport_id, html_injection=False):
    metar,taf,datis = ['']*3

    for url,resp in resp_dict.items():
        if f"metar?ids={airport_id}" in str(url):
            metar = resp
        elif f"taf?ids={airport_id}" in str(url):
            taf = resp
        elif f"clowd.io/api/{airport_id}" in str(url):
            datis = json.loads(resp)     # Apparently this is being returned within a list is being fed as is. Accounted for.

    raw_weather_returns = {"datis":datis,"metar":metar,"taf":taf}
    # dep_weather = wp.processed_weather(weather_raw=dep_weather)
    
    if html_injection:
        return weather_html_injection(raw_weather_returns)
    else:
        wp = Weather_parse()
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