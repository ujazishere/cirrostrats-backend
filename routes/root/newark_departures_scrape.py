from .root_class import Root_class

# TODO: Scrape all essential information from airport-ewr.com web so that excessive pull on pick_flight_data
# TODO: raw_bs4_html_ele contains delay info. Get delayed flight numbers
            
class Newark_departures_scrape(Root_class):
    
    def __init__(self) -> None:
            pass


    def all_newark_departures(self):

        #  This code pulls out all the flight numbers departing out of EWR
        
        print('working on united departures out of Newark')
        day_times = {'very_early_morn': '?tp=0',
                     'morning': '?tp6',
                     'noon': '?tp=12',
                     'evening': '?tp=18',
                         }                                

        all_day_EWR_departures = []
        for time_of_the_day, associated_code in day_times.items():
            EWR_deps_url = f'https://www.airport-ewr.com/newark-departures{associated_code}'

            soup = self.request(EWR_deps_url)
            raw_bs4_all_EWR_deps = soup.find_all('div', class_="flight-col flight-col__flight")[1:]
            # raw_bs4_html_ele = soup.find_all('div', class_="flight-row")[1:]

            for index in range(len(raw_bs4_all_EWR_deps)):
                for i in raw_bs4_all_EWR_deps[index]:
                    if i != '\n':
                        all_day_EWR_departures.append(i.text)
        
        return all_day_EWR_departures


    def united_departures(self):
        # returns list of all united flights as UA**** each
        # Here we extract raw united flight number departures from airport-ewr.com
        
        all_EWR_deps = self.all_newark_departures()
        # extracting all united flights and putting them all in list to return it in the function.
        united_departures_newark = [each for each in all_EWR_deps if 'UA' in each]
        
        # TODO: Log these on a file and setup a scheduler to send email notifications.
        print('Successfully pulled United departures out of Newark at', self.date_time())
        print(f'Total United departures: {len(united_departures_newark)}')
        
        return united_departures_newark
