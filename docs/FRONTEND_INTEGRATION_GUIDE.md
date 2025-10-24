# Frontend Integration Guide - FastAPI Backend

**Date**: 2025-10-22
**Status**: Week 3 Day 15 Complete
**Backend**: FastAPI (admin-api)
**Frontend**: React 19 + Vite

---

## 📋 Overview

This guide explains how to integrate the React frontend with the FastAPI backend for the chat system.

### Key Changes

| Component | Old (Spring Boot) | New (FastAPI) |
|-----------|------------------|---------------|
| **Chat API** | `/api/chat/conversation` | `/api/v1/chat/send` (SSE) |
| **History List** | `POST /api/chat/history/list` | `POST /api/v1/history/list` |
| **History Detail** | `POST /api/history/getDetailHistory` | `GET /api/v1/history/{room_id}` |
| **File Upload** | `/v1/addFile` | `POST /api/v1/files/upload` |
| **Authentication** | Spring Security SSO | HTTP Session (Cookies) |
| **Streaming** | N/A | SSE (Server-Sent Events) |

---

## 🔧 API Client Files

### Updated Files

1. **`chat_updated.js`** - Chat API with SSE streaming
2. **`history_updated.js`** - History API with pagination
3. **`file_updated.js`** - File upload/download API

### Installation

**Option 1**: Replace existing files
```bash
cd /home/aigen/new-exgpt-feature-chat/new-exgpt-ui/src/components/api/
cp chat_updated.js chat.js
cp history_updated.js history.js
cp file_updated.js file.js
```

**Option 2**: Import from updated files
```javascript
// In your components
import { sendChatWithSSE } from '../api/chat_updated';
import { getHistoryList, getDetailHistory } from '../api/history_updated';
import { uploadFile } from '../api/file_updated';
```

---

## 💬 Chat API Usage

### SSE Streaming (Recommended)

```javascript
import { sendChatWithSSE } from '../api/chat_updated';
import { useRoomId } from '../store/roomIdStore';

function ChatComponent() {
  const { roomId, setCurrentRoomId } = useRoomId();
  const [messages, setMessages] = useState([]);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const handleSendMessage = async (userMessage) => {
    setIsStreaming(true);
    setCurrentAnswer('');

    try {
      const abort = await sendChatWithSSE(
        [], // file_ids (optional)
        userMessage,
        roomId, // null for new conversation
        {
          // 1. Room created (첫 메시지)
          onRoomCreated: (newRoomId) => {
            console.log('Room created:', newRoomId);
            setCurrentRoomId(newRoomId);
          },

          // 2. Token received (실시간 응답)
          onToken: (token) => {
            setCurrentAnswer(prev => prev + token);
          },

          // 3. Metadata received (참고 문서, 토큰 수 등)
          onMetadata: (metadata) => {
            console.log('Metadata:', metadata);
            // metadata.sources - 참고 문서
            // metadata.tokens_used - 토큰 수
            // metadata.response_time_ms - 응답 시간
          },

          // 4. Complete (스트리밍 완료)
          onComplete: () => {
            console.log('Streaming complete');
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: currentAnswer
            }]);
            setCurrentAnswer('');
            setIsStreaming(false);
          },

          // 5. Error
          onError: (error) => {
            console.error('Streaming error:', error);
            alert(`에러 발생: ${error.message}`);
            setIsStreaming(false);
          }
        }
      );

      // Store abort function for cancellation
      // abortRef.current = abort;

    } catch (err) {
      console.error('Send message error:', err);
      alert(`메시지 전송 실패: ${err.message}`);
      setIsStreaming(false);
    }
  };

  return (
    <div>
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={msg.role}>
            {msg.content}
          </div>
        ))}
        {currentAnswer && (
          <div className="assistant streaming">
            {currentAnswer}
            <span className="cursor">|</span>
          </div>
        )}
      </div>
      <input
        type="text"
        onKeyPress={(e) => {
          if (e.key === 'Enter' && !isStreaming) {
            handleSendMessage(e.target.value);
            e.target.value = '';
          }
        }}
        disabled={isStreaming}
      />
    </div>
  );
}
```

### JSON Response (Fallback)

```javascript
import { sendChatJSON } from '../api/chat_updated';

const response = await sendChatJSON([], "안녕하세요", roomId);
console.log(response.content.response); // Full response text
```

---

## 📜 History API Usage

### List Conversations

```javascript
import { getHistoryList } from '../api/history_updated';

function HistoryList() {
  const [conversations, setConversations] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    loadHistory();
  }, [currentPage]);

  const loadHistory = async () => {
    try {
      const result = await getHistoryList(currentPage, 10);
      setConversations(result.items);
      setTotalPages(result.total_pages);
    } catch (err) {
      console.error('Load history error:', err);
    }
  };

  return (
    <div>
      {conversations.map(conv => (
        <div key={conv.cnvs_idt_id}>
          <h3>{conv.cnvs_smry_txt}</h3>
          <p>{new Date(conv.reg_dt).toLocaleString()}</p>
        </div>
      ))}
      <Pagination
        current={currentPage}
        total={totalPages}
        onChange={setCurrentPage}
      />
    </div>
  );
}
```

### Get Conversation Detail

```javascript
import { getDetailHistory } from '../api/history_updated';

const loadConversation = async (roomId) => {
  try {
    const detail = await getDetailHistory(roomId);
    console.log('Room:', detail.cnvs_idt_id);
    console.log('Summary:', detail.cnvs_smry_txt);
    console.log('Messages:', detail.messages);

    detail.messages.forEach(msg => {
      console.log('Q:', msg.ques_txt);
      console.log('A:', msg.ans_txt);
    });
  } catch (err) {
    if (err.message.includes('찾을 수 없습니다')) {
      alert('대화가 존재하지 않습니다');
    } else if (err.message.includes('권한')) {
      alert('접근 권한이 없습니다');
    } else {
      alert(`에러: ${err.message}`);
    }
  }
};
```

### Update Room Name

```javascript
import { updateRoomName } from '../api/history_updated';

const renameRoom = async (roomId, newName) => {
  try {
    await updateRoomName(roomId, newName);
    alert('이름이 변경되었습니다');
  } catch (err) {
    alert(`이름 변경 실패: ${err.message}`);
  }
};
```

### Delete Room

```javascript
import { deleteRoom } from '../api/history_updated';

const handleDelete = async (roomId) => {
  if (!confirm('정말 삭제하시겠습니까?')) return;

  try {
    await deleteRoom(roomId);
    alert('삭제되었습니다');
    // Refresh list
  } catch (err) {
    alert(`삭제 실패: ${err.message}`);
  }
};
```

---

## 📁 File Upload API Usage

### Single File Upload

```javascript
import { uploadFile } from '../api/file_updated';

function FileUploader({ roomId }) {
  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const result = await uploadFile(file, roomId);
      console.log('Uploaded:', result);
      alert(`파일 업로드 완료: ${result.file_name}`);
    } catch (err) {
      alert(`업로드 실패: ${err.message}`);
    }
  };

  return (
    <input
      type="file"
      onChange={handleFileSelect}
      accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.hwp,.hwpx,.txt,.png,.jpg,.jpeg"
    />
  );
}
```

### Multiple Files Upload

```javascript
import { uploadMultipleFiles } from '../api/file_updated';

const handleMultipleFiles = async (files, roomId) => {
  try {
    const results = await uploadMultipleFiles(files, roomId);
    console.log(`${results.length}개 파일 업로드 성공`);
    return results.map(r => r.file_id); // Return file IDs
  } catch (err) {
    console.error('Upload error:', err);
  }
};
```

### File Download

```javascript
import { getFileDownloadUrl } from '../api/file_updated';

function FileList({ files }) {
  const handleDownload = (fileId, fileName) => {
    const url = getFileDownloadUrl(fileId);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    link.click();
  };

  return (
    <ul>
      {files.map(file => (
        <li key={file.file_id}>
          {file.file_name}
          <button onClick={() => handleDownload(file.file_id, file.file_name)}>
            다운로드
          </button>
        </li>
      ))}
    </ul>
  );
}
```

---

## 🏪 Zustand Store Integration

### Room ID Store (Already Exists)

```javascript
// src/components/store/roomIdStore.js
import { create } from 'zustand';

export const useRoomId = create(set => ({
  roomId: '',
  setCurrentRoomId: id => set({ roomId: id }),
  clearRoomId: () => set({ roomId: '' })
}));
```

**Usage:**
```javascript
import { useRoomId } from '../store/roomIdStore';

function ChatPage() {
  const { roomId, setCurrentRoomId } = useRoomId();

  // When room is created
  const handleRoomCreated = (newRoomId) => {
    setCurrentRoomId(newRoomId);
  };

  // When starting new conversation
  const handleNewChat = () => {
    setCurrentRoomId('');
  };

  return (
    <div>
      <h1>Current Room: {roomId || 'New Chat'}</h1>
      <button onClick={handleNewChat}>새 대화</button>
    </div>
  );
}
```

---

## 🔐 Authentication

### Session-based Auth

The backend uses **HTTP Session** authentication with cookies. No manual token management is needed.

**Requirements:**
1. Include `credentials: 'include'` in all fetch requests ✅ (Already implemented)
2. Backend sets `JSESSIONID` cookie on login
3. Browser automatically sends cookie with subsequent requests

**Login Flow:**
```javascript
// Login endpoint (if implemented)
const login = async (username, password) => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // Important!
    body: JSON.stringify({ username, password })
  });

  if (response.ok) {
    // Session cookie is automatically set
    // Redirect to chat page
    window.location.href = '/chat';
  } else {
    alert('로그인 실패');
  }
};
```

**401 Handling:**
All API clients automatically redirect to login on 401 Unauthorized:
```javascript
if (response.status === 401) {
  throw new Error('인증이 필요합니다');
  // Frontend should redirect to login page
}
```

---

## 🧪 Testing

### Manual Testing Steps

1. **Start Backend**
   ```bash
   cd /home/aigen/admin-api
   docker compose up -d
   ```

2. **Start Frontend**
   ```bash
   cd /home/aigen/new-exgpt-feature-chat/new-exgpt-ui
   npm run dev
   ```

3. **Test Chat**
   - Open browser to `http://localhost:5173`
   - Send first message → Check room_id creation
   - Send follow-up message → Check message continuity
   - Verify SSE streaming works

4. **Test History**
   - View conversation list
   - Click on conversation → Load details
   - Rename conversation
   - Delete conversation

5. **Test File Upload**
   - Upload PDF file
   - Verify file appears in chat
   - Download file

---

## ⚠️ Common Issues

### 1. CORS Errors

**Symptom**: `Access-Control-Allow-Origin` error in console

**Solution**: Backend needs CORS configuration
```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Session Cookie Not Sent

**Symptom**: 401 Unauthorized on every request

**Solution**: Check `credentials: 'include'` in fetch

### 3. SSE Connection Closed Early

**Symptom**: Streaming stops after a few tokens

**Solution**: Check reverse proxy (Nginx) buffering settings
```nginx
proxy_buffering off;
proxy_set_header X-Accel-Buffering no;
```

### 4. File Upload 413 Error

**Symptom**: Large files fail with 413 Payload Too Large

**Solution**: Increase Nginx max body size
```nginx
client_max_body_size 100M;
```

---

## 📊 API Response Formats

### Chat SSE Stream

```
data: {"type": "room_created", "room_id": "user123_20251022104412345678"}

data: {"type": "token", "content": {"response": "안녕하세요"}}

data: {"type": "token", "content": {"response": "무엇을"}}

data: {"type": "metadata", "metadata": {"tokens_used": 123, "response_time_ms": 1500}}

data: {"type": "sources", "sources": [{"filename": "doc.pdf", "relevance_score": 0.95}]}

data: [DONE]
```

### History List Response

```json
{
  "items": [
    {
      "cnvs_idt_id": "user123_20251022104412345678",
      "cnvs_smry_txt": "대화 제목",
      "reg_dt": "2025-10-22T10:44:12",
      "mod_dt": "2025-10-22T11:30:00"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 10,
  "total_pages": 3
}
```

### History Detail Response

```json
{
  "cnvs_idt_id": "user123_20251022104412345678",
  "cnvs_smry_txt": "대화 제목",
  "messages": [
    {
      "cnvs_id": 1,
      "ques_txt": "사용자 질문",
      "ans_txt": "AI 답변",
      "tkn_use_cnt": 123,
      "rsp_tim_ms": 1500,
      "reg_dt": "2025-10-22T10:44:12"
    }
  ],
  "total_messages": 1
}
```

### File Upload Response

```json
{
  "file_id": 123,
  "cnvs_idt_id": "user123_20251022104412345678",
  "file_name": "document.pdf",
  "file_path": "chat-uploads/user123/20251022/document_abc123.pdf",
  "file_size": 1048576,
  "upload_dt": "2025-10-22T10:44:12"
}
```

---

## 📝 Next Steps

1. **Day 16**: Verify Zustand store persistence (if needed)
2. **Day 17**: E2E testing with actual backend
3. **Day 18**: Security testing (OWASP Top 10)
4. **Day 19**: Performance optimization (response time < 2s)
5. **Day 20-21**: Production deployment

---

## 📚 References

- Backend API Spec: `/home/aigen/admin-api/app/routers/chat/`
- Test Files: `/home/aigen/admin-api/tests/chat/`
- Week 2 Report: `/home/aigen/admin-api/docs/WEEK2_COMPLETION_REPORT.md`
- Final Status: `/home/aigen/admin-api/docs/FINAL_STATUS_REPORT.md`
