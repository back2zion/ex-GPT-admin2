from fastapi import APIRouter
from app.api.endpoints import auth, documents, usage, permissions, notices, satisfaction

api_router = APIRouter()

# 각 엔드포인트 등록
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(usage.router, prefix="/usage", tags=["Usage History"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
api_router.include_router(notices.router, prefix="/notices", tags=["Notices"])
api_router.include_router(satisfaction.router, prefix="/satisfaction", tags=["Satisfaction Survey"])
