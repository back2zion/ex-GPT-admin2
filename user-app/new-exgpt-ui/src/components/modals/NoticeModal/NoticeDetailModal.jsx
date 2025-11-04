import { useState } from "react";
import Modal from "../../common/Modal/Modal";
import "./noticeModal.scss";

const notices = [
  {
    titleNm: "시스템 업데이트 안내",
    regYmd: "2025-08-18",
    pstId: "1",
    brdId: "NOTICE",
    pstCont:
      "ex-GPT 1.4 버전이 출시되었습니다. 새로운 기능으로 음성 입력, 국정감사 전용 AI 설정 등이 추가되었습니다. 더 나은 서비스를 위해 지속적으로 개선하고 있습니다.",
  },
  {
    titleNm: "정기 점검 예정",
    regYmd: "2025- 01-15",
    pstId: "2",
    brdId: "NOTICE",
    pstCont:
      "2025년 9월 1일(일) 오전 2시부터 4시까지 시스템 정기 점검이 예정되어 있습니다. 이 시간 동안 서비스 이용이 일시적으로 제한될 수 있습니다.",
  },
  {
    titleNm: "신규 기능 추가",
    regYmd: "2025-01-15",
    pstId: "3",
    brdId: "NOTICE",
    pstCont:
      "사용자 편의를 위해 파일 첨부 기능이 추가되었습니다. 이제 최대 5개의 파일을 한 번에 업로드할 수 있습니다.",
  },
];

const NoticeDetailModal = ({ onCancel, onConfirm }) => {
  const [openIndex, setOpenIndex] = useState(null);

  const toggleDetail = index => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <Modal
      className="notice-detail-modal"
      title="공지상세"
      onCancel={onCancel}
      footerButtons={[
        { className: "secondary", label: "취소", onClick: onCancel },
        { className: "primary", label: "확인", onClick: onConfirm },
      ]}
    >
      <div className="notice-modal-area">
        {notices.map((notice, index) => (
          <div className="notice-modal-item" key={index}>
            <div
              className="notice-modal-title"
              onClick={() => toggleDetail(index)}
              onKeyDown={e => {
                if (e.key === "Enter" || e.key === " ") toggleDetail(index);
              }}
              role="button"
              tabIndex={0}
            >
              <span className="notice-modal-title-bullet">•</span>
              <div className="notice-modal-title-content">
                <div className="notice-modal-title-text">{notice.titleNm}</div>
                <div className="notice-modal-title-date">{notice.regYmd}</div>
              </div>
            </div>
            {notice.pstCont && (
              <div className={`notice-modal-detail ${openIndex === index ? "open" : "hidden"}`}>
                {notice.pstCont}
              </div>
            )}
          </div>
        ))}
      </div>
    </Modal>
  );
};

export default NoticeDetailModal;
