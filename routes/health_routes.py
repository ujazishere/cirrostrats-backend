"""Health and readiness endpoints for orchestration and monitoring."""
from fastapi import APIRouter, Response, status
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health():
    """
    Liveness probe - is the app running?
    Returns 200 if the application is alive.
    """
    return {"status": "healthy", "service": "cirrostrats-backend-api"}


@router.get("/ready")
async def readiness():
    """
    Readiness probe - can the app serve traffic?
    Checks dependencies (MongoDB, Redis) are accessible.
    """
    try:
        # Check MongoDB connection
        from config.database import client, client_UJ
        client.admin.command('ping')
        client_UJ.admin.command('ping')

        # Check Redis connection
        import redis
        r = redis.Redis(host='redis', port=6379, db=0, socket_connect_timeout=2)
        r.ping()

        return {
            "status": "ready",
            "dependencies": {
                "mongodb": "ok",
                "mongodb_uj": "ok",
                "redis": "ok"
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return Response(
            content=f'{{"status": "not ready", "error": "{str(e)}"}}',
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json"
        )
