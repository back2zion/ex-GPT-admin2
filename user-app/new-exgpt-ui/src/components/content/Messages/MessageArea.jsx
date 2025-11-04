import React, { useState, forwardRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import "./messages.scss";

import { useModalStore } from "@store/modalStore";

import { GptIcon } from "@assets/components/messages/GptIcon";
import think from "@assets/icons/message/think.svg?react";
import response from "@assets/icons/message/response.svg?react";
import document from "@assets/icons/message/document.svg?react";

import Button from "../../common/Button/Button";
import Message from "./Message";

import { DetailArrowIcon } from "@assets/components/button/DetailArrowIcon";

const MessageArea = forwardRef(({ message }, ref) => {
  const [openIndex, setOpenIndex] = useState(null);
  const openModal = useModalStore(state => state.openModal);

  const handleToggle = index => {
    setOpenIndex(openIndex === index ? null : index);
  };

  function splitByFilename(dataArray) {
    const orgSources = {};
    dataArray.forEach(obj => {
      const fname = obj.filename;
      if (!orgSources[fname]) {
        orgSources[fname] = [];
      }
      orgSources[obj.filename].push(obj);
    });
    return orgSources;
  }

  // 안전하게 content 추출
  const getContent = () => {
    if (message.role === "user") {
      return typeof message.content === 'string' ? message.content : String(message.content || '');
    }
    if (message.role === "assistant") {
      if (typeof message.content === 'string') {
        return {
          think: "",
          response: message.content,
          sources: [],
          metadata: {}
        };
      }
      return {
        think: message.content?.think || "",
        response: message.content?.response || "",
        sources: message.content?.sources || [],
        metadata: message.content?.metadata || {}
      };
    }
    return "";
  };

  const content = getContent();

  return (
    <div className="content__message" ref={ref}>
      {message.role === "user" && (
        <div className="message message--user">
          <div className="message__content">{content}</div>
        </div>
      )}

      {message.role === "assistant" && (
        <div className="message message--assistant">
          <div className="message__avatar">
            <GptIcon />
          </div>
          <div className="message__content">
            {content.think && (
              <Message
                type="thinking-container"
                title={
                  <span className={content.response ? "" : "thinking-wave"} style={{ color: "#067EE1" }}>
                    <span>추</span>
                    <span>론</span>
                    <span> </span>
                    {content.response ? <span>완료</span> : <span>중</span>}
                    {!content.response && <span>.</span>}
                    {!content.response && <span>.</span>}
                    {!content.response && <span>.</span>}
                  </span>
                }
                icon={think}
                toggleable
              >
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content.think}</ReactMarkdown>
              </Message>
            )}
            <Message
              type="response-content"
              title="답변"
              icon={response}
              actions={
                content.response && (
                  <div className="message__action-buttons">
                    <button
                      className="message__action-btn"
                      onClick={() => {
                        navigator.clipboard.writeText(content.response);
                      }}
                      title="답변 복사"
                    >
                      📋
                    </button>
                    <button
                      className="message__action-btn"
                      onClick={() => openModal("errorSubmit")}
                      title="오류 신고"
                    >
                      🚨
                    </button>
                  </div>
                )
              }
            >
              {!content.response ? (
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content.response}</ReactMarkdown>
              )}
            </Message>
            {content.sources && content.sources.length > 0 && (
              <Message type="source-documents" title="근거" icon={document}>
                <ul>
                  {Object.entries(splitByFilename(content.sources)).map(
                  ([fileName, docList]) => {
                    const buttons = [];
                    const previews = [];

                    docList.forEach((doc, index) => {
                      if (index < 4) {
                        buttons.push(
                          <Button
                            key={`btn-${index}-${doc.document_id}`}
                            type="button"
                            className={`message__content_button source-toggle-button ${openIndex === `${index}-${doc.document_id}` ? "rotate" : ""}`}
                            onClick={() => handleToggle(`${index}-${doc.document_id}`)}
                          >
                            <span>
                              {openIndex === `${index}-${doc.document_id}` ? "숨기기" : "상세보기"}
                            </span>
                            <span className="relevance-score">
                              {" "}
                              ({(doc.relevance_score * 100).toFixed(1)}% 일치)
                            </span>
                            <DetailArrowIcon />
                          </Button>
                        );
                        previews.push(
                          <div
                            key={`preview-${index}-${doc.document_id}`}
                            className={`source-documents-preview ${openIndex === `${index}-${doc.document_id}` ? "active" : ""}`}
                          >
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {doc.content_preview}
                            </ReactMarkdown>
                          </div>
                        );
                      }
                    });

                    // 다운로드 URL 생성
                    const firstDoc = docList[0];
                    let downloadUrl = null;
                    if (firstDoc.download_url) {
                      // download_url이 있으면 그대로 사용 (이미 /v1/file/... 형식)
                      downloadUrl = firstDoc.download_url;
                      console.log('🔗 다운로드 URL (download_url):', downloadUrl, 'fileName:', fileName);
                    } else if (firstDoc.document_id) {
                      // document_id로 절대경로 URL 생성
                      downloadUrl = `/v1/file/public/${firstDoc.document_id}/download`;
                      console.log('🔗 다운로드 URL (document_id):', downloadUrl, 'fileName:', fileName);
                    } else {
                      console.warn('⚠️ download_url과 document_id가 모두 없음:', firstDoc);
                    }

                    return (
                      <li key={downloadUrl || fileName}>
                        <strong>{fileName}</strong>{" "}
                        {downloadUrl && (
                          <a
                            href={downloadUrl}
                            className="message__content_button"
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label={`${fileName} 다운로드`}
                          >
                            다운로드
                          </a>
                        )}
                        <div className="source-buttons">{buttons}</div>
                        <div className="source-previews">{previews}</div>
                      </li>
                    );
                  }
                )}
                </ul>
              </Message>
            )}
          </div>
        </div>
      )}
    </div>
  );
});

export default React.memo(MessageArea);
