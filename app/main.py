from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.api import api_router
from app.routers.admin import (
    notices,
    usage,
    satisfaction,
    export,
    departments,
    roles,
    permissions,
    approval_lines,
    document_permissions,
    users,
    statistics,
    conversations,
    gpt_access,
    user_document_permissions,
    pii_detections,
    ip_whitelist,
    access_requests
)
import os

app = FastAPI(
    title="AI Streams Admin API",
    description="Enterprise AI Platform Management System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Admin 라우터 등록 (MVP)
app.include_router(notices.router)
app.include_router(usage.router)
app.include_router(satisfaction.router)
app.include_router(export.router)
app.include_router(statistics.router)
app.include_router(conversations.router)

# Admin 라우터 등록 (Phase 2 - 권한 관리)
app.include_router(departments.router)
app.include_router(roles.router)
app.include_router(permissions.router)
app.include_router(approval_lines.router)
app.include_router(document_permissions.router)
app.include_router(users.router)
app.include_router(gpt_access.router)
app.include_router(user_document_permissions.router)

# Admin 라우터 등록 (P0 - PII Detection, IP Whitelist, Access Requests)
app.include_router(pii_detections.router)
app.include_router(ip_whitelist.router)
app.include_router(access_requests.router)

# 정적 파일 제공 (관리자 페이지)
admin_path = "/home/aigen/html/admin"
if os.path.exists(admin_path):
    app.mount("/admin/static", StaticFiles(directory=f"{admin_path}"), name="admin-static")

    @app.get("/admin")
    @app.get("/admin/")
    async def admin_dashboard():
        return FileResponse(f"{admin_path}/index.html")

@app.get("/")
async def root():
    return {
        "message": "AI Streams Admin API",
        "version": "0.1.0",
        "docs": "/docs",
        "admin": "/admin"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
