from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from time import sleep

class EDCT_LookUp:
    def __init__(self) -> None:
        # setting up headless chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.browser = webdriver.Chrome(service=service, options=chrome_options)
            print("Chrome WebDriver initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    
    def extract_edct(self, flightID: str, origin: str, destination: str):
        faa_edct_lookup_url = "https://www.fly.faa.gov/edct/jsp/edctLookUp.jsp"
        self.browser.get(faa_edct_lookup_url)

        callsign_input = WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.NAME, "callsign"))
            )
        callsign_input.send_keys(flightID)

        dept_input = self.browser.find_element(By.NAME, "dept")
        dept_input.send_keys(origin)  # Replace with your origin code

        arr_input = self.browser.find_element(By.NAME, "arr")
        arr_input.send_keys(destination)  # Replace with your destination code
        lookup_button = self.browser.find_element(By.XPATH, "//input[@value='Lookup EDCT']")
        lookup_button.click()

        table = self.browser.find_element(By.XPATH, "//table[@border='1']")
        rows = table.find_elements(By.TAG_NAME, "tr")

        edct_collective = []
        
        for row in rows[1:]:    # Skip the header row 
            cols = row.find_elements(By.TAG_NAME, "td")
            edct = cols[0].text
            filed_departure_time = cols[1].text
            control_element = cols[2].text.strip()  # Remove leading/trailing whitespace
            flight_cancelled = cols[3].text
            if not edct =='--':     # Only extract ones that have edct info.
                edct_collective.append({
                    "filedDepartureTime": filed_departure_time,
                    "edct": edct,
                    "controlElement": control_element,
                    "flightCancelled": flight_cancelled
                })
        return edct_collective

        
        
    



