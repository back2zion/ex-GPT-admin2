"""
Public-facing API - User Chat Service Only
Security-isolated from admin APIs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import chat_proxy

app = FastAPI(
    title="ex-GPT Chat API",
    description="Public chat service for end users",
    version="0.1.0",
    docs_url=None,  # Disable docs for public API
    redoc_url=None
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chat Proxy 라우터만 등록 (사용자용)
app.include_router(chat_proxy.router)

@app.get("/")
async def root():
    return {
        "message": "ex-GPT Chat API",
        "version": "0.1.0",
        "service": "public"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "public-chat"}
