"""
GPT 통계 스키마
"""
from pydantic import BaseModel, Field
from typing import List


class DepartmentStatsResponse(BaseModel):
    """부서별 GPT 접근 권한 통계"""
    id: int = Field(..., description="부서 ID")
    name: str = Field(..., description="부서명")
    code: str = Field(..., description="부서 코드")
    total_users: int = Field(..., description="전체 사용자 수")
    users_with_gpt_access: int = Field(..., description="GPT 접근 권한 보유 사용자 수")
    access_rate: float = Field(..., description="접근 권한 비율 (%)")

    class Config:
        from_attributes = True


class DepartmentStatsListResponse(BaseModel):
    """부서별 통계 목록 응답"""
    departments: List[DepartmentStatsResponse]
    total_departments: int
    total_users: int
    total_users_with_access: int


class ModelDistributionResponse(BaseModel):
    """모델별 사용자 분포"""
    model: str = Field(..., description="모델명")
    user_count: int = Field(..., description="사용자 수")
    percentage: float = Field(..., description="비율 (%)")


class ModelDistributionListResponse(BaseModel):
    """모델별 분포 목록 응답"""
    models: List[ModelDistributionResponse]
    total_users_with_access: int
