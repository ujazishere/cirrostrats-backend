import re
import bs4
import logging
from routes.root.root_class import Root_class
from typing import List, Optional, Tuple

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
                    
        return EWR_departures_and_links


    def time_converter(self, time_data):
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
            return f"{hours:02d}:{minutes}"


    def extract_individual_flight_details(self, soup) -> Tuple[Optional[str], ...]:
        """Extract flight details with robust error handling and logging.
        
        Args:
            soup_gate: BeautifulSoup object containing flight information
            
        Returns:
            dict with primary key as flight number and value as sub dict with date, scheduled, 
            scheduled type and gate - check mock data mongo_collection.gate_collection.
        """
        # Initialize all values as None
        extracts = {}
        try:
            # Extract flight info containers with defensive selection
            flight_info = soup.select('div[class*="flight-info"]') or []
            flight_info_date = soup.select('div[class*="flight-info__date"]') or []
            flight_info_sc_dep = soup.select('div[class*="flight-info__sch-departed"]') or []
            # 1. Extract date
            if flight_info_date:
                extracts.update({"Date": flight_info_date[0].get_text(strip=True)})
            else:
                logger.warning("Flight date element not found in HTML structure")
                
            # 2. Extract scheduled time
            if flight_info_sc_dep:
                scheduled_time = flight_info_sc_dep[0].get_text(strip=True)
                hhmm = self.time_converter(scheduled_time)
                extracts.update({"Scheduled" : hhmm})
            else:
                logger.warning("Scheduled departure time element not found")

            # 3. Extract departure title
            try:
                dep_title = flight_info[7].text.strip()
                if "Departure Time" in dep_title:           # Typically estimated
                    departure_time_title = dep_title.strip("Departure Time:")
                    departure_time_raw = flight_info[8].text.strip()
                    hhmm = self.time_converter(departure_time_raw)
                    extracts.update({departure_time_title:hhmm})
                elif "Departed at:" in dep_title:
                    departure_time_raw = flight_info[8].text.strip()
                    hhmm = self.time_converter(departure_time_raw)
                    extracts.update({"Departed":hhmm})
                else:
                    logger.warning(f"Outlaw in estimated/actual time -- departure extract")
                    
            except IndexError:
                logger.warning(f"Flight info index 7 or 8 not found (only {len(flight_info)} elements present)")
                

            # 4. Extract gate
            try:
                extracts.update({"Gate": flight_info[14].text.strip()})
            except IndexError:
                logger.warning(f"Gate info index 14 not found (only {len(flight_info)} elements present)")

            # Log successful extraction
            if not all([extracts.get('Date'), extracts.get('Scheduled'), extracts.get('Gate')]):
                logger.info("Partial flight details extracted (some fields missing)")

        except Exception as e:
            logger.error(f"Unexpected error during flight details extraction: {str(e)}", exc_info=True)

        return extracts
    
    
    def gate_scrapes(self,flight_id, link):
        burl = "https://www.airport-ewr.com"
        url = burl+link
        soup = self.request(url)
        return {flight_id: self.extract_individual_flight_details(soup)}
    
    
    def gate_scrape_main(self):
        all_day_EWR_departures = self.extract_flight_id_and_link()
        flight_rows = []
        for flight_id,link in all_day_EWR_departures[350:385]:
            # time.sleep(1)  # Respectful scraping delay
            flight_rows.append(self.gate_scrapes(flight_id,link))
        return flight_rows
        