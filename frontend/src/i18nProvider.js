/**
 * react-admin i18n Provider (한글 + 영어)
 * 다국어 지원: 한국어, English
 */
import polyglotI18nProvider from 'ra-i18n-polyglot';
import koreanMessages from 'ra-language-korean';
import englishMessages from 'ra-language-english';

// 한국어 커스텀 메시지
const customKoreanMessages = {
    ...koreanMessages,
    ra: {
        ...koreanMessages.ra,
        page: {
            ...koreanMessages.ra.page,
            dashboard: '📊 통계 대시보드',
            empty: '데이터가 없습니다',
            invite: '추가하시겠습니까?',
        },
        message: {
            ...koreanMessages.ra.message,
            bulk_delete_content: '이 %{name}을(를) 정말 삭제하시겠습니까? |||| 이 %{smart_count}개 항목을 정말 삭제하시겠습니까?',
            bulk_delete_title: '%{name} 삭제 |||| %{smart_count}개 %{name} 삭제',
        },
    },
};

// 영어 커스텀 메시지
const customEnglishMessages = {
    ...englishMessages,
    ra: {
        ...englishMessages.ra,
        page: {
            ...englishMessages.ra.page,
            dashboard: '📊 Statistics Dashboard',
        },
    },
};

// 다국어 메시지
const translations = {
    ko: customKoreanMessages,
    en: customEnglishMessages,
};

// i18nProvider 생성
const i18nProvider = polyglotI18nProvider(
    (locale) => translations[locale] ? translations[locale] : translations.ko,
    'ko', // 기본 언어
    [
        { locale: 'ko', name: '한국어' },
        { locale: 'en', name: 'English' }
    ],
    { allowMissing: true }
);

export default i18nProvider;
