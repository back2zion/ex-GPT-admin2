import { useState,useEffect } from "react";
import { Virtuoso } from "react-virtuoso";

import { getNoticeList, getNoticeDetail } from "@api/notice";
import Modal from "../../common/Modal/Modal";

import "./noticeModal.scss";


const NoticeModal = ({ closeModal }) => {
  const [openIndex, setOpenIndex] = useState(null);
  const [notices, setNotices] = useState([]);

  useEffect(() => {
    const getNotice = async () => {
      try{
        const data = await getNoticeList()
        setNotices(data.data)
      } catch (error) {
        console.error("Error fetching notices:", error);
      }
    }
    getNotice()
  }, []);

  const getNoticeContent = async (pstId, brdId) => {
    try {
      const data = await getNoticeDetail(pstId, brdId)
      return data.data.pstCont
    }
    catch (error) {
      console.error("Error fetching notice detail:", error);
      return "내용을 불러오는 도중 오류가 발생했습니다.";
    }
    
  }

  const toggleDetail = (index, pstId, brdId) => {
    setOpenIndex(openIndex === index ? null : index);
    getNoticeContent(pstId, brdId).then(content => {
      setNotices(prevNotices => {
        const updatedNotices = [...prevNotices];
        updatedNotices[index] = { ...updatedNotices[index], pstCont: content };
        return updatedNotices;
      });
    });
  };

  return (
    <Modal
      className="notice-modal"
      title="공지사항"
      onCancel={closeModal}
      footerButtons={[{ className: "primary", label: "닫기", onClick: closeModal }]}
    >
      <div className="notice-modal-area">
        <Virtuoso 
          style={{ height: '300px' }}
          totalCount={notices.length}
          itemContent={(index) => {
            const notice = notices[index];
            return (
              <div className="notice-modal-item" key={index}>
                <div
                  className="notice-modal-title"
                  onClick={() => toggleDetail(index, notice.pstId, notice.brdId)}
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
                <div className={`notice-modal-detail ${openIndex === index ? "open" : "hidden"}`}>
                  {notice.pstCont}
                </div>
              </div>
            )
          }}
        />
      </div>
    </Modal>
  );
};

export default NoticeModal;
