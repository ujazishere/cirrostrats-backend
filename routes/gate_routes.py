from fastapi import APIRouter
from services.gate_service import gate_returns_service

router = APIRouter()

@router.get("/gates/{referenceId}")
async def gate_returns(referenceId):
    return await gate_returns_service(referenceId)
   