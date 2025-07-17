from routes.root.root_class import Root_class
class FlightStatsExtractor:
    def __init__(self):
        """ Given Soup through `tc` this class extracts airport Code, city, airport name,
        scheduled time, estimated/actual time and terminal-gate."""
        pass


    def tc_extracts(self, tc:list):
        
        extracts = []
        for i in range(len(tc)):
            data = tc[i]
            # print(i)
            for i in data:
                # if "AirportCodeLabel" in i.get('class'):
                # extracts = {'cl':i.get('class')[0], 'data': i.text}           # include the class name of the the element
                
                # print(extracts['data'])
                extracts.append(i.text)
    
        returns = {}
        if len(extracts) < 13:
            print('Validation failed: not enough data extracted from the ticket card. Continuation would result in index error.')
            # Save soup, flight number, datetime, etca  log error. Investigate later.
            print('flight not found')
            return
        tc_code, tc_city, tc_airport_name = extracts[0], extracts[1], extracts[2]
        returns.update({'Code': tc_code, 'City': tc_city, 'AirportName': tc_airport_name})
        if extracts[3] == "Flight Departure Times" or extracts[3] == "Flight Arrival Times":
            returns.update({'ScheduledDate': extracts[4]})  # This is the title of the section, either departure or arrival
        if extracts[5] == "Scheduled":
            returns.update({'ScheduledTime': extracts[6]})
        if extracts[7] == "Estimated" or extracts[7] == "Actual":
            # TODO: Actual time does not have a date associated wit it what if its delayed over a day?
            returns.update({extracts[7]+'Time': extracts[8]})
            # times_title, times_value = extracts[7], extracts[8]
        
        if extracts[9] == "Terminal":
            terminal = extracts[10]
            # terminal = extracts[10]
        if extracts[11] == "Gate":
            gate = extracts[12]
        if terminal and gate:
            returns.update({'TerminalGate': terminal + '-' + gate})
            # gate = extracts[12]
        return returns
               
    
    def tc(self, soup_fs):
        Ticket_Card = soup_fs.select('[class*="TicketCard"]')           # returns a list of classes that matches..
        multi_flight = soup_fs.select('[class*="past-upcoming-flights__TextHelper"]')           # returns a list of classes that matches..
        for i in multi_flight:
            # TODO: Can detect multiple flights using same flight number. but can only access new one. old one requires numeric flightid
            # print(i.get_text())
            # print(i.get('class'), i.get_text())
            pass
        # for i in pf:
            # print(i.get_text())
        # if len of Ticket_card is 2 first one is dep second one is arrival
        if len(Ticket_Card) == 2:
            departure = Ticket_Card[0]
            arrival = Ticket_Card[1]
        
            fs_departure_info_section = departure.select('[class*="InfoSection"]')           # returns a list of classes that matches..
            fs_arrival_info_section = arrival.select('[class*="InfoSection"]')           # returns a list of classes that matches..
        
            dep_extracts = self.tc_extracts(fs_departure_info_section)
            arr_extracts = self.tc_extracts(fs_arrival_info_section)
            return {'fsDeparture': dep_extracts, 'fsArrival': arr_extracts}
        elif len(Ticket_Card) != 2:
            # Save soup, flight number, datetime, etca  log error. Investigate later.
            print('flight not found')
            return 
    
    # VVI: There maybe multiple details of the flight belongiung to the same flight number.
    # tc(test_soups[0])


class FlightStatsScraper:
    def __init__(self):
        self.extractor = FlightStatsExtractor()


    def scrape(self,airline_code="UA", flt_num_query=None, departure_date:str=None, return_bs4=False):
        """ Returns clean scraped data or bs4 data if return_bs4 is True. Date format is YYYYMMDD.
        flt_num_query is numberic only."""
        rc=Root_class()

        flt_num = flt_num_query
        date = departure_date if departure_date else rc.date_time(raw=True)     # Root_class inheritance format yyyymmdd
        base_url = "https://www.flightstats.com/v2/flight-tracker"
        flight_stats_url = f"{base_url}/{airline_code}/{flt_num}?year={date[:4]}&month={date[4:6]}&date={date[-2:]}"

        soup_fs = rc.request(flight_stats_url)

        return soup_fs if return_bs4 else self.extractor.tc(soup_fs)