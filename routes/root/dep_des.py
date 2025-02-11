import requests
from bs4 import BeautifulSoup as bs4
from .root_class import Root_class
from .flight_aware_data_pull import flight_aware_data_pull
import xml.etree.ElementTree as ET
import re
import pickle

'''
This Script pulls the departure and destination when provided with the flight number.
'''

class Pull_flight_info(Root_class):

    def __init__(self) -> None:
        # Super method inherits the init method of the superclass. In this case`Root_class`.
        super().__init__()


    def fs_dep_arr_timezone_pull(self, flt_num_query=None, pre_process=None):
        if type(flt_num_query) == list:
            flt_num_query = flt_num_query[1]

        # flt_num = query.split()[1]
        flt_num = flt_num_query
        if pre_process:
            soup_fs = pre_process
        else:       
            # This is obsolete. will be removed. this is the old synchronous way to fetch data.
            # This only exists as a backup in case we have to return to synchronous if async doesn't work when deploying

            date = self.date_time(raw=True)     # Root_class inheritance format yyyymmdd
            
            #  TODO: pull information on flight numners from the info web and use that to pull info through flightview.
            # attempt to only pull departure and destination from the united from the info web.
            flight_stats_url = f"https://www.flightstats.com/v2/flight-tracker/UA/{flt_num}?year={date[:4]}&month={date[4:6]}&date={date[-2:]}"
            soup_fs = self.request(flight_stats_url)

        # fs_juice = soup_fs.select('[class*="TicketContainer"]')     # This is the whole packet not needed now
        
        # If there is a valid active flight its time zone will show up in TimeGroupContainer
        departure_time_zone,arrival_time_zone = [None]*2
        origin_fs,destination_fs = [None]*2
        Ticket_Card = soup_fs.select('[class*="TicketCard"]')           # returns a list of classes that matches..
        fs_time_zone = soup_fs.select('[class*="TimeGroupContainer"]')
        if fs_time_zone and Ticket_Card:
            origin_fs = Ticket_Card[0]
            origin_fs = "K"+origin_fs.select('[class*="Airport"]')[0].text
            destination_fs = Ticket_Card[1]
            destination_fs = "K"+destination_fs.select('[class*="Airport"]')[0].text
            
            departure_time_zone = fs_time_zone[0].get_text()        #  format is HH:MM XXX timezone(eg.EST)
            departure_time_zone = departure_time_zone[9:18]
            # departure_estimated_or_actual = departure_time_zone[18:]
            arrival_time_zone = fs_time_zone[1].get_text()
            arrival_time_zone = arrival_time_zone[9:18]
            # arrival_estimated_or_actual = arrival_time_zone[18:]
            print('dep_des.py fs_dep_arr_timezone_pull - SUCCESS at flightstats.com for scheduled_dep and arr local time stating what time zone it is.')
        else:
            print("no departure_arrival time zone found using flight_stats")

        # TODO: If this is unavailable, which has been the case latey- May 2024, use the other source for determining scheduled and actual departure and arriavl times
        bulk_flight_deet = {'flight_number': flt_num,            # This flt_num is probably misleading since the UA attached manually. Try pulling it from the flightstats web
                            'origin_fs':origin_fs,
                            'destination_fs':destination_fs,
                            'scheduled_departure_time': departure_time_zone,
                            'scheduled_arrival_time': arrival_time_zone,
                                            }
        return bulk_flight_deet

    def united_departure_destination_scrape(self,airline_code=None, flt_num=None,pre_process=None):
        departure_scheduled_time,destination_scheduled_time = [None]*2
        if not airline_code:
            airline_code = 'UA'
        if pre_process:
            soup = pre_process
        else:
            info = f"https://united-airlines.flight-status.info/{airline_code}-{flt_num}"               # This web probably contains incorrect information.
            soup = self.request(info)
        # Airport distance and duration can be misleading. Be careful with using these. 

        # table = soup.find('div', {'class': 'a2'})
        try: 
            # TODO: This is prone to throwing list index out of range errors. add if statement on airport_id befor processing departure_ID and destination_ID since airport_ID can be None.
            airport_id = soup.find_all('div', {'class': 'a2_ak'})
            airport_id = [i.text for i in airport_id if 'ICAO' in i.text]
            if airport_id:
                departure_ID = airport_id[0].split()[2]
                destination_ID = airport_id[1].split()[2]
                # TODO: WIP for getting scheduled times since the flight stats one is unreliable
                scheduled_times = soup.find_all('div', {'class': 'tb2'})
                scheduled_times = [i.text for i in scheduled_times]
                scheduled_times = [i for i in scheduled_times if 'Scheduled' in i]
                scheduled_times = [match.group() for i in scheduled_times if (match := re.search(r'\d\d:\d\d',i))]
                if scheduled_times: 
                    departure_scheduled_time = scheduled_times[0]
                    destination_scheduled_time = scheduled_times[1]
                print('dep_des.py united_departure_destination_scrape. Found scheduled times using flight_stats.')
        except Exception as e:
            departure_ID, destination_ID = [None]*2
            print('dep_des.py Unable united_departure_destination_scrape', e)
        print('dep_des.py united_departure_destination_scrape for departure and destination: ', departure_ID, destination_ID)
        return {'departure_ID': departure_ID,
                'destination_ID': destination_ID,
                'departure_scheduled_time': departure_scheduled_time,
                'destination_scheduled_time': destination_scheduled_time
                }


    def nas_final_packet(self,dep_ID, dest_ID=None):
        # TODO: airport closures remaining.
        departure_ID = dep_ID[1:]       # Stripping off the 'K' since NAS uses 3 letter airport ID
        destination_ID = dest_ID[1:]

        nas_delays = self.nas_pre_processing()          # Doing the scraping here
        airport_closures = nas_delays['Airport Closure']
        ground_stop_packet = nas_delays['ground_stop_packet']
        ground_delay_packet = nas_delays['ground_delay_packet']
        arr_dep_del_list = nas_delays['arr_dep_del_list']

        departure_affected = {}
        destination_affected = {}


        affected_ground_stop = []
        for i in airport_closures:
            if i[0] == 'ARPT':
                airport_identifier = i[1]
                affected_ground_stop.append(airport_identifier)
                if airport_identifier == departure_ID or airport_identifier == destination_ID:
                    airport_index = airport_closures.index(i)
                    reason = airport_closures[airport_index+1][1]
                    start = airport_closures[airport_index+2][1]
                    reopen = airport_closures[airport_index+3][1]
                    if airport_identifier == departure_ID:
                        departure_affected.update({'Airport Closure':{'Departure': airport_identifier,
                                                'Reason': reason,
                                                'Start': start,
                                                'Reopen': reopen}})
                    if airport_identifier == destination_ID:
                        destination_affected.update({'Airport Closure':{'Destination': airport_identifier,
                                                'Reason': reason,
                                                'Start': start,
                                                'Reopen': reopen}})

        affected_ground_delay_packet = []
        for i in ground_delay_packet:
            if i[0] == 'ARPT':
                airport_identifier = i[1]
                affected_ground_delay_packet.append(airport_identifier)
                if airport_identifier == departure_ID or airport_identifier == destination_ID:
                    airport_index = ground_delay_packet.index(i)
                    reason = ground_delay_packet[airport_index+1][1]
                    average_delay = ground_delay_packet[airport_index+2][1]
                    max_delay = ground_delay_packet[airport_index+3][1]
                    if airport_identifier == departure_ID:
                        departure_affected.update({'Ground Delay':{'Departure': airport_identifier,
                                                'Reason': reason,
                                                'Average Delay': average_delay,
                                                'Maximum Delay': max_delay}})
                    if airport_identifier == destination_ID:
                        destination_affected.update({'Ground Delay':{'Destination': airport_identifier,
                                                'Reason': reason,
                                                'Average Delay': average_delay,
                                                'Maximum Delay': max_delay}})

                                                
        affected_ground_stop_packet = []
        for i in ground_stop_packet:
            if i[0] == 'ARPT':
                airport_identifier = i[1]
                affected_ground_stop_packet.append(airport_identifier)
                if airport_identifier == departure_ID or airport_identifier == destination_ID:
                    airport_index = ground_stop_packet.index(i)
                    reason = ground_stop_packet[airport_index+1][1]
                    end_time = ground_stop_packet[airport_index+2][1]
                    if airport_identifier == departure_ID:
                        departure_affected.update({'Ground Stop':{'Departure': airport_identifier,
                                                'Reason': reason,
                                                'End Time': end_time}})
                    if airport_identifier == destination_ID:
                        destination_affected.update({'Ground Stop':{'Destination': airport_identifier,
                                                'Reason': reason,
                                                'End Time': end_time}})

        affected_arr_dep_del_list = []
        for i in arr_dep_del_list:
            if i[0] == 'ARPT':
                airport_identifier = i[1]
                affected_arr_dep_del_list.append(airport_identifier)
                if airport_identifier == departure_ID or airport_identifier == destination_ID:
                    airport_index = arr_dep_del_list.index(i)
                    reason = arr_dep_del_list[airport_index+1][1]
                    arr_or_dep = arr_dep_del_list[airport_index+2][1]
                    min_delay = arr_dep_del_list[airport_index+3][1]
                    max_delay = arr_dep_del_list[airport_index+4][1]
                    trend = arr_dep_del_list[airport_index+5][1]
                    if airport_identifier == departure_ID:
                        departure_affected.update({'Arrival/Departure Delay':{'Departure': airport_identifier,
                                                'Reason': reason,
                                                'Type': arr_or_dep['Type'],
                                                'Minimum': min_delay,
                                                'Maximum': max_delay,
                                                'Trend': trend}})
                    if airport_identifier == destination_ID:
                        destination_affected.update({'Arrival/Departure Delay':{'Destination': airport_identifier,
                                                'Reason': reason,
                                                'Type': arr_or_dep['Type'],
                                                'Minimum': min_delay,
                                                'Maximum': max_delay,
                                                'Trend': trend}})

        print('dep_des.py nas_final_packer. Providing NAS final packet dict.')
        return {'nas_departure_affected': departure_affected,
                'nas_destination_affected': destination_affected}


    def nas_fetch(self,):
        nas = "https://nasstatus.faa.gov/api/airport-status-information"
        response = requests.get(nas)
        xml_data = response.content
        return xml_data


    def nas_pre_processing(self):

        xml_data = self.nas_fetch()

        root = ET.fromstring(xml_data) 
        update_time = root[0].text

        affected_airports = [i.text for i in root.iter('ARPT')]
        affected_airports = list(set(affected_airports))
        affected_airports.sort()
        print('dep_des.py nas_pre_processing. NAS affected airports:', affected_airports)

        airport_closures = []
        closure = root.iter('Airport_Closure_List')
        for i in closure:
            for y in i:
                for x in y:
                    airport_closures.append([x.tag, x.text])

        ground_stop_packet = []
        count = 0
        for programs in root.iter('Program'):
            count += 1
            for each_program in programs:
                ground_stop_packet.append([each_program.tag, each_program.text])

        ground_delay_packet = []
        gd = root.iter('Ground_Delay')
        for i in gd:
            for y in i:
                ground_delay_packet.append([y.tag, y.text])

        arr_dep_del_list = []
        addl = root.iter('Arrival_Departure_Delay_List')
        for i in addl:
            for y in i:
                for x in y:
                    if x.tag == 'Arrival_Departure':
                        arr_dep_del_list.append([x.tag, x.attrib])
                    else:
                        arr_dep_del_list.append([x.tag, x.text])
                    for a in x:
                        arr_dep_del_list.append([a.tag, a.text])
        
        print('dep_des.py Done NAS pull through nas_packet_pull')
        return {'update_time': update_time,
                'affected_airports': affected_airports,
                'ground_stop_packet': ground_stop_packet, 
                'ground_delay_packet': ground_delay_packet,
                'arr_dep_del_list': arr_dep_del_list,
                'Airport Closure': airport_closures
                }


    def flight_view_gate_info(self, flt_num=None, airport=None, pre_process=None):             # not used yet. Plan on using it such that only reliable and useful information is pulled.

        # TODO: flight view can give reliable origin and destination info. Repo flights still dont show up tho. Use flightstats for repo flights. Use link below:
            #  https://www.flightview.com/flight-tracker/UA/4437
        # date format in the url is YYYYMMDD. For testing, you can find flt_nums on https://www.airport-ewr.com/newark-departures
        if pre_process:     # it doesn't feed in the pre-process if it cannt find the
            soup = pre_process

        else:            
            use_custom_dummy_data = False
            if use_custom_dummy_data:
                date = 20230505
            else:
                date = str(self.date_time(raw=True))     # Root_class inheritance format yyyymmdd
            print("dep_des.py flight_view_gate_info",flt_num,airport,date)
            try:        # the airport coming in initially wouldnt take airport as arg since it lacks the initial info, hence sec rep info will have this airport ID
                flight_view = f"https://www.flightview.com/flight-tracker/UA/{flt_num}?date={date}&depapt={airport[1:]}"
            except:
                pass
            print('dep_des.py flight_view_gate_info. Standard synchronoys fetch for gate info from:', flight_view)
            
            self.soup = self.request(flight_view)
            soup = self.soup
        try :
            leg_data = soup.find_all('div', class_='leg')   # Has all the departure and destination data
            departure_gate = leg_data[0].find_all('tr', class_='even')[1].text[17:]
            # departure_gate = departure_gate[26:-1]
            arrival_gate = leg_data[0].find_all('tr', class_='even')[4].text[17:]
            # arrival_gate = arrival_gate[26:-1]
            if 'Terminal' in departure_gate:
                departure_gate = departure_gate.replace('Terminal', '')
            if 'Terminal' in arrival_gate:
                arrival_gate = arrival_gate.replace('Terminal', '')

            scripts = soup.find_all('script')       # scripts is a section in the html that contains departure and destination airports 
            for script in scripts:
                # looks up text 'var sdepapt' which is associated with departure airport.
                    # then splits all lines into list form then just splits the departure and destination in string form (")
                # TODO: It is important to get airport names along with identifiers to seperate international flights for metar view.
                        # Since the whole of html is being supplied might as well get the city and state in.
                if 'var sdepapt' in script.get_text():
                    departure = script.get_text().split('\n')[1].split('\"')[1]
                    destination = script.get_text().split('\n')[2].split('\"')[1]
            # print(scripts[-3].get_text())       #this is where you can find departure and destination times
                    # departure_time = 
            # return dict({flt_num: [departure, destination]})
            
            if 'min' in departure_gate:      # This acocunts for faulty hrs and mins in string
                departure_gate = None
            if 'min' in arrival_gate:
                arrival_gate = None
            print('dep_des.py SUCCESS at pull_dep_des for gate info')
            return {'departure_gate': departure_gate,
                    'arrival_gate': arrival_gate,
                    }

        except Exception as e:
            empty_soup = {'departure_gate': 'None',
                          'arrival_gate': 'None'} 
            print('dep_des !!!UNSUCCESSFUL at flight_view_gate_info for gate info, Error:',e)
            return empty_soup

        # typically 9th index of scripts is where departure and destination is.
            # try print(scripts[9].get_text()) for string version for parsing
        
        # print(departure, destination)

    
    def fa_data_pull(self, airline_code=None,flt_num=None,pre_process=None):
        # """
        # This is just for testing
        # fa_test_path = r"C:\Users\ujasv\OneDrive\Desktop\codes\Cirrostrats\dj\fa_test.pkl"
        # with open(fa_test_path, 'rb') as f:
            # resp = pickle.load(f)
            # fa_resp = json.loads(resp)
        # resp_dict.update({'https://aeroapi.flightaware.com/aeroapi/flights/UAL4433':fa_resp})
        # """
        fa_returns = flight_aware_data_pull(airline_code=airline_code, flt_num=flt_num, pre_process=pre_process)
        return fa_returns


    def aviation_stack_pull(self,):
        return None


"""
# for use in jupyter
from dep_des import Pull_flight_info

# united scrape mechanism
flt_info = Pull_flight_info()
scrape_all = flt_info.united_departure_destination_scrape(flt_num="4184")

"""