import logging
from core.root_class import Root_class
from typing import Literal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

ScrapeStatus = Literal['On time', 'Scheduled', 'Cancelled']

# TODO Cleanup: Take this extractor out of the api. Api is only for scrapes and api fetches.
class FlightStatsExtractor:
    def __init__(self):
        """ Given Soup through `ticket_card` this class extracts airport Code, city, airport name,
        scheduled time, estimated/actual time and terminal-gate and delay status."""
        # TODO: Jet blue code is B6 on flightstats use it for airline code.
    
    
    def delay_status(self,soup_fs) -> ScrapeStatus:
        """
        Extracts flight status (On time, Scheduled, Cancelled) from BeautifulSoup 
        element with robust error handling.
        
        Args:
            th_element: BeautifulSoup element containing flight status information
            
        Returns:
            single string one of three- On time, Scheduled, Cancelled
            or None if not found
        """
        th = soup_fs.select('[class*="ticket__Header"]')           # returns a list of classes that matches..
        try:
            th_element = th[0]
            # return self.extract_flight_status(th)
        except IndexError as e:
            logger.error(f'Delay status error in FlightStatsExtractor.tc,{e}')
            return None

        flight_status = None
        
        try:
            if not th_element:
                logger.warning("No TH element provided for status extraction")
                return None
                
            status_containers = th_element.select('[class*="StatusContainer"]')
            if not status_containers:
                logger.debug("No status containers found in TH element")
                return None
                
            for container in status_containers:
                for child in container.children:
                    try:
                        if not hasattr(child, 'text'):
                            continue  # Skip non-tag elements like '\n'
                            
                        status_text = child.get_text(strip=True)
                        if not status_text:
                            continue
                            
                        logger.debug(f"Found status text: {status_text}")
                        
                        if status_text != 'Arrived':
                            flight_status = status_text
                            logger.info(f"Extracted flight status: {flight_status}")
                            return flight_status  # Return first valid status found
                            
                    except Exception as child_error:
                        logger.warning(f"Error processing child element: {child_error}", exc_info=True)
                        continue
                        
        except Exception as e:
            logger.error(f"Unexpected error in flight status extraction: {e}", exc_info=True)
            
        return flight_status
    

    def ticket_card_extracts(self, tc:list):
        
        extracts = []
        for i in range(len(tc)):
            data = tc[i]
            # print(i)
            for i in data:
                # if "AirportCodeLabel" in i.get('class'):
                # extracts = {'cl':i.get('class')[0], 'data': i.text}           # include the class name of the the element
                
                # print(extracts['data'])
                extracts.append(i.text)
        self.ticket_extracts = extracts         # for troubleshooting access.
        returns = {}
        if len(extracts) < 13:
            print('Validation failed: not enough data extracted from the ticket card. Continuation would result in index error.')
            # Save soup, flight number, datetime, etca  log error. Investigate later.
            print('flight not found')
            logger.error('FlightStatsExtractor.tc_extracts: Not enough data extracted from the ticket card. required 13.')
            logger.error(f"Extracted data: {extracts}")
            return

        tc_code, tc_city, tc_airport_name = extracts[0], extracts[1], extracts[2]
        # TODO VHP Validate all these returns. trigger log if not valid.
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
            if terminal != "N/A" and gate != "N/A":
                returns.update({'TerminalGate': terminal + '-' + gate})
            elif gate == "N/A":
                returns.update({'TerminalGate': terminal})
            elif terminal == "N/A":
                returns.update({'TerminalGate': gate})
            # gate = extracts[12]
        return returns
               



    def ticket_card(self, soup_fs):

        delay_status = self.delay_status(soup_fs=soup_fs)
        Ticket_Card = soup_fs.select('[class*="TicketCard"]')           # returns a list of classes that matches..

        # # TODO: Can detect multiple flights using same flight number. but can only access new one. old one requires numeric flightid
        # multi_flight = soup_fs.select('[class*="past-upcoming-flights__TextHelper"]')           # returns a list of classes that matches..
        # for i in multi_flight:
        #     # print(i.get_text())
        #     # print(i.get('class'), i.get_text())
        #     pass
        
        if len(Ticket_Card) == 2:
            # if len of Ticket_card is 2 first one is dep second one is arrival
            departure = Ticket_Card[0]
            arrival = Ticket_Card[1]
        
            fs_departure_info_section = departure.select('[class*="InfoSection"]')           # returns a list of classes that matches..
            fs_arrival_info_section = arrival.select('[class*="InfoSection"]')           # returns a list of classes that matches..
        
            dep_extracts = self.ticket_card_extracts(fs_departure_info_section)
            arr_extracts = self.ticket_card_extracts(fs_arrival_info_section)
            return {'fsDeparture': dep_extracts, 'fsArrival': arr_extracts, 'fsDelayStatus': delay_status}
        elif len(Ticket_Card) != 2:
            # Save soup, flight number, datetime, etca  log error. Investigate later.
            print('flight not found')
            return 
    
    # VVI: There maybe multiple details of the flight belongiung to the same flight number.
    # tc(test_soups[0])


class FlightStatsScraper:
    def __init__(self):
        self.extractor = FlightStatsExtractor()


    def scrape(self,airline_code="UA", flt_num=None, departure_date:str=None, return_bs4=False):
        """ Returns clean scraped data or bs4 data if return_bs4 is True. Date format is YYYYMMDD.
        flt_num_query is numberic only."""
        rc=Root_class()

        date = departure_date if departure_date else rc.date_time(raw=True)     # Root_class inheritance format yyyymmdd
        base_url = "https://www.flightstats.com/v2/flight-tracker"
        flight_stats_url = f"{base_url}/{airline_code}/{flt_num}?year={date[:4]}&month={date[4:6]}&date={date[-2:]}"

        soup_fs = rc.request(flight_stats_url)
        self.soup = soup_fs

        return soup_fs if return_bs4 else self.extractor.ticket_card(soup_fs)