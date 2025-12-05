from core.api.source_links_and_api import Source_links_and_api
from core.root_class import Root_class
from datetime import datetime
import logging
from typing import Literal

from core.search.query_classifier import QueryClassifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

ScrapeStatus = Literal['On time', 'Scheduled', 'Cancelled']

class FlightStatsExtractor:
    def __init__(self):
        """Extractor for core flight details from a FlightStats `ticket_card`.

        Given a BeautifulSoup document (provided via `ticket_card` / `ticket_card_extracts`),
        this class is responsible purely for parsing and extracting:

        - **Airport metadata**: code, city, airport name.
        - **Timing data**: scheduled time, estimated/actual time.
        - **Facility info**: terminal / gate and combined terminal-gate string.
        - **Delay status**: status such as "On time", "Scheduled", "Cancelled".
        # TODO flightStats: This may not be working checkout models.py for validation of this status

        Network access is handled elsewhere (see `FlightStatsScraper`); this class
        should remain focused on HTML parsing.
        """
        # TODO: Jet blue code is B6 on flightstats use it for airline code.
    
    
    def delay_status(self,soup_fs) -> ScrapeStatus:
        """Extract the delay / status label from the FlightStats header.

        The status is read from the ticket header section and is expected to be one of
        ``"On time"``, ``"Scheduled"`` or ``"Cancelled"``. If the HTML structure is
        not as expected, the method logs the issue and returns ``None``.

        Args:
            th_element: BeautifulSoup element containing flight status information
            
        Returns:
            A string status (e.g. ``"On time"``, ``"Scheduled"``, ``"Cancelled"``)
            or ``None`` if the status cannot be found or parsed.
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
        """Parse the raw ticket‑card info sections into a structured mapping.

        This is the original, position‑based extractor which expects a very specific
        ordering of text nodes in the FlightStats ticket card and will log an error
        if fewer than 13 data elements are present.

        Args:
            tc: List of BeautifulSoup containers that represent the ticket card
                "InfoSection" blocks (typically for departure or arrival).

        Returns:
            A dictionary with keys such as ``"Code"``, ``"City"``, ``"AirportName"``,
            ``"ScheduledDate"``, ``"ScheduledTime"``, and terminal/gate information
            under ``"TerminalGate"``, or ``None`` if validation fails.
        """
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
               

    def multi_flight_comparison(self, dep_extracts, multiple_flights_soup_extracts):
        
        multi_date_format = '%A, %d-%b-%Y'
        solo_date_format = '%d-%b-%Y'
        
        departure_date = datetime.strptime(dep_extracts['ScheduledDate'], solo_date_format)
        
        multi_extracts = []
        for each_multi in multiple_flights_soup_extracts:
            each_date = datetime.strptime(each_multi['date'], multi_date_format)
            if each_date== departure_date:
                multi_extracts.append(each_multi)
                # print(each_date,departure_date)
        if len(multi_extracts) >1:
            return multi_extracts


    def multi_flight_extracts(self, soup):
        """ Extracts multiple flights based on dates """
        multi_flight = soup.select('[class*="past-upcoming-flights__TextHelper"]')
        flights_data = []
        current_date = None
        current_flight = []
        
        for element in multi_flight:
            classes = element.get('class', [])
            text = element.get_text(strip=True)
            
            if 'bTIClP' in classes and text.startswith('Flights for'):
                current_date = text.replace('Flights for ', '')
                continue
            
            if 'HeaderText' in ' '.join(classes):
                continue
            
            if current_date:
                if 'cUykul' in classes or 'cjETuy' in classes or 'diRMZq' in classes:
                    current_flight.append(text)
                    
                    # When we have 6 items (dep_time, origin, origin_name, dest, dest_name, arr_time)
                    if len(current_flight) == 6:
                        flights_data.append({
                            'date': current_date,
                            'departure_time': current_flight[0],
                            'origin': current_flight[1],
                            'origin_name': current_flight[2],
                            'destination': current_flight[3],
                            'destination_name': current_flight[4],
                            'arrival_time': current_flight[5]
                        })
                        current_flight = []
        return flights_data


    def ticket_card(self, soup_fs):
        """Return parsed departure/arrival ticket‑card details and delay status.

        This method locates the two FlightStats ticket cards on the page
        (departure and arrival), extracts their `InfoSection` blocks and passes them
        to `ticket_card_extracts`. It also attaches the overall delay status from
        `delay_status`.

        Args:
            soup_fs: Root BeautifulSoup document for the FlightStats page.

        Returns:
            A dictionary of the form:
                ``{"fsDeparture": {...}, "fsArrival": {...}, "fsDelayStatus": <str|None>}``
            or ``None`` if the expected ticket card structure is not found.
        """

        delay_status = self.delay_status(soup_fs=soup_fs)
        Ticket_Card = soup_fs.select('[class*="TicketCard"]')           # returns a list of classes that matches..

        
        
        if len(Ticket_Card) == 2:
            # if len of Ticket_card is 2 first one is dep second one is arrival
            departure = Ticket_Card[0]
            arrival = Ticket_Card[1]
        
            fs_departure_info_section = departure.select('[class*="InfoSection"]')           # returns a list of classes that matches..
            fs_arrival_info_section = arrival.select('[class*="InfoSection"]')           # returns a list of classes that matches..
        
            dep_extracts = self.ticket_card_extracts(fs_departure_info_section)
            arr_extracts = self.ticket_card_extracts(fs_arrival_info_section)
            base_fs_data =  {'fsDeparture': dep_extracts, 'fsArrival': arr_extracts, 'fsDelayStatus': delay_status}

            # # TODO flight discrepancy: Can detect multiple flights using same flight number. but can only access new one. old one requires numeric flightid
            multiple_flights_soup_extracts = self.multi_flight_extracts(soup_fs)
            multiple_flights = self.multi_flight_comparison(dep_extracts, multiple_flights_soup_extracts)
            if multiple_flights:
                base_fs_data['multipleFlights'] = multiple_flights

            return base_fs_data
        elif len(Ticket_Card) != 2:
            # TODO test: Save soup, flight number, datetime, etc and log error. Investigate later.
            print('flight not found')
            return 
    
    
    def flightStats_data_frontend_format(self,flightID, return_bs4=False):
        # TODO Refactor: This function can be refactored to FlightStatsScraper class in core/api
        
        fss = FlightStatsScraper()
        fs_data = fss.scrape(flightID, return_bs4=return_bs4)
        
        
        # use this for custom datetime instead 
        # fs_data = fss.scrape(airline_code="UA", flt_num_query="45", departure_date="20250717", return_bs4=False)

        if not fs_data:     # early retur if data isnt found
            return
        
        departure = fs_data.get('fsDeparture')
        arrival = fs_data.get('fsArrival')

        # TODO Test: 
                # Flow - return city from fs and fv , match with fuzz find on similarity scale if theyre both same fire up LLM 
        # TODO Test: If this is unavailable, which has been the case lately- May 2024, use the other source for determining scheduled and actual departure and arriavl times
        return {
            'flightStatsFlightID': flightID,
            'flightStatsDelayStatus': fs_data.get('fsDelayStatus'),
            'flightStatsOrigin':departure.get('Code'),
            'flightStatsDestination':arrival.get('Code'),
            'flightStatsOriginGate': departure.get('TerminalGate'),
            'flightStatsDestinationGate': arrival.get('TerminalGate'),
            # departure date and time
            'flightStatsScheduledDepartureDate': departure.get('ScheduledDate'),    # Date
            'flightStatsScheduledDepartureTime': departure.get('ScheduledTime'),    # Scheduled Time
            'flightStatsEstimatedDepartureTime': departure.get('EstimatedTime'),    # Estimated Time
            'flightStatsActualDepartureTime': departure.get('ActualTime'),          # Actual Time
            # arrival times
            'flightStatsScheduledArrivalTime': arrival.get('ScheduledTime'),        # Scheduled arrival time
            'flightStatsActualArrivalTime': arrival.get('ActualTime'),              # Actual arrival time
            # Multiple flights for same day
            # TODO flight descrepency: add a date befor eand date after as well.
            'flightStatsMultipleFlights': fs_data.get('multipleFlights')
        }


class FlightStatsScraper:
    def __init__(self):
        self.extractor = FlightStatsExtractor()

    def parse_query_for_flight_stats(self,flightID):
        """ 
        returns: tuple with IATA airline code and flight number
            e.g: ('UA','4433')
        """

        qc = QueryClassifier()
        parsed_flight_category = qc.parse_flight_query(flightID)

        code_type = parsed_flight_category.get('code_type')
        IATA_airline_code = parsed_flight_category.get('IATA_airline_code') 
        ICAO_airline_code = parsed_flight_category.get('ICAO_airline_code') 
        flight_number = parsed_flight_category.get('flight_number') 


        if code_type and code_type == 'ICAO':
            codes = Source_links_and_api().regional_ICAO_to_associated_major_IATA()
            if ICAO_airline_code in codes.keys():
                associated_major_IATA_airline_code = codes.get(ICAO_airline_code)
                return associated_major_IATA_airline_code, flight_number
        else:
            return IATA_airline_code, flight_number


    def scrape(self,flightID, return_bs4=False):
        """ Returns clean scraped data or bs4 data if return_bs4 is True. Date format is YYYYMMDD """
        
        rc=Root_class()

        IATA_airline_code, flt_num = self.parse_query_for_flight_stats(flightID)
        flight_stats_url = Source_links_and_api().flight_stats_url(IATAAirlineCode=IATA_airline_code, flight_number=flt_num)

        # TODO flight discrepancy: flightStats is returning no data for flight going out next day.
            # This can be a simple fix by adding a day prior/post flight date using timedelta? - careful with end of month day plus 1 same for beginning minus 1.
            # This can assist in improving the accuracy of the data and prevent AJMS.flightAware data discrepancy.

        soup_fs = rc.request(flight_stats_url)
        self.soup = soup_fs

        return soup_fs if return_bs4 else self.extractor.ticket_card(soup_fs)