import json
from core.EDCT_Lookup import EDCT_LookUp
import requests
from core.tests.mock_test_data import Mock_data
from core.dep_des import Pull_flight_info
from core.flight_deets_pre_processor import response_filter
from core.root_class import Fetching_Mechanism, Source_links_and_api
from core.search.query_classifier import QueryClassifier

qc = QueryClassifier(icao_file_path="unique_icao.pkl")
sic_docs = qc.initialize_search_index_collection()



from fastapi import APIRouter
from services.flight_aggregator_service import aws_jms_service,flight_stats_url_service,aviation_stack_service,flight_aware_w_auth_service,get_edct_info_service
router = APIRouter()


@router.get("/ajms/{flightID}")
async def aws_jms(flightID, mock=False):
    return await aws_jms_service(flightID,mock)


@router.get("/flightStatsTZ/{flightID}")
async def flight_stats_url(flightID):
    return await flight_stats_url_service(flightID)


@router.get("/aviationStack/{flight_number}")
async def aviation_stack(flight_number):
    return await aviation_stack_service(flight_number)


# @router.get("/flightAware/{flight_number}")
# async def flight_aware_w_auth(flight_number, mock=False):
#     return await flight_aware_w_auth_service(flight_number, mock)

@router.get("/flightAware/{flight_number}")
async def flight_aware_w_auth(flight_number, mock=False):
    if mock:
        md = Mock_data()
        md.flight_data_init(html_injected_weather=False)
        print('mock flight aware data', md.flightAware)
        return md.flightAware
    
    # sl.flight_stats_url(flight_number_query)
    fm = Fetching_Mechanism(flt_num=flight_number)
    sl = Source_links_and_api()
    flt_info = Pull_flight_info()

    link = sl.flight_aware_w_auth(flight_number)
    resp_dict: dict = await fm.async_pull([link])
    # return resp_dict
    resp = response_filter(resp_dict, "json",)
    fa_return = resp['flights']
    flight_aware_data = flt_info.fa_data_pull(pre_process=fa_return)

    # Accounted for gate through flight aware. gives terminal and gate as separate key value pairs.
    return flight_aware_data

@router.get("/EDCTLookup/{flightID}")
async def get_edct_info(flightID: str, origin: str, destination: str):
    return await get_edct_info_service(flightID, origin, destination)