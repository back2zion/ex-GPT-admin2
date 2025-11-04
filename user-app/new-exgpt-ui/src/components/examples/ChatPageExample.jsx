/**
 * ChatPage Example - FastAPI Integration
 *
 * Complete example demonstrating:
 * - SSE streaming
 * - Room ID management
 * - File upload
 * - History loading
 * - Error handling
 */

import React, { useState, useEffect, useRef } from 'react';
import { sendChatWithSSE } from '../api/chat_updated';
import { getHistoryList, getDetailHistory, updateRoomName, deleteRoom } from '../api/history_updated';
import { uploadFile, getFileDownloadUrl } from '../api/file_updated';
import { useRoomId } from '../store/roomIdStore';

export default function ChatPageExample() {
  // Room ID management
  const { roomId, setCurrentRoomId, clearRoomId } = useRoomId();

  // Messages state
  const [messages, setMessages] = useState([]);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [metadata, setMetadata] = useState(null);

  // History state
  const [conversations, setConversations] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  // File upload state
  const [uploadedFiles, setUploadedFiles] = useState([]);

  // Refs
  const abortRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentAnswer]);

  // Load conversation history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  // Load history list
  const loadHistory = async () => {
    try {
      const result = await getHistoryList(1, 20);
      setConversations(result.items);
    } catch (err) {
      console.error('Load history error:', err);
    }
  };

  // Load specific conversation
  const loadConversation = async (conversationRoomId) => {
    try {
      const detail = await getDetailHistory(conversationRoomId);
      setCurrentRoomId(conversationRoomId);

      // Convert to message format
      const loadedMessages = [];
      detail.messages.forEach(msg => {
        loadedMessages.push({ role: 'user', content: msg.ques_txt });
        if (msg.ans_txt) {
          loadedMessages.push({ role: 'assistant', content: msg.ans_txt });
        }
      });

      setMessages(loadedMessages);
      setShowHistory(false);
    } catch (err) {
      alert(`대화 불러오기 실패: ${err.message}`);
    }
  };

  // Send message
  const handleSendMessage = async () => {
    const userMessage = inputRef.current.value.trim();
    if (!userMessage || isStreaming) return;

    // Clear input
    inputRef.current.value = '';

    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsStreaming(true);
    setCurrentAnswer('');
    setMetadata(null);

    try {
      abortRef.current = await sendChatWithSSE(
        uploadedFiles.map(f => f.file_id), // File IDs
        userMessage,
        roomId, // null for new conversation
        {
          // Room created (first message)
          onRoomCreated: (newRoomId) => {
            console.log('Room created:', newRoomId);
            setCurrentRoomId(newRoomId);
          },

          // Token received (streaming response)
          onToken: (token) => {
            setCurrentAnswer(prev => prev + token);
          },

          // Metadata received
          onMetadata: (meta) => {
            console.log('Metadata:', meta);
            setMetadata(meta);
          },

          // Complete
          onComplete: () => {
            console.log('Streaming complete');
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: currentAnswer
            }]);
            setCurrentAnswer('');
            setIsStreaming(false);
            setUploadedFiles([]); // Clear uploaded files
            loadHistory(); // Refresh history
          },

          // Error
          onError: (error) => {
            console.error('Streaming error:', error);
            alert(`에러 발생: ${error.message}`);
            setIsStreaming(false);
          }
        }
      );
    } catch (err) {
      console.error('Send message error:', err);
      alert(`메시지 전송 실패: ${err.message}`);
      setIsStreaming(false);
    }
  };

  // Cancel streaming
  const handleCancelStreaming = () => {
    if (abortRef.current) {
      abortRef.current();
      setIsStreaming(false);
      alert('스트리밍이 중단되었습니다');
    }
  };

  // File upload
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!roomId) {
      alert('먼저 대화를 시작해주세요');
      return;
    }

    try {
      const result = await uploadFile(file, roomId);
      setUploadedFiles(prev => [...prev, result]);
      alert(`파일 업로드 완료: ${result.file_name}`);
    } catch (err) {
      alert(`업로드 실패: ${err.message}`);
    }
  };

  // Remove uploaded file
  const handleRemoveFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(f => f.file_id !== fileId));
  };

  // New conversation
  const handleNewChat = () => {
    clearRoomId();
    setMessages([]);
    setCurrentAnswer('');
    setUploadedFiles([]);
    setMetadata(null);
  };

  // Rename conversation
  const handleRename = async (conversationRoomId) => {
    const newName = prompt('새 이름을 입력하세요:');
    if (!newName) return;

    try {
      await updateRoomName(conversationRoomId, newName);
      loadHistory();
      alert('이름이 변경되었습니다');
    } catch (err) {
      alert(`이름 변경 실패: ${err.message}`);
    }
  };

  // Delete conversation
  const handleDeleteConversation = async (conversationRoomId) => {
    if (!confirm('정말 삭제하시겠습니까?')) return;

    try {
      await deleteRoom(conversationRoomId);
      loadHistory();
      if (roomId === conversationRoomId) {
        handleNewChat();
      }
      alert('삭제되었습니다');
    } catch (err) {
      alert(`삭제 실패: ${err.message}`);
    }
  };

  return (
    <div className="chat-page" style={{ display: 'flex', height: '100vh' }}>
      {/* Sidebar - History */}
      <aside style={{
        width: '300px',
        borderRight: '1px solid #ccc',
        padding: '20px',
        overflowY: 'auto',
        display: showHistory ? 'block' : 'none'
      }}>
        <h2>대화 목록</h2>
        <button onClick={handleNewChat} style={{ marginBottom: '10px', width: '100%' }}>
          + 새 대화
        </button>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {conversations.map(conv => (
            <li key={conv.cnvs_idt_id} style={{
              padding: '10px',
              marginBottom: '5px',
              border: '1px solid #eee',
              borderRadius: '5px',
              cursor: 'pointer',
              backgroundColor: roomId === conv.cnvs_idt_id ? '#e3f2fd' : 'white'
            }}>
              <div onClick={() => loadConversation(conv.cnvs_idt_id)}>
                <div style={{ fontWeight: 'bold' }}>{conv.cnvs_smry_txt}</div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  {new Date(conv.reg_dt).toLocaleString()}
                </div>
              </div>
              <div style={{ marginTop: '5px' }}>
                <button onClick={() => handleRename(conv.cnvs_idt_id)} style={{ fontSize: '12px', marginRight: '5px' }}>
                  이름변경
                </button>
                <button onClick={() => handleDeleteConversation(conv.cnvs_idt_id)} style={{ fontSize: '12px' }}>
                  삭제
                </button>
              </div>
            </li>
          ))}
        </ul>
      </aside>

      {/* Main Chat Area */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <header style={{
          padding: '20px',
          borderBottom: '1px solid #ccc',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h1>AI Chat</h1>
          <div>
            <button onClick={() => setShowHistory(!showHistory)}>
              {showHistory ? '대화 목록 숨기기' : '대화 목록 보기'}
            </button>
            <button onClick={handleNewChat} style={{ marginLeft: '10px' }}>
              새 대화
            </button>
          </div>
        </header>

        {/* Messages Area */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          backgroundColor: '#f5f5f5'
        }}>
          {messages.length === 0 && !currentAnswer && (
            <div style={{ textAlign: 'center', marginTop: '100px', color: '#999' }}>
              <h2>대화를 시작하세요</h2>
              <p>메시지를 입력하고 Enter를 누르세요</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} style={{
              marginBottom: '20px',
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
            }}>
              <div style={{
                maxWidth: '70%',
                padding: '15px',
                borderRadius: '10px',
                backgroundColor: msg.role === 'user' ? '#1976d2' : 'white',
                color: msg.role === 'user' ? 'white' : 'black',
                boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
              }}>
                {msg.content}
              </div>
            </div>
          ))}

          {/* Streaming Answer */}
          {currentAnswer && (
            <div style={{
              marginBottom: '20px',
              display: 'flex',
              justifyContent: 'flex-start'
            }}>
              <div style={{
                maxWidth: '70%',
                padding: '15px',
                borderRadius: '10px',
                backgroundColor: 'white',
                boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
              }}>
                {currentAnswer}
                <span style={{ animation: 'blink 1s infinite' }}>|</span>
              </div>
            </div>
          )}

          {/* Metadata (Sources, Tokens, etc.) */}
          {metadata && metadata.sources && metadata.sources.length > 0 && (
            <div style={{
              marginBottom: '20px',
              padding: '10px',
              backgroundColor: '#fff3cd',
              borderRadius: '5px'
            }}>
              <strong>참고 문서:</strong>
              <ul>
                {metadata.sources.map((src, idx) => (
                  <li key={idx}>
                    {src.filename} (관련도: {(src.relevance_score * 100).toFixed(1)}%)
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Uploaded Files */}
        {uploadedFiles.length > 0 && (
          <div style={{ padding: '10px', borderTop: '1px solid #ccc', backgroundColor: '#f9f9f9' }}>
            <strong>첨부 파일:</strong>
            {uploadedFiles.map(file => (
              <span key={file.file_id} style={{
                display: 'inline-block',
                margin: '5px',
                padding: '5px 10px',
                backgroundColor: '#e3f2fd',
                borderRadius: '5px'
              }}>
                {file.file_name}
                <button onClick={() => handleRemoveFile(file.file_id)} style={{
                  marginLeft: '5px',
                  border: 'none',
                  background: 'transparent',
                  cursor: 'pointer'
                }}>
                  ✕
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div style={{
          padding: '20px',
          borderTop: '1px solid #ccc',
          backgroundColor: 'white'
        }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            {/* File Upload */}
            <label style={{ cursor: 'pointer' }}>
              <input
                type="file"
                onChange={handleFileUpload}
                accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.hwp,.hwpx,.txt,.png,.jpg,.jpeg"
                style={{ display: 'none' }}
              />
              <span style={{
                padding: '10px 15px',
                border: '1px solid #ccc',
                borderRadius: '5px',
                backgroundColor: '#f5f5f5'
              }}>
                📎 파일 첨부
              </span>
            </label>

            {/* Text Input */}
            <input
              ref={inputRef}
              type="text"
              placeholder="메시지를 입력하세요..."
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !isStreaming) {
                  handleSendMessage();
                }
              }}
              disabled={isStreaming}
              style={{
                flex: 1,
                padding: '15px',
                border: '1px solid #ccc',
                borderRadius: '5px',
                fontSize: '16px'
              }}
            />

            {/* Send/Cancel Button */}
            {isStreaming ? (
              <button onClick={handleCancelStreaming} style={{
                padding: '15px 30px',
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer'
              }}>
                중단
              </button>
            ) : (
              <button onClick={handleSendMessage} style={{
                padding: '15px 30px',
                backgroundColor: '#1976d2',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer'
              }}>
                전송
              </button>
            )}
          </div>
        </div>
      </main>

      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
