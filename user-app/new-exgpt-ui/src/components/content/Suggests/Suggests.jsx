import { useEffect, useRef, useState } from "react";
import Slider from "react-slick";

import { suggestionList } from "../../api/suggestionList";

import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import "./suggests.scss";

const Suggests = ({ onSuggestClick }) => {
  const [suggestList, setSuggestList] = useState([]);
  const [slidesToShow, setSlidesToShow] = useState(4);
  const sliderRef = useRef(null);

  useEffect(() => {
    const fetchSuggestions = async () => {
      try {
        const data = await suggestionList();
        if(data.result == "fail") {
          console.error("추천질문 목록 가져오기 실패:", data.message);
          setSuggestList([
            { title: "통행료는 어떤 방식으로 산정되나요?" },
            { title: "법인카드 사용 제한 업종" },
            { title: "둘째 아이 출산시 출산 지원비는 얼마인가요?" },
            { title: "병가 관련 규정 알려줘" },
          ]);
        }
        else{
          setSuggestList(data.data);
        }
      } catch {
        setSuggestList([
          { title: "통행료는 어떤 방식으로 산정되나요?" },
          { title: "법인카드 사용 제한 업종" },
          { title: "둘째 아이 출산시 출산 지원비는 얼마인가요?" },
          { title: "병가 관련 규정 알려줘" },
        ]);
      }
    };

    fetchSuggestions();
  }, []);

  useEffect(() => {
    const updateSlides = () => {
      const width = window.innerWidth;
      if (width <= 575) setSlidesToShow(1);
      else if (width <= 670) setSlidesToShow(1);
      else if (width <= 770) setSlidesToShow(2);
      else if (width <= 1680) setSlidesToShow(3);
      else setSlidesToShow(4);
    };

    updateSlides();
    window.addEventListener("resize", updateSlides);
    return () => window.removeEventListener("resize", updateSlides);
  }, []);

  // slick-active 기준으로 tabIndex 설정
  useEffect(() => {
    const updateTabIndex = () => {
      const items = document.querySelectorAll(".content__suggests__item");
      items.forEach(item => {
        const slide = item.closest(".slick-slide");
        if (slide?.classList.contains("slick-active")) {
          item.setAttribute("tabIndex", "0");
        } else {
          item.setAttribute("tabIndex", "-1");
        }
      });
    };

    updateTabIndex();

    const sliderNode = sliderRef.current?.innerSlider?.list;
    sliderNode?.addEventListener("transitionend", updateTabIndex);

    return () => {
      sliderNode?.removeEventListener("transitionend", updateTabIndex);
    };
  }, []);

  const settings = {
    dots: false,
    infinite: true,
    speed: 500,
    slidesToShow,
    slidesToScroll: 1,
    arrows: true,
    centerPadding: "12px",
  };

  return (
    <div className="content__suggests_wrapper">
      <div className="content__inner" aria-label="추천 질문 목록">
        <div className="content__suggests">
          <Slider ref={sliderRef} {...settings}>
            {suggestList.map((item, index) => (
              <div key={index}>
                <div
                  className="content__suggests__item"
                  onClick={() => onSuggestClick(item.title)}
                  onKeyDown={e => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSuggestClick(item.title);
                    }
                  }}
                  tabIndex={-1}
                  role="button"
                  aria-label={item.title}
                >
                  <div className="content__suggests__text">{item.title}</div>
                </div>
              </div>
            ))}
          </Slider>
        </div>
      </div>
    </div>
  );
};

export default Suggests;
