from core.search.query_classifier import QueryClassifier
from services.flight_aggregator_service import aws_jms_service,flight_stats_url_service,aviation_stack_service,flight_aware_w_auth_service,get_edct_info_service

from fastapi import APIRouter
router = APIRouter()

# RESTRUCTURING UPDATE: Now uses dynamic path resolution (October 2025)
# QueryClassifier automatically finds ICAO file using dynamic paths

@router.get("/ajms/{flightID}")
async def aws_jms(flightID, mock=False):
    return await aws_jms_service(flightID,mock)


@router.get("/flightStatsTZ/{flightID}")
async def flight_stats_url(flightID):
    return await flight_stats_url_service(flightID)


@router.get("/aviationStack/{flight_number}")
async def aviation_stack(flight_number):
    return await aviation_stack_service(flight_number)


@router.get("/flightAware/{flight_number}")
async def flight_aware_w_auth(flight_number, mock=False):
    return await flight_aware_w_auth_service(flight_number, mock)

@router.get("/EDCTLookup/{flightID}")
async def get_edct_info(flightID: str, origin: str, destination: str):
    return await get_edct_info_service(flightID, origin, destination)