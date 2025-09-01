from fastapi import APIRouter
from services.misc_service import nas_service
from typing import Optional
router = APIRouter()


@router.get("/NAS")
async def nas(
    airport: Optional[str]  = None,
    departure: Optional[str] = None,
    destination: Optional[str] = None
):
   return await nas_service(airport,departure,destination)