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
    access_requests,
    stats,
    categories,
    documents
)
from app.routers import chat_proxy
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

# Chat Proxy 라우터 등록 (layout.html용)
app.include_router(chat_proxy.router)

# Admin 라우터 등록 (MVP)
app.include_router(notices.router)
app.include_router(usage.router)
app.include_router(satisfaction.router)
app.include_router(export.router)
app.include_router(statistics.router)
app.include_router(conversations.router)
app.include_router(stats.router)

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

# Admin 라우터 등록 (Vector Data Management - 학습데이터 관리)
app.include_router(categories.router)
app.include_router(documents.router)

# 정적 파일 제공 (React 관리자 페이지)
admin_path = "/home/aigen/html/admin"

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

# React SPA 라우팅 지원 (모든 /admin/* 경로를 index.html로)
if os.path.exists(admin_path):
    # 정적 파일 (js, css, 이미지 등)
    app.mount("/admin/assets", StaticFiles(directory=f"{admin_path}/assets"), name="admin-assets")

    # /admin 루트 경로
    @app.get("/admin")
    @app.get("/admin/")
    async def serve_admin_root():
        """관리자 페이지 루트"""
        return FileResponse(f"{admin_path}/index.html")

    # vite.svg 같은 루트 정적 파일들
    @app.get("/admin/vite.svg")
    async def serve_vite_svg():
        """Vite SVG 아이콘"""
        return FileResponse(f"{admin_path}/vite.svg")

    # Catch-all route: 모든 /admin/* 경로를 index.html로 (SPA 라우팅)
    @app.get("/admin/{full_path:path}")
    async def serve_admin_spa(full_path: str):
        """React SPA의 클라이언트 사이드 라우팅 지원"""
        # 파일이 실제로 존재하면 그 파일을 반환
        file_path = f"{admin_path}/{full_path}"
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        # 그 외의 경우 index.html 반환 (React Router가 처리)
        return FileResponse(f"{admin_path}/index.html")
