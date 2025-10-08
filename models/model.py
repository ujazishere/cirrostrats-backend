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
def validate_IATA_airport_code(v: str) -> str:
    if not v.isalpha() or len(v) != 3 or not v.isupper():
        # TODO airport code: is this supposed to be alphanumeric?
        message = f'Airport code must be 3 uppercase .isalpha letters. Rather this was supplied {v}'
        send_telegram_notification_service(message=message)
        logger.warning(message)
        # raise ValueError(message)
    return v

def validate_fs_delay_status(v: str) -> str:
    allowed_statuses = ['On time', 'Scheduled', 'Delayed', 'Estimated', 'Departed']

    # Regex for: "Delayed by <number> minute(s) ago or just <number>m"
    delayed_pattern = re.compile(r"^Delayed by (\d+)(?: minutes? ago|m)$")

    if v in allowed_statuses:
        return v
    elif delayed_pattern.match(v):
        return v
    else:
        message = (f'FS Delay status must be one of: On time, Scheduled, Delayed. Rather this was supplied {v}')
        send_telegram_notification_service(message=message)
        logger.warning(message)
        # raise ValueError(message)

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
AirportCode = Annotated[str, AfterValidator(validate_IATA_airport_code)]
DelayStatus = Annotated[str, AfterValidator(validate_fs_delay_status)]
TimeFormat = Annotated[str, AfterValidator(validate_fs_time_format)]
DateFormat = Annotated[str, AfterValidator(validate_fs_date_format)]

class FlightStatsResponse(BaseModel):
    flightStatsFlightID: str
    flightStatsDelayStatus: Optional[DelayStatus] = None
    flightStatsOrigin: AirportCode          # Origin - A necessary field
    flightStatsDestination: AirportCode     # Destination - A necessary field
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



# Old code - not used anymore
class FlightData(BaseModel):
    flightID: str
    origin: str
    destination: str
    registration: str
    scheduled_out: str
    estimated_out: str
    scheduled_in: str
    estimated_in: str
    terminal_origin: str
    terminal_destination: str
    gate_origin: str
    gate_destination: str
    terminal_origin: str
    filed_altitude: str
    filed_ete: str
    route: str
    sv: str
    gate: str
    destination: str

# Old code - not used anymore
class Airport (BaseModel):
    id: str
    name: str
    code: str
