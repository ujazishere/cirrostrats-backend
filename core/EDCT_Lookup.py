import requests
from bs4 import BeautifulSoup

class EDCT_LookUp:
    def __init__(self):
        # URL of the EDCT lookup page
        self.url = "https://www.fly.faa.gov/edct/showEDCT"
        # self.url = "https://www.fly.faa.gov/edct/jsp/showEDCT.jsp"
        
    def extract_edct(self, call_sign: str, origin: str, destination: str):
        # Form data
        data = {
            "callsign": call_sign.upper(),  # Convert to uppercase to match form behavior
            "dept": origin.upper(),
            "arr": destination.upper(),
        }

        # Send POST request
        response = requests.post(self.url, data=data)
        edct_collective = []

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the results table (same as Selenium's border=1 table)
            table = soup.find('table', {'border': '1'})
            
            if table:
                # Process all rows except header (same as rows[1:] in Selenium)
                rows = table.find_all('tr')[1:]
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:  # Ensure we have enough columns
                        edct = cols[0].get_text(strip=True)
                        filed_departure_time = cols[1].get_text(strip=True)
                        control_element = cols[2].get_text(strip=True)
                        flight_cancelled = cols[3].get_text(strip=True)
                        
                        if edct != '--':
                            edct_collective.append({
                                "filedDepartureTime": filed_departure_time,
                                "edct": edct,
                                "controlElement": control_element,
                                "flightCancelled": flight_cancelled
                            })
            
            print('edct collective', edct_collective)
            return edct_collective
        else:
            print(f"Request failed with status {response.status_code}")
            return None

# Example usage:
# edct = EDCT_LookUp()
# results = edct.extract_edct("GJS4384", "ILM", "EWR")
# print(results)