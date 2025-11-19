from datetime import datetime
import logging
import re
from typing import Annotated, Optional, Union
from pydantic import AfterValidator, BaseModel

from services.notification_service import send_telegram_notification_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


# TODO Test: Use pydantic to validate the data for all route returns:
        # For example, flighStats returns a 4 letter ICAO code, times,
        # delay status etc. validate this data(received data vs expected data) for consistency:
        # fire notification for outlaws

# Validate incoming SearchData request
class SearchData(BaseModel):
    email: str
    stId: Union[str, None]        # submitTerm can be string or null type of variable from react
    submitTerm: Union[str, None]        # submitTerm can be string or null type of variable from react
    timestamp: datetime




# Define validator functions OUTSIDE the class
# NOTE: These validator functions need to be at module level - they can't be defined inside the class when using Annotated types
def validate_ICAO_airport_code(v: str) -> str:
    if not v.isalpha() or len(v) != 4 or not v.isupper():
        # TODO airport code: is this supposed to be alphanumeric?
        message = f'ICAO Airport code must be 4 char, uppercase .isalpha letters. Rather this was supplied {v}'
        send_telegram_notification_service(message=message)
        logger.warning(message)
        # raise ValueError(message)
    return v

def validate_IATA_airport_code(v: str) -> str:
    if not v.isalpha() or len(v) != 3 or not v.isupper():
        # TODO airport code: is this supposed to be alphanumeric?
        message = f'Airport code must be 3 char uppercase .isalpha letters. Rather this was supplied {v}'
        send_telegram_notification_service(message=message)
        logger.warning(message)
        # raise ValueError(message)
    return v

def validate_fs_delay_status(v: str) -> str:
    # 1. Allowed fixed statuses
    allowed_statuses = ['On time', 'Scheduled', 'Delayed', 'Estimated', 'Departed', 'Cancelled']

    # 2. Regex for "Delayed by..." (hours/minutes)
    delayed_pattern = re.compile(r"^Delayed by (?:(?:\d+h\s*)?(?:\d+m)?|\d+ minutes? ago)$")

    # 3. STRICT Regex for "Diverted to [3-Letter Code]"
    # Matches: "Diverted to BWI", "Diverted to ORD"
    # Fails: "Diverted to ", "Diverted to Chicago", "Diverted to KBWI" (4 letters)
    diverted_pattern = re.compile(r"^Diverted to [A-Z]{3}$")

    if v in allowed_statuses:
        return v
    elif delayed_pattern.match(v):
        return v
    elif diverted_pattern.match(v):
        return v
    else:
        message = (f'FS Delay status must be one of: On time, Scheduled, Delayed. Rather this was supplied {v}')
        send_telegram_notification_service(message=message)
        logger.warning(message)
        return v

def validate_fs_time_format(v: str) -> str:
    """ Validate time format e.g "12:00 +01" or "12:00 CST" or "02:00 ChST" """
    if not v or v == "-- ":  # Handle empty and "--" cases
        # Thes logs are discarded because Actual/Estimated times could be empty 
        # message=f"Time format error. Supplied: {v}"
        # send_telegram_notification_service(message)
        # logger.warning(message)
        return v
    # Allow both "HH:MM TZ" and "HH:MM +XX" formats
    time_pattern_w_tz = r'^\d{1,2}:\d{2} (?:[A-Za-z]{1,2}[A-Z]{2}|[+-]\d{2})$'
    if not re.match(time_pattern_w_tz, v):
        message = f'Time must be in format "HH:MM TZ" or "HH:MM +XX". Rather this was supplied {v}'
        send_telegram_notification_service(message=message)
        logger.warning(message)
        # raise ValueError(message)
    return v

def validate_fs_date_format(v: str) -> str:
    """ Validate date format e.g "04-Oct-2025" """
    if not v:  
        message=f"Date format error. Supplied: {v}"
        send_telegram_notification_service(message)
        logger.warning(message)
        return v
    # Validate "DD-MMM-YYYY" format
    pattern = r'^\d{1,2}-[A-Za-z]{3,4}-\d{4}$'
    if not re.match(pattern, v):
        message = f'Date must be in format "DD-MMM-YYYY". Rather this was supplied {v}'
        send_telegram_notification_service(message=message)
        logger.warning(message)
        # raise ValueError(message)
    return v

# Create custom types
ICAOAirportCode = Annotated[str, AfterValidator(validate_ICAO_airport_code)]
IATAAirportCode = Annotated[str, AfterValidator(validate_IATA_airport_code)]
DelayStatus = Annotated[str, AfterValidator(validate_fs_delay_status)]
TimeFormat = Annotated[str, AfterValidator(validate_fs_time_format)]
DateFormat = Annotated[str, AfterValidator(validate_fs_date_format)]

class FlightStatsResponse(BaseModel):
    flightStatsFlightID: str
    flightStatsDelayStatus: Optional[DelayStatus] = None

    flightStatsOrigin: IATAAirportCode          # Origin - A necessary field
    flightStatsDestination: IATAAirportCode     # Destination - A necessary field

    flightStatsOriginGate: Optional[str] = None
    flightStatsDestinationGate: Optional[str] = None

    # departure date and time
    flightStatsScheduledDepartureDate: DateFormat      # Date - A necessary field
    flightStatsScheduledDepartureTime: TimeFormat      # Scheduled Time - A necessary field

    flightStatsEstimatedDepartureTime: Optional[TimeFormat] = None      # Estimated Time
    flightStatsActualDepartureTime: Optional[TimeFormat] = None         # Actual Time
    # arrival times
    flightStatsScheduledArrivalTime: Optional[TimeFormat] = None
    flightStatsActualArrivalTime: Optional[TimeFormat] = None



class FlightAware(BaseModel):
    fa_ident_icao: str
    fa_origin: str
    fa_destination: str
    fa_registration: str
    fa_date_out: str
    fa_scheduled_out: str
    fa_estimated_out: str
    fa_scheduled_in: str
    fa_estimated_in: str
    fa_terminal_origin: str
    fa_terminal_destination: str
    fa_gate_origin: str
    fa_gate_destination: str
    fa_filed_altitude: str
    fa_filed_ete: str
    fa_route: str
    fa_sv: str
    



# Old code - not used anymore
class AirportCache (BaseModel):
    # id: str
    IATA: Optional[IATAAirportCode] = None  # Make it Optional
    ICAO: ICAOAirportCode
    airportName: str
    regionName: str
    countryCode: str
    weather: dict
    # TODO feature: Add runways, lat longs, 
