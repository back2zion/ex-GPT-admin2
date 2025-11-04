import { useState, useEffect } from "react";

import { useUserSettingsStore } from "@store/userSettingsStore";
import { useModalStore } from "@store/modalStore";

// header
import Button from "@common/Button/Button";
import ThemeIcon from "@assets/components/header/ThemeIcon";
import TextIcon from "@assets/components/header/TextIcon";
import BookIcon from "@assets/components/header/BookIcon";
import NoticeIcon from "@assets/components/header/NoticeIcon";
import StarIcon from "@assets/components/header/StarIcon";
import "./header.scss";

export const Header = ({ mode }) => {
  const initSettings = useUserSettingsStore(state => state.initSettings);
  const openModal = useModalStore(state => state.openModal);
  // BUTTON label 화면 너비 작을 때 숨김 및 title 추가
  const [isLargeScreen, setIsLargeScreen] = useState(window.innerWidth > 850);

  useEffect(() => {
    initSettings();
  }, []);

  // 리사이즈 핸들러
  useEffect(() => {
    const handleResize = () => {
      const large = window.innerWidth > 850;
      setIsLargeScreen(large);
    };

    window.addEventListener("resize", handleResize);
    handleResize(); // 최초 실행

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const getTitleLabel = (isLargeScreen, label) => {
    return isLargeScreen ? "" : label;
  };

  let originalLocalStorageColor = localStorage.getItem("exGpt-theme");

  if (originalLocalStorageColor === null) {
    localStorage.setItem("exGpt-theme", "light");
  }

  // 테마
  const theme = useUserSettingsStore(state => state.theme);
  const updateTheme = useUserSettingsStore(state => state.updateTheme);

  const toggleTheme = () => {
    updateTheme(theme === "light" ? "dark" : "light");
  };

  return (
    <header className="header">
      <div className="header__inner">
        <div className="header__util-menu">
          <Button
            iconComponent={<ThemeIcon />}
            className="header__util-button"
            label="테마선택"
            titleLabel={getTitleLabel(isLargeScreen, "테마선택")}
            onClick={toggleTheme}
          />
          <Button
            iconComponent={<TextIcon />}
            className="header__util-button text-size"
            label="글자크기"
            titleLabel={getTitleLabel(isLargeScreen, "글자크기")}
            onClick={() => openModal("fontSize")}
          />
          <Button
            iconComponent={<BookIcon />}
            className="header__util-button guide"
            label="사용법안내"
            titleLabel={getTitleLabel(isLargeScreen, "사용법안내")}
            onClick={() => openModal("guide")}
          />
          <Button
            iconComponent={<NoticeIcon />}
            className="header__util-button notice"
            label="공지사항"
            titleLabel={getTitleLabel(isLargeScreen, "공지사항")}
            onClick={() => openModal("notice")}
          />
          <Button
            iconComponent={<StarIcon />}
            className="header__util-button survey"
            label="만족도조사"
            titleLabel={getTitleLabel(isLargeScreen, "만족도조사")}
            onClick={() => openModal("survey")}
          />
        </div>
      </div>
    </header>
  );
};
