from routes.root.weather_parse import Weather_parse
from routes.root.dep_des import Pull_flight_info

# Fetching raw data from raw functions from the backend.
wp = Weather_parse()
flt_info = Pull_flight_info()

a = wp.processed_weather('KEWR')
b = flt_info.flight_view_gate_info('4433','KEWR')
c = flt_info.flightstats_dep_arr_timezone_pull('4433')
d = flt_info.nas_final_packet('KLAS','KEWR')



# shows how the data is structured in the mdb collections.
from routes.root.root_class import Root_class, Fetching_Mechanism, Root_source_links, Source_links_and_api
sl = Source_links_and_api()

flight_number_query = '4433'
# sl.ua_dep_dest_flight_status(flight_number_query)
# sl.flight_stats_url(flight_number_query),

from routes.root.root_class import Root_class, Fetching_Mechanism, Root_source_links, Source_links_and_api


# departures and destinations from particular airports. Need another source for redundancy.
# The other one probs can be flightView.com
import requests
from bs4 import BeautifulSoup as bs4
fv_link = 'https://www.flightview.com/airport/ORD-Chicago-IL-(O_Hare)/departures'
airport_code,year,month,date,hour = 'EWR','2024','11','21','0'
fs_link = f'https://www.flightstats.com/v2/flight-tracker/departures/{airport_code}/?year={year}&month={month}&date={date}&hour={hour}'
response = requests.get(fs_link)
soup_fs = bs4(response.content, 'html.parser')
all_text = soup_fs.get_text()

text_to_search = 'American Airlines'
all_div = soup_fs.find_all('div')
for each_div in all_div:
    each_text = each_div.get_text()
    # We also limit the text size so the blown up or too little texts are avoided
    if text_to_search in each_text and len(each_text) < 100 and len(each_text) > 4: 
        print(each_div)
        print(each_text)

all_items = soup_fs.select('[class*="table__TableRowWrapper"]')
