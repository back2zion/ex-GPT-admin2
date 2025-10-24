# Zustand Store Usage Guide - Enhanced Version

**Date**: 2025-10-22
**Status**: Day 16 Complete
**Version**: 2.0 (Enhanced with Persistence & Security)

---

## 📋 Overview

Enhanced Zustand stores with:
- ✅ **Persistence**: localStorage support (optional)
- ✅ **Security**: XSS prevention, input validation
- ✅ **Memory Management**: Message/file limits
- ✅ **Error Handling**: Graceful fallbacks
- ✅ **Type Safety**: Validation for all inputs

---

## 🏪 Enhanced Stores

### 1. Room ID Store

**File**: `roomIdStore_enhanced.js`

**Features**:
- ✅ Automatic persistence to localStorage
- ✅ Room ID format validation
- ✅ XSS/Path traversal prevention
- ✅ Quota exceeded handling

**Usage**:

```javascript
import { useRoomId } from './store/roomIdStore_enhanced';

function ChatComponent() {
  const { roomId, setCurrentRoomId, clearRoomId, hasRoomId } = useRoomId();

  // Set room ID (with validation)
  const handleRoomCreated = (newRoomId) => {
    const success = setCurrentRoomId(newRoomId);
    if (success) {
      console.log('Room ID set:', newRoomId);
    } else {
      console.error('Invalid room ID format');
    }
  };

  // Clear room ID
  const handleNewChat = () => {
    clearRoomId();
  };

  // Check if room exists
  if (hasRoomId()) {
    console.log('Continuing conversation:', roomId);
  } else {
    console.log('Starting new conversation');
  }

  return (
    <div>
      <h1>Room: {roomId || 'New Chat'}</h1>
      <button onClick={handleNewChat}>New Chat</button>
    </div>
  );
}
```

**API**:
```typescript
interface RoomIdStore {
  roomId: string;

  // Initialize from localStorage (auto-called on load)
  initRoomId: () => void;

  // Set room ID with validation (returns true on success)
  setCurrentRoomId: (id: string) => boolean;

  // Clear room ID and localStorage
  clearRoomId: () => void;

  // Get current room ID
  getCurrentRoomId: () => string;

  // Check if room ID exists
  hasRoomId: () => boolean;
}
```

**Security**:
```javascript
// ✅ Valid room IDs
setCurrentRoomId('user123_20251022104412345678');  // OK
setCurrentRoomId('admin-session-2024');            // OK

// ❌ Invalid room IDs (rejected)
setCurrentRoomId('<script>alert("XSS")</script>'); // XSS attempt
setCurrentRoomId('../../etc/passwd');              // Path traversal
setCurrentRoomId('a'.repeat(300));                 // Too long
```

---

### 2. Message Store

**File**: `messageStore_enhanced.js`

**Features**:
- ✅ Optional persistence (disabled by default)
- ✅ Message limit (max 100 messages)
- ✅ XSS prevention (HTML sanitization)
- ✅ Message length limits (50KB per message)
- ✅ Export/Import functionality

**Usage**:

```javascript
import { useMessageStore } from './store/messageStore_enhanced';

function ChatComponent() {
  const {
    messages,
    addUserMessage,
    addAssistantMessage,
    clearMessages,
    enablePersistence,
    getMessagesCount,
    exportMessages
  } = useMessageStore();

  // Enable persistence (optional)
  useEffect(() => {
    enablePersistence(true);  // Persist messages to localStorage
  }, []);

  // Add user message
  const handleSend = (userInput) => {
    addUserMessage(userInput);
  };

  // Add assistant message
  const handleResponse = (chatData) => {
    addAssistantMessage(chatData);
  };

  // Export chat history
  const handleExport = () => {
    const json = exportMessages();
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    // Download...
  };

  return (
    <div>
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={msg.role}>
            {msg.content}
          </div>
        ))}
      </div>
      <p>Total messages: {getMessagesCount()}</p>
      <button onClick={() => clearMessages()}>Clear History</button>
      <button onClick={handleExport}>Export Chat</button>
    </div>
  );
}
```

**API**:
```typescript
interface MessageStore {
  messages: Array<{
    role: 'user' | 'assistant';
    content: string;
    raw?: any;  // Original data (assistant only)
    timestamp: number;
  }>;
  persistenceEnabled: boolean;

  // Initialize from localStorage (if enabled)
  initMessages: () => void;

  // Enable/disable persistence
  enablePersistence: (enabled: boolean) => void;

  // Add user message (with validation)
  addUserMessage: (content: string) => void;

  // Add assistant message (with sanitization)
  addAssistantMessage: (chatData: any) => void;

  // Update last assistant message (for streaming)
  updateLastAssistantMessage: (content: string) => void;

  // Clear all messages
  clearMessages: () => void;

  // Get messages count
  getMessagesCount: () => number;

  // Get recent N messages
  getRecentMessages: (count?: number) => Array<Message>;

  // Export messages as JSON
  exportMessages: () => string;

  // Import messages from JSON
  importMessages: (jsonString: string) => boolean;
}
```

**Security Features**:
```javascript
// ✅ XSS Prevention
addUserMessage('<script>alert("XSS")</script>');
// Stored as: '&lt;script&gt;alert("XSS")&lt;/script&gt;'

// ✅ Length Limit
const longMessage = 'a'.repeat(100000);
addUserMessage(longMessage);
// Truncated to 50KB: 'aaa... (truncated)'

// ✅ Message Limit
for (let i = 0; i < 200; i++) {
  addUserMessage(`Message ${i}`);
}
// Only last 100 messages kept
```

---

### 3. File Store

**File**: `fileStore_enhanced.js`

**Features**:
- ✅ File type validation (whitelist)
- ✅ File size limits (100MB per file)
- ✅ Duplicate prevention
- ✅ Max 10 files at once
- ✅ Path traversal prevention

**Usage**:

```javascript
import { useFileStore } from './store/fileStore_enhanced';

function FileUploader() {
  const {
    attachedFiles,
    addFiles,
    removeFile,
    resetFiles,
    getTotalSize,
    getFormattedTotalSize,
    isLimitReached,
    getUploadErrors,
    clearUploadErrors
  } = useFileStore();

  const handleFileSelect = (e) => {
    const files = e.target.files;
    const result = addFiles(files);

    if (result.success.length > 0) {
      console.log(`Added ${result.success.length} files`);
    }

    if (result.failed.length > 0) {
      result.failed.forEach(({ file, error }) => {
        alert(`Failed to add ${file.name}: ${error}`);
      });
    }
  };

  return (
    <div>
      <input
        type="file"
        multiple
        onChange={handleFileSelect}
        accept=".pdf,.docx,.xlsx,.txt,.png,.jpg,.jpeg"
        disabled={isLimitReached()}
      />

      <div>
        <strong>Attached Files ({attachedFiles.length}/10):</strong>
        <ul>
          {attachedFiles.map((file, idx) => (
            <li key={idx}>
              {file.name} ({(file.size / 1024).toFixed(2)} KB)
              <button onClick={() => removeFile(file)}>Remove</button>
            </li>
          ))}
        </ul>
      </div>

      <p>Total Size: {getFormattedTotalSize()}</p>

      {getUploadErrors().length > 0 && (
        <div className="errors">
          {getUploadErrors().map((err, idx) => (
            <p key={idx}>{err.file.name}: {err.error}</p>
          ))}
          <button onClick={clearUploadErrors}>Clear Errors</button>
        </div>
      )}

      <button onClick={resetFiles}>Clear All</button>
    </div>
  );
}
```

**API**:
```typescript
interface FileStore {
  attachedFiles: Array<File>;
  uploadErrors: Array<{ file: File; error: string }>;

  // Add files with validation
  addFiles: (files: FileList | Array<File>) => {
    success: Array<File>;
    failed: Array<{ file: File; error: string }>;
  };

  // Remove file by object or name, or null to clear all
  removeFile: (file: File | string | null) => void;

  // Reset all files
  resetFiles: () => void;

  // Get file by name
  getFileByName: (filename: string) => File | undefined;

  // Get total size in bytes
  getTotalSize: () => number;

  // Get formatted total size (e.g., "10.5 MB")
  getFormattedTotalSize: () => string;

  // Check if limit reached (10 files)
  isLimitReached: () => boolean;

  // Get upload errors
  getUploadErrors: () => Array<{ file: File; error: string }>;

  // Clear upload errors
  clearUploadErrors: () => void;

  // Validate files (debugging)
  validateFiles: () => Array<{
    name: string;
    size: number;
    type: string;
    validation: { valid: boolean; error?: string };
  }>;
}
```

**Allowed File Types**:
```javascript
// ✅ Documents
.pdf    (application/pdf)
.doc    (MS Word 97-2003)
.docx   (MS Word 2007+)
.xls    (MS Excel 97-2003)
.xlsx   (MS Excel 2007+)
.ppt    (MS PowerPoint 97-2003)
.pptx   (MS PowerPoint 2007+)
.hwp    (Hangul/한글)
.hwpx   (Hangul 2014+/한글 2014+)

// ✅ Text & Images
.txt    (text/plain)
.png    (image/png)
.jpg    (image/jpeg)
.jpeg   (image/jpeg)

// ❌ Not Allowed (Security)
.exe, .sh, .bat, .js, .html, .svg, .zip, .rar, etc.
```

**Security Features**:
```javascript
// ✅ File Type Validation
const result = addFiles([pdfFile, docxFile, exeFile]);
console.log(result.failed); // [{ file: exeFile, error: 'File type not allowed' }]

// ✅ File Size Validation
const largeFile = new File(['...'], 'large.pdf', { type: 'application/pdf', size: 150 * 1024 * 1024 });
const result = addFiles([largeFile]);
console.log(result.failed); // [{ file: largeFile, error: 'File too large: 150.00MB (max 100MB)' }]

// ✅ Path Traversal Prevention
const maliciousFile = new File(['...'], '../../etc/passwd', { type: 'text/plain' });
const result = addFiles([maliciousFile]);
console.log(result.failed); // [{ file: maliciousFile, error: 'Invalid filename (path traversal detected)' }]

// ✅ Duplicate Prevention
addFiles([file1]); // Success
addFiles([file1]); // Failed: 'Duplicate file'
```

---

## 🔄 Migration from Original Stores

### Step 1: Update Imports

**Before**:
```javascript
import { useRoomId } from './store/roomIdStore';
import { useMessageStore } from './store/messageStore';
import { useFileStore } from './store/fileStore';
```

**After**:
```javascript
import { useRoomId } from './store/roomIdStore_enhanced';
import { useMessageStore } from './store/messageStore_enhanced';
import { useFileStore } from './store/fileStore_enhanced';
```

### Step 2: Update Usage (Optional)

**RoomIdStore** - No changes needed (API compatible)

**MessageStore** - Add persistence if needed:
```javascript
// Enable persistence (optional)
useEffect(() => {
  useMessageStore.getState().enablePersistence(true);
}, []);
```

**FileStore** - Handle validation results:
```javascript
// Before
addFiles(files);

// After (with error handling)
const result = addFiles(files);
if (result.failed.length > 0) {
  result.failed.forEach(({ file, error }) => {
    console.error(`Failed: ${file.name} - ${error}`);
  });
}
```

---

## 🧪 Testing

### Running Tests

```bash
cd /home/aigen/new-exgpt-feature-chat/new-exgpt-ui
npm install vitest --save-dev
npm run test
```

### Test Files Created

1. **`roomIdStore.test.js`** (150 lines)
   - Basic functionality
   - Persistence
   - Validation
   - Security (XSS, path traversal)
   - Edge cases

2. **`messageStore.test.js`** (200 lines)
   - Basic functionality
   - Message ordering
   - Optional persistence
   - Memory management
   - XSS prevention
   - Edge cases

---

## 🔐 Security Best Practices

### 1. Input Validation

All stores validate inputs before storing:
```javascript
// Room ID: alphanumeric, dash, underscore only (max 200 chars)
const ROOM_ID_PATTERN = /^[a-zA-Z0-9_-]{1,200}$/;

// Messages: HTML sanitization + length limit (50KB)
// Files: Type whitelist + size limit (100MB)
```

### 2. XSS Prevention

```javascript
// Bad (vulnerable)
<div dangerouslySetInnerHTML={{ __html: message.content }} />

// Good (safe)
<div>{message.content}</div>  // React auto-escapes
```

### 3. localStorage Security

```javascript
// ✅ DO: Store non-sensitive data only
localStorage.setItem('exGpt-room-id', roomId);

// ❌ DON'T: Store sensitive data
localStorage.setItem('password', password);  // NEVER
localStorage.setItem('token', token);        // NEVER
```

### 4. Memory Management

```javascript
// Automatic limits enforced
MAX_MESSAGES = 100;  // Message store
MAX_FILES = 10;      // File store
MAX_MESSAGE_LENGTH = 50000;  // 50KB per message
MAX_FILE_SIZE = 100 * 1024 * 1024;  // 100MB per file
```

---

## 📊 Performance Considerations

### LocalStorage Usage

| Store | Size | Persistence | Impact |
|-------|------|-------------|--------|
| **roomIdStore** | ~50B | Always | Minimal |
| **messageStore** | ~5-50KB | Optional | Low |
| **fileStore** | N/A | No | None |
| **userSettingsStore** | ~100B | Always | Minimal |

**Total**: < 100KB (within localStorage limits)

### Memory Usage

| Store | RAM Usage | Notes |
|-------|-----------|-------|
| **messageStore** | ~50KB | Last 100 messages |
| **fileStore** | ~100MB | Max 10 files (refs only) |

---

## 🐛 Common Issues

### Issue 1: Room ID Lost on Refresh

**Symptom**: Room ID disappears after page refresh

**Solution**: Room ID store automatically persists. Ensure you're using `roomIdStore_enhanced.js`

### Issue 2: Messages Not Persisting

**Symptom**: Messages disappear on refresh

**Solution**: Enable persistence explicitly:
```javascript
useMessageStore.getState().enablePersistence(true);
```

### Issue 3: File Upload Rejected

**Symptom**: File upload fails silently

**Solution**: Check validation result:
```javascript
const result = addFiles(files);
console.log(result.failed);  // See why files were rejected
```

### Issue 4: localStorage Quota Exceeded

**Symptom**: Error when saving to localStorage

**Solution**: Stores automatically handle quota errors by:
1. Clearing old data
2. Retrying with reduced data
3. Gracefully degrading if still failing

---

## 📚 References

### Source Files
- `/home/aigen/new-exgpt-feature-chat/new-exgpt-ui/src/components/store/roomIdStore_enhanced.js`
- `/home/aigen/new-exgpt-feature-chat/new-exgpt-ui/src/components/store/messageStore_enhanced.js`
- `/home/aigen/new-exgpt-feature-chat/new-exgpt-ui/src/components/store/fileStore_enhanced.js`

### Test Files
- `/home/aigen/new-exgpt-feature-chat/new-exgpt-ui/src/components/store/__tests__/roomIdStore.test.js`
- `/home/aigen/new-exgpt-feature-chat/new-exgpt-ui/src/components/store/__tests__/messageStore.test.js`

### Related Docs
- `FRONTEND_INTEGRATION_GUIDE.md` - API client usage
- `DAY15_COMPLETION_REPORT.md` - Day 15 completion status

---

**Status**: ✅ Day 16 Complete
**Next**: Day 17 - E2E Testing
