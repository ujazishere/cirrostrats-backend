from datetime import datetime
import re
import bs4
import logging
from routes.root.root_class import Root_class
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class Newark_departures_scrape(Root_class):

    def soup_scrape(self,) -> list:
        """ Get All departures soups in list. 4 soups in list before the day is split in 4 parts. """
        day_times = {'very_early_morn': '?tp=0',
                    'morning': '?tp6',
                    'noon': '?tp=12',
                    'evening': '?tp=18',
                        }                                

        soups = []

        for time_of_the_day, time_associated_code in day_times.items():
            EWR_deps_url = f'https://www.airport-ewr.com/newark-departures{time_associated_code}'

            soup = self.request(EWR_deps_url)
            soups.append(soup)
        
        return soups


    def extract_flight_id_and_link(self,) -> List[Tuple[str, str]]:
        # TODO: Need to put this in celery.
        """Extract flight numbers and links from BeautifulSoup data with redundancy handling.
        
        Args:
            raw_bs4_all_EWR_deps: List of BeautifulSoup elements containing flight information
            
        Returns:
            List of tuples containing (flight_number, link)
        """
        EWR_departures_and_links = []
        
        soups = self.soup_scrape()
        for s in soups:
            flight_id_link = s.find_all('div', class_="flight-row")
            try:
                raw_bs4_all_EWR_deps = flight_id_link[1:]
            except IndexError:
                logger.warn("newark_depatures_scrape soups index error. soup ", s)
                break

            for element in raw_bs4_all_EWR_deps:
                # Skip if element is just a newline
                if element == '\n':
                    continue
                    
                # Verify it's a BeautifulSoup Tag object
                if not isinstance(element, bs4.element.Tag):
                    continue
                    
                # Find all flight columns - use find() instead of find_all()[0] for safety
                dep = element.find('div', class_="flight-col flight-col__flight")
                if not dep:
                    continue
                    
                # Find the anchor tag with multiple safety checks
                s_tag = dep.find('a')
                if not s_tag:
                    continue
                    
                # Extract link and flight number with fallbacks
                link = s_tag.get('href', '').strip()
                flight_number = s_tag.get_text(strip=True)
                
                # Only add if we have both pieces of information
                if flight_number and link:
                    EWR_departures_and_links.append((flight_number, link))
                    
        self.EWR_departures_and_links = EWR_departures_and_links

        return EWR_departures_and_links


    def time_converter(self,flight_id, time_data):
        # TODO declutter: assess this time pattern and can this be reused elsewhere, if yes,
            # move it away to root_class or separate data validation and conversion file.?
        pattern = r"(\d{1,2}):(\d{2})\s*(am|pm)"
        match = re.search(pattern, time_data)
        if match:
            hours = int(match.group(1))
            minutes = match.group(2)
            am_pm = match.group(3).lower()

            if am_pm == "pm" and hours != 12:
                hours += 12
            elif am_pm == "am" and hours == 12:
                hours = 0
            time_str = f"{hours:02d}:{minutes}"
            # time_obj = datetime.strptime(time_str, "%H%M").time()         # Attempt to convert to datetime obj but gives error when saving to mongo
            return time_str
        else:
            logger.warn("Time issues in time_converter:", flight_id, time_data)


    def validate_date(self,flight_id, date_str):
        try:
            datetime.strptime(date_str, "%B %d, %Y").date()
            return date_str
            # return datetime.strptime(date_str, "%B %d, %Y").date()            # attemt to return datetime obj but mongo wouldnt take it unless its precise.
        except ValueError:
            logger.warn("Date issues in validate_date:", date_str, flight_id)
            return False


    def extract_individual_flight_details(self, flight_id, soup) -> Tuple[Optional[str], ...]:
        """Extract flight details with robust error handling and logging.
        
        Args:
            soup_gate: BeautifulSoup object containing flight information
            
        Returns:
            dict with primary key as flight number and value as sub dict with date, scheduled, 
            scheduled type and gate - check mock data mongo_collection.gate_collection.
        """
        # Initialize all values as None
        scheduled_date = scheduled_time = None
        extracts = {}
        try:
            # Extract flight info containers with defensive selection
            flight_info = soup.select('div[class*="flight-info"]') or []
            flight_info_date = soup.select('div[class*="flight-info__date"]') or []
            flight_info_sc_dep = soup.select('div[class*="flight-info__sch-departed"]') or []
            # 1. Extract date
            if flight_info_date:
                scheduled_date_extracts = flight_info_date[0].get_text(strip=True)
                scheduled_date = self.validate_date(flight_id, scheduled_date_extracts)
            else:
                logger.warning("Flight date element not found in HTML structure", flight_id, scheduled_date_extracts)
                
            # 2. Extract scheduled time
            if flight_info_sc_dep and scheduled_date:
                scheduled_time_extracts = flight_info_sc_dep[0].get_text(strip=True)
                scheduled_time = self.time_converter(flight_id, scheduled_time_extracts)
                if scheduled_time:
                    # Combine date and time objects into a datetime object
                    datetime_obj = scheduled_date+" "+scheduled_time
                    extracts.update({"Scheduled": datetime_obj})
            else:
                logger.warning("Scheduled departure time element not found in HTML structure", flight_id)

            # 3. Extract departure title
            try:
                dep_title = flight_info[7].text.strip()
                if 'Estimated Departure Time' in dep_title:
                    departure_time_raw = flight_info[8].text.strip()
                    hhmm = self.time_converter(flight_id, departure_time_raw)
                    extracts.update({"Estimated":hhmm})
                elif "Departed at:" in dep_title:
                    departure_time_raw = flight_info[8].text.strip()
                    hhmm = self.time_converter(flight_id, departure_time_raw)
                    extracts.update({"Departed":hhmm})
                else:
                    logger.warning(f"Outlaw in estimated/actual time -- departure extract")
                    
            except IndexError:
                logger.warning(f"Flight info index 7 or 8 not found (only {len(flight_info)} elements present)")
                

            # 4. Extract gate
            try:
                gate_extract = flight_info[14].text.strip()
                # TODO: Flaw - few showes 'Gate:' as the data extract because of either multiple flights associated or diverted or gate returns.
                    # make a separate flightstats scraper for ones with gate issues and account for multiple flights, divers, etc?
                    # But then it may clash with hard stands multiple flights/diverts/gate changes etc.
                    # Better leave it alone and give it link to check? or give it a gate and give it link to check on google.
                    # Google link: https://www.google.com/search?q=ua577
                if "Gate:" in gate_extract:
                    gate_extract = None
                extracts.update({"Gate": gate_extract})
            except IndexError:
                logger.warning(f"Gate info index 14 not found (only {len(flight_info)} elements present)")

            # Log successful extraction
            if not all([extracts.get('Scheduled'), extracts.get('Gate')]):
                logger.info("Partial flight details extracted (some fields missing),", type(extracts),extracts)

        except Exception as e:
            logger.error(f"Unexpected error during flight details extraction: {str(e)}", exc_info=True)

        return extracts
    
    
    def gate_scrape_per_flight(self,flight_id, link) -> Dict:
        """ 
        Function returns such itmes in dict:
            Scheduled, Departed/Estimated/etc, Gate, FlightID
        """
        burl = "https://www.airport-ewr.com"
        url = burl+link
        soup = self.request(url)
        gate_data = self.extract_individual_flight_details(flight_id, soup)
        gate_data.update({'FlightID': flight_id})
        return gate_data
    
    
    def gate_scrape_main(self, test=False):
        """Scrapes ALL UA departures out of Newark and thier associated info.
        Typically takes 1-2 minutes for the complete UA scrapes.
        Test will use first 30 newark departures and fetch UA ones from them.
        
        
        function returns list of such itmes:
            Scheduled, Departed/Estimated/etc, Gate, FlightID
        """

        # Newark departurns returns:
            # tuple format (flight_number, link)
        all_day_EWR_departures = self.extract_flight_id_and_link()
        self.all_day_EWR_departures = all_day_EWR_departures

        flight_rows = []
        
        if test==True:
            all_day_EWR_departures = all_day_EWR_departures[:30]
        
        for flight_id,link in all_day_EWR_departures:
            if flight_id[:2] == "UA":
                # time.sleep(1)  # Respectful scraping delay
                flight_rows.append(self.gate_scrape_per_flight(flight_id,link))

        self.final_gate_scrape_flight_rows = flight_rows

        return flight_rows
        