from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SatisfactionResponse(BaseModel):
    """만족도 조사 응답 스키마"""
    id: int
    user_id: str
    rating: int = Field(..., ge=1, le=5, description="평점 (1-5)")
    feedback: Optional[str] = None
    category: Optional[str] = None
    related_question_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
