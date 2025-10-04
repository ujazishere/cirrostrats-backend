import bs4
import json

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