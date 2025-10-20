from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime, timezone

Base = declarative_base()


class TimestampMixin:
    """
    타임스탬프 믹스인

    **Timezone**: UTC로 저장 (timezone-aware datetime)
    - 한국 시간(KST) = UTC + 9시간
    - 응답 시 schema에서 KST로 변환
    """
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
