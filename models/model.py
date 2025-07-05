from datetime import datetime
from typing import Union
from pydantic import BaseModel

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

class Airport (BaseModel):
    id: str
    name: str
    code: str

# Define a Pydantic model to validate incoming SearchData request
class SearchData(BaseModel):
    email: str
    stId: Union[str, None]        # submitTerm can be string or null type of variable from react
    submitTerm: Union[str, None]        # submitTerm can be string or null type of variable from react
    timestamp: datetime
