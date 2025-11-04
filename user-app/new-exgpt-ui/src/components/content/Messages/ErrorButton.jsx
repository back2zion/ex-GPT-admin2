import Button from "../../common/Button/Button";
import { ErrorSubmitIcon } from "../../../assets/components/messages/ErrorSubmitIcon";

const ErrorButton = ({ onOpenErrorSubmitModal }) => {
  return (
    <div className="message__error__button">
      <Button
        iconComponent={<ErrorSubmitIcon />}
        className="message__error__icon"
        onClick={onOpenErrorSubmitModal}
      ></Button>
      <span className="message__error__tooltip">오류 신고하세요!</span>
    </div>
  );
};

export default ErrorButton;
