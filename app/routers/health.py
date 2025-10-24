"""
Health Check Router
프로덕션 배포용 Health Check 엔드포인트

Endpoints:
- GET /health - Basic health status
- GET /health/db - Database connection check
- GET /health/ready - Readiness probe (Kubernetes)
- GET /health/live - Liveness probe (Kubernetes)

Security:
- No authentication required (public endpoints)
- Minimal logging (high frequency)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
from datetime import datetime
import logging

router = APIRouter(tags=["health"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """
    Basic Health Check

    Returns basic application health status.
    No database or dependency checks.

    Returns:
        {
            "status": "healthy",
            "timestamp": "2025-10-22T12:00:00.000Z",
            "version": "1.0.0"
        }
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "service": "admin-api"
    }


@router.get("/health/db")
async def health_check_database(db: AsyncSession = Depends(get_db)):
    """
    Database Health Check

    Verifies database connection by executing a simple query.

    Returns:
        200 OK: Database is connected
        503 Service Unavailable: Database connection failed

    Returns:
        {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-10-22T12:00:00.000Z",
            "db_name": "admin_db"
        }
    """
    try:
        # Execute simple query to verify connection
        result = await db.execute(text("SELECT 1"))
        result.fetchone()

        # Get database name
        db_name_result = await db.execute(text("SELECT current_database()"))
        db_name = db_name_result.scalar()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "db_name": db_name
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": "Database connection failed"
            }
        )


@router.get("/health/ready")
@admin_router.get("/health/ready")  # Admin API용 별도 라우트
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """
    Readiness Probe (Kubernetes)

    Checks if the application is ready to accept traffic.
    Verifies all dependencies are available.

    Returns:
        200 OK: Application is ready
        503 Service Unavailable: Application is not ready

    Returns:
        {
            "status": "ready",
            "timestamp": "2025-10-22T12:00:00.000Z",
            "checks": {
                "database": "ok",
                "application": "ok",
                "tomcat": "ok"
            }
        }
    """
    checks = {
        "application": "ok"
    }

    # Check database connection
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        checks["database"] = "ok"

    except Exception as e:
        logger.error(f"Readiness check - Database failed: {e}")
        checks["database"] = "failed"

    # Check Tomcat (User UI Server) - from settings
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(settings.USER_UI_URL)
            if response.status_code == 200:
                checks["tomcat"] = "ok"
            else:
                checks["tomcat"] = "failed"
    except Exception as e:
        logger.error(f"Readiness check - Tomcat failed: {e}")
        checks["tomcat"] = "failed"

    # Check User UI Database (if configured)
    if settings.USER_DB_URL:
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            user_engine = create_async_engine(settings.USER_DB_URL)
            async with user_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                checks["user_database"] = "ok"
            await user_engine.dispose()
        except Exception as e:
            logger.error(f"Readiness check - User Database failed: {e}")
            checks["user_database"] = "failed"

    # Return 503 if any critical dependency is down
    if checks.get("database") == "failed" or checks.get("tomcat") == "failed":
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "checks": checks,
                "error": "One or more services are not available"
            }
        )

    # All checks passed
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks
    }


@router.get("/health/live")
async def liveness_probe():
    """
    Liveness Probe (Kubernetes)

    Checks if the application is alive (not deadlocked/crashed).
    Does NOT check dependencies (should be fast).

    This endpoint should always return 200 OK if the application is running.
    Kubernetes will restart the pod if this fails.

    Returns:
        {
            "status": "alive",
            "timestamp": "2025-10-22T12:00:00.000Z"
        }
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime": "application is running"
    }
