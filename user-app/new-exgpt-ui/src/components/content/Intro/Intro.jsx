import Logo from "../../../assets/components/header/Logo";
import "./Intro.scss";

const Intro = () => {
  return (
    <div className="content__intro_wrapper">
      <div className="content__inner">
        <div className="content__intro">
          <h2 className="content__intro-title">
            <span className="content__logo-img" aria-label="로고 이미지">
              <Logo></Logo>
            </span>
          </h2>
        </div>
      </div>
    </div>
  );
};

export default Intro;
