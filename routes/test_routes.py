from fastapi import APIRouter
from services.test_service import test_flight_deet_data_service
router = APIRouter()
    
@router.get("/testDataReturns")
async def test_flight_deet_data(airportLookup: str = None):
    return test_flight_deet_data_service(airportLookup)