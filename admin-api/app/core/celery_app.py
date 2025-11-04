"""
Celery Application Configuration
Fine-tuning 작업 큐를 위한 Celery 설정

설정:
- Broker: Redis
- Result Backend: Redis
- Task Serializer: JSON
- Result Serializer: JSON
"""
import os
from celery import Celery

# Redis 설정
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Celery app 생성
celery_app = Celery(
    "finetuning_mlops",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'app.workers.finetuning_worker'
    ]
)

# Celery 설정
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=86400,  # 24 hours
    task_soft_time_limit=82800,  # 23 hours

    # Result backend
    result_expires=3600,  # 1 hour
    result_persistent=True,

    # Worker
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,

    # Retry
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s',
)
