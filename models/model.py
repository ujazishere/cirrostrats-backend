from pydantic import BaseModel


class Flight(BaseModel):
    gate: str
    flight_number: str
    destination: str


class Airport (BaseModel):
    id: str
    name: str
    code: str
