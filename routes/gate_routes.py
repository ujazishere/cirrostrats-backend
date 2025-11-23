from fastapi import APIRouter
from services.gate_service import gate_returns_service

router = APIRouter()

@router.get("/gates/{gate}")
async def gate_returns(gate):
    return await gate_returns_service(gate)
   