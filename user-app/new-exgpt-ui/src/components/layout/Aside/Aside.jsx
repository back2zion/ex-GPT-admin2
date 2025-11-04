import { useState, useEffect } from "react";

import { useMessageStore } from "../../store/messageStore";

// toggle button icon
import { ToggleCloseIcon } from "../../../assets/components/aside/ToggleCloseIcon";
import { ToggleOpenIcon } from "../../../assets/components/aside/ToggleOpenIcon";

// department icon
import userDeptProfile from "../../../assets/icons/aside/userDeptProfile.svg";
// logo icon
import Logo from "../../../assets/components/header/Logo";
// 새 대화
import { PlusIcon } from "../../../assets/components/aside/PlusIcon";
import { NewChatGliterIcon } from "../../../assets/components/aside/NewChatGliterIcon";

import { DeleteChatIcon } from "../../../assets/components/aside/DeleteChatIcon";
// 국정 감사 AI
import { GovInspctionIcon } from "../../../assets/components/aside/GovInspctionIcon";
// 메뉴 우측 화살표
import { ChevronRightIcon } from "../../../assets/components/aside/ChevronRightIcon";

import Button from "../../common/Button/Button";
import ChatHistory from "./ChatHistory";

import "./aside.scss";

export const Aside = ({ mode }) => {
  // aside 열/닫
  const [isOpen, setIsOpen] = useState(true); // 기본은 큰 화면 열림
  const [isLargeScreen, setIsLargeScreen] = useState(window.innerWidth > 1530);
  const [manualClosed, setManualClosed] = useState(false); // 큰 화면에서 닫았는지 기억

  const clearMessages = useMessageStore(state => state.clearMessages);

  // 버튼 토글
  const toggleAside = () => {
    if (isLargeScreen) {
      setIsOpen(!isOpen);
      setManualClosed(!isOpen === false); // 열린 상태에서 누르면 -> 닫은 걸 기록
    } else {
      setIsOpen(!isOpen);
    }
  };

  // 리사이즈 핸들러
  useEffect(() => {
    const handleResize = () => {
      const large = window.innerWidth > 1530;
      setIsLargeScreen(large);

      if (large) {
        // 큰 화면으로 돌아왔을 때
        setIsOpen(!manualClosed); // 닫은 적 있으면 닫힘 유지, 아니면 열림
      } else {
        // 작은 화면은 항상 닫힘 기본
        setIsOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize(); // 최초 실행

    return () => window.removeEventListener("resize", handleResize);
  }, [manualClosed]);

  return (
    <>
      <aside className={`aside ${isOpen ? "" : "folded"}`} aria-label="사이드바">
        <div className="aside__inner">
          <h1 className="aside__logo-meta">
            <Button
              className="aside__toggle_btn"
              onClick={toggleAside}
              tabIndex={0}
              ariaLabel={isOpen ? "사이드바 접기" : "사이드바 펼치기"}
            >
              {isOpen ? <ToggleCloseIcon /> : <ToggleOpenIcon />}
            </Button>
            <div className="aside__logo-desc" aria-label="로고 이미지">
              <div>
                <span className="aside__logo-img">
                  <Logo></Logo>
                </span>
                <span className="aside__logo-version">1.5</span>
              </div>
              <span className="aside__logo-text">한국도로공사 AI</span>
            </div>
          </h1>
          {/* 프로필 이미지, 현재 버전 정보 */}
          <div className="user-info">
            {/*
            <div className="user-info__profile">
              <img
                src={
                  localStorage.getItem('color') == "light" ? userDefaultIconLight : userDefaultIconDark
                }
                alt="사용자 기본 프로필"
              />
            </div>
            <div className="user-info__meta">
              <div className="user-info__name">ex-GPT</div>
              <div className="user-info__version">한국도로공사 AI 1.4</div>
            </div>
          */}
          </div>
          {/* 새 대화, 대화 지우기, 국정감사 전용 AI */}
          <div className="aside__list">
            <div
              className="aside__link aside__link-new"
              onClick={clearMessages}
              tabIndex={0}
              aria-label="새 대화"
            >
              <div className="aside__link__inner">
                <div className="icon">
                  <PlusIcon />
                </div>
                <span className="aside__link-text">새 대화</span>
                <NewChatGliterIcon />
              </div>
            </div>
            {/*
            <div className="aside__link aside__link-delete" tabIndex={0}>
              <div className="aside__link__inner">
                <div className="icon">
                  <DeleteChatIcon />
                </div>
                <span className="aside__link-text">대화 지우기</span>
                <ChevronRightIcon className="aside__link-arrow" />
              </div>
            </div>
             */}
          </div>
          <ChatHistory />
        </div>
        {/* 부서 */}
        <div className="user__dept">
          <div className="user__dept-profile">
            <img src={userDeptProfile} alt="ex-GPT 로고" />
          </div>
          <div className="user__dept-details">
            <div className="user__dept-name">디지털계획처</div>
            <div className="user__dept-extension">(내선:800-4552)</div>
          </div>
        </div>
      </aside>
      {isOpen && <div className="overlay" onClick={toggleAside}></div>}
    </>
  );
};
