# STT Integration Architecture

## Overview

Integration between Admin API and ex-GPT-STT for large-scale audio transcription and meeting minutes generation.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Admin API (FastAPI)                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │ STT Router   │   │ STT Service  │   │ STT Client   │        │
│  │ (API Layer)  │──▶│ (Business)   │──▶│ (ex-GPT-STT) │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
│         │                   │                   │                │
│         │                   ▼                   │                │
│         │           ┌──────────────┐            │                │
│         │           │  PostgreSQL  │            │                │
│         │           │  (Progress)  │            │                │
│         │           └──────────────┘            │                │
│         ▼                                       │                │
│  ┌──────────────┐                               │                │
│  │ Background   │                               │                │
│  │ Job Queue    │                               │                │
│  └──────────────┘                               │                │
└────────────────────────────────────────────────┼────────────────┘
                                                   │
                                                   │ HTTP API
                                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ex-GPT-STT API Server                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │ FastAPI      │   │ Faster       │   │ vLLM/Ollama  │        │
│  │ Server       │──▶│ Whisper      │──▶│ (Meeting     │        │
│  │ (Port 8001)  │   │ (large-v3)   │   │  Minutes)    │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
│         │                   │                   │                │
│         │                   ▼                   ▼                │
│         │           ┌──────────────┐   ┌──────────────┐        │
│         │           │ Speaker      │   │ Korean Text  │        │
│         │           │ Diarization  │   │ Post-Process │        │
│         │           └──────────────┘   └──────────────┘        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ Email        │                                               │
│  │ Service      │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Admin API Components

#### 1.1 STT Router (`app/routers/admin/stt_batches.py`)
**Status**: ✅ Implemented (271 tests passing)

Endpoints:
- `POST /api/v1/admin/stt-batches` - Create batch
- `GET /api/v1/admin/stt-batches/{id}` - Get batch details
- `GET /api/v1/admin/stt-batches/{id}/progress` - Get progress
- `GET /api/v1/admin/stt-batches` - List batches with pagination
- `PUT /api/v1/admin/stt-batches/{id}` - Update batch (pause/resume)
- `DELETE /api/v1/admin/stt-batches/{id}` - Delete batch

#### 1.2 STT Service (`app/services/stt_service.py`)
**Status**: ✅ Implemented with security

Features:
- Path Traversal prevention (whitelist patterns)
- SQL Injection prevention (parameterized queries)
- File size limits (1GB max, DoS prevention)
- Email validation (SMTP injection prevention)
- Progress calculation
- Batch search

**To Add**:
- Background job processing
- Integration with STT Client
- Email notification on completion

#### 1.3 STT Client Service (`app/services/stt_client_service.py`)
**Status**: ⏳ To Implement

Purpose: HTTP client to communicate with ex-GPT-STT API

Methods:
```python
class STTClientService:
    async def submit_audio(
        audio_file_path: str,
        meeting_title: str,
        sender_name: str
    ) -> dict:
        """Submit audio file to ex-GPT-STT for processing"""

    async def get_task_status(task_id: str) -> dict:
        """Check processing status of a task"""

    async def get_task_result(task_id: str) -> dict:
        """Retrieve completed transcription and meeting minutes"""
```

#### 1.4 Background Job Processor
**Status**: ⏳ To Implement

Options:
1. **FastAPI BackgroundTasks** (Recommended for MVP)
   - Simple, no extra dependencies
   - Good for small-scale batches (<1000 files)
   - No separate worker processes needed

2. **Celery + Redis** (For production scale)
   - Robust for 500만건 scale
   - Distributed workers
   - Retry logic, monitoring
   - Requires Redis setup

**Recommended**: Start with BackgroundTasks, migrate to Celery when needed

### 2. ex-GPT-STT API Server

#### 2.1 Existing Components (✅ Already Implemented)

File: `/home/aigen/ex-GPT-STT/src/api/api_server.py`

Endpoints:
- `POST /process-audio` - Upload and process audio file
- `GET /status/{task_id}` - Check task status
- `GET /result/{task_id}` - Get transcription results
- `GET /health` - Health check

Processing Pipeline:
1. **Audio Upload** → Save to temp directory
2. **Faster Whisper STT** → Transcribe with Korean optimization
3. **Korean Post-Processing** → Text correction
4. **Speaker Diarization** → Time-based speaker separation
5. **AI Analysis** → vLLM (Qwen3-32B) or Ollama (qwen3:8b)
6. **Meeting Minutes** → Structured format
7. **Email Notification** → Send to recipients

### 3. Database Schema

#### 3.1 STT Tables (✅ Implemented)

**stt_batches** - Batch processing metadata
```sql
id SERIAL PRIMARY KEY
name VARCHAR(255) NOT NULL
source_path VARCHAR(500) NOT NULL
total_files INTEGER DEFAULT 0
status VARCHAR(20) DEFAULT 'pending'
priority VARCHAR(10) DEFAULT 'normal'
created_by VARCHAR(100)
created_at TIMESTAMP
```

**stt_transcriptions** - Individual file transcriptions
```sql
id SERIAL PRIMARY KEY
batch_id INTEGER REFERENCES stt_batches(id)
audio_file_path VARCHAR(500) UNIQUE NOT NULL
transcription_text TEXT NOT NULL
speaker_labels JSONB
segments JSONB
status VARCHAR(20)
created_at TIMESTAMP
```

**stt_summaries** - AI-generated meeting minutes
```sql
id SERIAL PRIMARY KEY
transcription_id INTEGER REFERENCES stt_transcriptions(id)
summary_text TEXT NOT NULL
keywords TEXT[]
action_items JSONB
llm_model VARCHAR(50)
tokens_used INTEGER
created_at TIMESTAMP
```

**stt_email_logs** - Email notification tracking
```sql
id SERIAL PRIMARY KEY
summary_id INTEGER REFERENCES stt_summaries(id)
recipient_email VARCHAR(255)
status VARCHAR(20)
sent_at TIMESTAMP
delivery_status VARCHAR(50)
```

#### 3.2 New Fields to Add

**stt_transcriptions** table:
```sql
ALTER TABLE stt_transcriptions ADD COLUMN ex_gpt_task_id VARCHAR(100);
ALTER TABLE stt_transcriptions ADD COLUMN processing_started_at TIMESTAMP;
ALTER TABLE stt_transcriptions ADD COLUMN processing_completed_at TIMESTAMP;
ALTER TABLE stt_transcriptions ADD COLUMN processing_duration FLOAT;
```

## Integration Workflow

### Scenario: Process 500만건 Audio Files

#### Step 1: Create Batch (User Action)
```
User → Admin UI → POST /api/v1/admin/stt-batches
{
  "name": "2024년 12월 총무처 회의록",
  "source_path": "s3://audio-files/2024-12/",
  "file_pattern": "*.mp3",
  "priority": "high",
  "notify_emails": ["admin@ex.co.kr"]
}
```

Response:
```json
{
  "id": 12345,
  "status": "pending",
  "total_files": 5000000
}
```

#### Step 2: Background Job Starts
```python
async def process_batch_background(batch_id: int):
    # 1. Scan source_path for audio files
    files = await scan_audio_files(batch.source_path, batch.file_pattern)

    # 2. Update batch total_files
    await update_batch(batch_id, total_files=len(files))

    # 3. Process files in chunks (e.g., 100 at a time)
    for chunk in chunks(files, 100):
        await process_chunk(batch_id, chunk)
```

#### Step 3: Process Each File
```python
async def process_file(batch_id: int, file_path: str):
    # 1. Submit to ex-GPT-STT
    result = await stt_client.submit_audio(
        audio_file_path=file_path,
        meeting_title=Path(file_path).stem,
        sender_name="Auto Batch"
    )

    # 2. Create transcription record
    transcription = STTTranscription(
        batch_id=batch_id,
        audio_file_path=file_path,
        ex_gpt_task_id=result["task_id"],
        status="processing"
    )
    db.add(transcription)
    await db.commit()

    # 3. Poll for completion (or use webhook)
    while True:
        status = await stt_client.get_task_status(result["task_id"])
        if status["status"] == "completed":
            break
        await asyncio.sleep(5)

    # 4. Store results
    task_result = await stt_client.get_task_result(result["task_id"])
    transcription.transcription_text = task_result["transcription"]
    transcription.status = "success"
    await db.commit()

    # 5. Create summary
    summary = STTSummary(
        transcription_id=transcription.id,
        summary_text=task_result["meeting_minutes"],
        llm_model=task_result.get("llm_model", "unknown")
    )
    db.add(summary)
    await db.commit()
```

#### Step 4: Progress Tracking
```python
# Realtime progress via API
GET /api/v1/admin/stt-batches/12345/progress

Response:
{
  "batch_id": 12345,
  "status": "processing",
  "total_files": 5000000,
  "completed": 3250000,
  "failed": 1250,
  "pending": 1748750,
  "progress_percentage": 65.0,
  "avg_processing_time": 12.5,  # seconds per file
  "estimated_completion": "2025-10-23T14:30:00Z"
}
```

#### Step 5: Completion & Email
```python
async def on_batch_complete(batch_id: int):
    batch = await get_batch(batch_id)
    batch.status = "completed"
    await db.commit()

    # Send email notification
    if batch.notify_emails:
        await send_batch_completion_email(
            emails=batch.notify_emails,
            batch_name=batch.name,
            total_files=batch.total_files,
            completed=batch.completed_files,
            failed=batch.failed_files
        )
```

## Security Considerations

### ✅ Already Implemented

1. **Path Traversal Prevention**
   - Whitelist patterns for file paths
   - Reject `..`, `/../`, etc.

2. **SQL Injection Prevention**
   - Parameterized queries via SQLAlchemy ORM
   - No raw SQL concatenation

3. **Email Injection Prevention**
   - Email regex validation (RFC 5322)
   - Forbidden characters check (\n, \r, \0)

4. **DoS Prevention**
   - File size limits (1GB max)
   - Rate limiting (recommended, not yet implemented)

### 🔄 To Implement

5. **Authentication & Authorization**
   - API key for ex-GPT-STT calls
   - RBAC for batch operations (already exists via Cerbos)

6. **Rate Limiting**
   - Limit concurrent batch processing
   - Throttle ex-GPT-STT API calls

7. **Resource Limits**
   - Max concurrent jobs
   - Memory/CPU limits per worker

## Performance Optimization

### 1. Batch Processing Strategy

**Small Batches (<1000 files)**:
- Sequential processing
- FastAPI BackgroundTasks
- Single worker

**Medium Batches (1000-100k files)**:
- Parallel processing (10-50 concurrent)
- Celery with 5-10 workers
- Progress tracking every 100 files

**Large Batches (100k-500만 files)**:
- Chunked parallel processing (100 files per chunk)
- Celery with 50+ distributed workers
- Redis for task queue
- Progress tracking every 1000 files
- Batch status dashboard

### 2. ex-GPT-STT Optimization

- **GPU Acceleration**: Faster Whisper on CUDA
- **Batch Inference**: Process multiple audio chunks together
- **VAD Filtering**: Skip silence in audio
- **Model Caching**: Keep Whisper model in memory

### 3. Database Optimization

- **Indexing**:
  ```sql
  CREATE INDEX idx_batch_status ON stt_batches(status);
  CREATE INDEX idx_transcription_batch ON stt_transcriptions(batch_id);
  CREATE INDEX idx_transcription_status ON stt_transcriptions(status);
  ```

- **Partitioning**: For 500만건+ scale
  ```sql
  CREATE TABLE stt_transcriptions_2024_12
  PARTITION OF stt_transcriptions
  FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');
  ```

## Testing Strategy

### Unit Tests (✅ 271 passing)

- STT Service methods
- Path validation
- Email validation
- Progress calculation

### Integration Tests (⏳ To Add)

- ex-GPT-STT API client
- Background job processing
- Email sending
- End-to-end batch flow

### Load Tests (⏳ To Add)

- 1000 concurrent file processing
- Progress tracking accuracy
- Database query performance

## Deployment

### Development
```bash
# Terminal 1: Start ex-GPT-STT API
cd /home/aigen/ex-GPT-STT
python src/api/api_server.py

# Terminal 2: Start Admin API
cd /home/aigen/admin-api
docker compose up admin-api

# Terminal 3: Start Celery worker (when implemented)
celery -A app.workers.celery_app worker --loglevel=info
```

### Production
```yaml
# docker-compose.yml
services:
  admin-api:
    build: ./admin-api
    ports:
      - "8010:8010"
    depends_on:
      - postgres
      - redis
      - stt-api

  stt-api:
    build: ./ex-GPT-STT
    ports:
      - "8001:8001"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]

  celery-worker:
    build: ./admin-api
    command: celery -A app.workers.celery_app worker
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 10  # Scale for 500만건 processing

  redis:
    image: redis:7-alpine

  postgres:
    image: postgres:15-alpine
```

## Next Steps (Priority Order)

1. ✅ **STT Models & Service** - DONE (271 tests passing)
2. ✅ **STT API Endpoints** - DONE (9/9 tests passing)
3. ⏳ **STT Client Service** - Create HTTP client for ex-GPT-STT
4. ⏳ **Background Jobs** - Implement batch processing
5. ⏳ **Progress Tracking** - Real-time updates
6. ⏳ **Email Notifications** - Completion alerts
7. ⏳ **Monitoring Dashboard** - Real-time batch status
8. ⏳ **Load Testing** - Verify 500만건 scale

## References

- [PRD_STT_SYSTEM.md](../PRD_STT_SYSTEM.md) - Product requirements
- [TECH_DECISION.md](../TECH_DECISION.md) - Technical decisions
- [ex-GPT-STT CLAUDE.md](/home/aigen/ex-GPT-STT/CLAUDE.md) - STT implementation details
