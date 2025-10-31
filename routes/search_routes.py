from fastapi import APIRouter
from models.model import SearchData
from services.search_service import get_search_suggestions_service,track_search_service,get_search_timeline_service,get_all_searches_service,get_user_searches_service,raw_search_handler_service

router = APIRouter()

# GET /searches/suggestions/Anonymous?query= HTTP/1.1" 200 OK

@router.get("/searches/suggestions/{email}")
async def get_search_suggestions(email: str, query: str, limit: int = 100):
    return await get_search_suggestions_service(email, query, limit)


@router.post('/searches/track')
async def track_search(data: SearchData):
    return await track_search_service(data)

@router.get('/searches/timeline')
async def get_search_timeline():
    return await get_search_timeline_service()


@router.get('/searches/all')
async def get_all_searches():
    return await get_all_searches_service()

@router.get('/searches/{email}')
async def get_user_searches(email):
    return await get_user_searches_service()


@router.get('/query')       
# @router.get('/query/{passed_variable}')       # This can be used to get the passed variable but search already takes care of that.
async def raw_search_handler(search: str = None):
    return await raw_search_handler_service(search)