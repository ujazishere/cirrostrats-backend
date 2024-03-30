import requests
from bs4 import BeautifulSoup as bs4

# This is a prototype. Trying to move the departures EWR UA into its own file.

class Req:
    def __init__(self) -> None:
        pass

    def request(self, url):
        response = requests.get(url)
        return bs4(response.content, 'html.parser')


def departures_EWR_UA():
    # returns list of all united flights as UA**** each
    # Here we extract raw united flight number departures from airport-ewr.com
    
    evening = '?tp=6'
    # evening = ''
    EWR_deps_url = f'https://www.airport-ewr.com/newark-departures{evening}'
    
    soup = Req.request(EWR_deps_url)
    raw_bs4_all_EWR_deps = soup.find_all('div', class_="flight-col flight-col__flight")[1:]
    # TODO: raw_bs4_html_ele contains delay info. Get delayed flight numbers
    # raw_bs4_html_ele = soup.find_all('div', class_="flight-row")[1:]

    #  This code pulls out all the flight numbers departing out of EWR
    all_EWR_deps = []
    for index in range(len(raw_bs4_all_EWR_deps)):
        for i in raw_bs4_all_EWR_deps[index]:
            if i != '\n':
                all_EWR_deps.append(i.text)


    # extracting all united flights and putting them all in list to return it in the function.
    united_flights =[each for each in all_EWR_deps if 'UA' in each]
    print(f'total flights {len(all_EWR_deps)} of which UA flights: {len(united_flights)}')
    return united_flights