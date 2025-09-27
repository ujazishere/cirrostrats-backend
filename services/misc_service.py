from typing import Dict, Optional, Union
from core.api.nas import NAS


async def nas_service(
    airport: Optional[str]  = None,
    departure: Optional[str] = None,
    destination: Optional[str] = None
):
    # TODO: Canadian airports need to be handled. As of July 2025 throws error in fronend.
    nas = NAS()
    if airport:
        nas_returns = nas.nas_airport_matcher(airport=airport)
    else:
        nas_returns = nas.nas_airport_matcher(departure=departure,destination=destination)
    return nas_returns