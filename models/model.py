from pydantic import BaseModel




# {
#     'name': 'San Fran',
#     'code': 'SFO',
#     'weather': 
#             {
#                 'datis': '',
#                 'metar': '',
#                 'taf': '',
#             }
# }

# {
#     'flight-number': 'UA4433',
#             'departue': '',
#             'arrival': '',
#             'route':'',
#             'ETA':'',
#             'STD'



# }



class FlightNumber(BaseModel):
    flight_number: str
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
