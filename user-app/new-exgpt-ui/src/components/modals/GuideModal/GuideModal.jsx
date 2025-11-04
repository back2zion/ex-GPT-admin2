import Modal from "@common/Modal/Modal";

import TextIcon from "@assets/components/header/TextIcon";
import NoticeIcon from "@assets/components/header/NoticeIcon";
import StarIcon from "@assets/components/header/StarIcon";
import { GovInspctionIcon } from "@assets/components/aside/GovInspctionIcon";

import "./guideModal.scss";

const GuideModal = ({ closeModal }) => {
  return (
    <Modal
      className="guide-modal"
      title="사용법 안내"
      onCancel={closeModal}
      footerButtons={[{ className: "primary", label: "닫기", onClick: closeModal }]}
    >
      <div className="guide-modal-set">
        <div className="guide-modal-title">기본 사용법</div>
        <ul className="guide-modal-list">
          <li>질문을 입력하고 Enter 또는 전송 버튼을 클릭하세요</li>
          <li>AI가 실시간으로 답변을 제공합니다</li>
          <li>추천 질문을 클릭하여 빠르게 질문할 수 있습니다</li>
        </ul>
      </div>
      <div className="guide-modal-set">
        <div className="guide-modal-title">주요 기능</div>
        <ul className="guide-modal-list">
          <li>
            <span className="icon-inn">
              <TextIcon />
            </span>
            글자 크기 조절: 읽기 편한 크기로 조정
          </li>
          <li>
            <span className="icon-inn">
              <NoticeIcon />
            </span>
            공지사항: 시스템 업데이트 및 공지 확인
          </li>
          <li>
            <span className="icon-inn">
              <StarIcon />
            </span>
            만족도 조사: 서비스 개선을 위한 의견 제출
          </li>
          <li>
            <span className="icon-inn">
              <GovInspctionIcon />
            </span>
            국정감사 전용 AI: 국정감사 업무에 특화된 AI 모드 선택
          </li>
        </ul>
      </div>
      <div className="guide-modal-set">
        <div className="guide-modal-title">단축키</div>
        <ul className="guide-modal-list">
          <li>
            <em>Enter:</em> 메시지 전송
          </li>
          <li>
            <em>Shift + Enter:</em> 줄바꿈
          </li>
          {/* <li>
                <em>Ctrl + T:</em>Think 모드 토글
                </li> */}
        </ul>
      </div>
    </Modal>
  );
};

export default GuideModal;
