/**
 * 시큐어 코딩 유틸리티
 * OWASP Top 10 대응: XSS, CSRF, 입력 검증
 */

import DOMPurify from 'dompurify';

// ==================== XSS 방어 ====================

/**
 * HTML 살균 (XSS 방어)
 * @param {string} html - 살균할 HTML 문자열
 * @returns {string} 살균된 HTML
 */
export function sanitizeHtml(html) {
  if (!html) return '';
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
    ALLOWED_ATTR: ['href', 'target']
  });
}

/**
 * HTML 엔티티 인코딩 (XSS 방어)
 * @param {string} str - 인코딩할 문자열
 * @returns {string} 인코딩된 문자열
 */
export function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * 안전한 텍스트만 추출 (HTML 태그 제거)
 * @param {string} html - HTML 문자열
 * @returns {string} 텍스트만 추출
 */
export function stripHtml(html) {
  if (!html) return '';
  const div = document.createElement('div');
  div.innerHTML = DOMPurify.sanitize(html);
  return div.textContent || div.innerText || '';
}

// ==================== CSRF 방어 ====================

/**
 * CSRF 토큰 가져오기
 * @returns {string|null} CSRF 토큰
 */
export function getCsrfToken() {
  // 1. 메타 태그에서 읽기
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) {
    return meta.getAttribute('content');
  }

  // 2. 쿠키에서 읽기 (Django, Laravel 방식)
  const name = 'csrftoken';
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(';').shift();
  }

  return null;
}

/**
 * CSRF 토큰 설정 (메타 태그에)
 * @param {string} token - CSRF 토큰
 */
export function setCsrfToken(token) {
  let meta = document.querySelector('meta[name="csrf-token"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.name = 'csrf-token';
    document.head.appendChild(meta);
  }
  meta.content = token;
}

// ==================== 입력 검증 ====================

/**
 * 날짜 형식 검증 (YYYY-MM-DD)
 * @param {string} dateString - 검증할 날짜 문자열
 * @returns {boolean} 유효한 날짜 여부
 */
export function isValidDate(dateString) {
  if (!dateString) return true; // 빈 값은 허용

  // 정규식: YYYY-MM-DD
  const regex = /^\d{4}-\d{2}-\d{2}$/;
  if (!regex.test(dateString)) return false;

  // 실제 날짜인지 확인
  const date = new Date(dateString);
  return date instanceof Date && !isNaN(date);
}

/**
 * 사용자 ID 검증 (영문, 숫자, -, _ 만 허용)
 * @param {string} userId - 검증할 사용자 ID
 * @returns {boolean} 유효한 사용자 ID 여부
 */
export function isValidUserId(userId) {
  if (!userId) return true; // 빈 값은 허용

  // 영문, 숫자, -, _ 만 허용 (1~50자)
  const regex = /^[a-zA-Z0-9_-]{1,50}$/;
  return regex.test(userId);
}

/**
 * 이메일 형식 검증
 * @param {string} email - 검증할 이메일
 * @returns {boolean} 유효한 이메일 여부
 */
export function isValidEmail(email) {
  if (!email) return true; // 빈 값은 허용

  // RFC 5322 간소화 버전
  const regex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
  return regex.test(email);
}

/**
 * 숫자 범위 검증
 * @param {number} value - 검증할 값
 * @param {number} min - 최소값
 * @param {number} max - 최대값
 * @returns {boolean} 범위 내 여부
 */
export function isInRange(value, min, max) {
  const num = Number(value);
  if (isNaN(num)) return false;
  return num >= min && num <= max;
}

/**
 * SQL Injection 패턴 감지 (방어 레이어)
 * @param {string} input - 검증할 입력
 * @returns {boolean} SQL Injection 패턴 포함 여부
 */
export function containsSqlInjection(input) {
  if (!input) return false;

  // SQL 키워드 패턴 (대소문자 무시)
  const sqlPatterns = [
    /(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bCREATE\b)/i,
    /(\bUNION\b.*\bSELECT\b)/i,
    /(OR|AND)\s+\d+\s*=\s*\d+/i,
    /['";].*(--)|(\/\*)/,
  ];

  return sqlPatterns.some(pattern => pattern.test(input));
}

/**
 * XSS 패턴 감지 (방어 레이어)
 * @param {string} input - 검증할 입력
 * @returns {boolean} XSS 패턴 포함 여부
 */
export function containsXss(input) {
  if (!input) return false;

  // XSS 패턴
  const xssPatterns = [
    /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
    /javascript:/gi,
    /on\w+\s*=/gi, // onclick, onerror 등
    /<iframe/gi,
  ];

  return xssPatterns.some(pattern => pattern.test(input));
}

// ==================== 데이터 마스킹 (개인정보 보호) ====================

/**
 * 이메일 마스킹
 * @param {string} email - 마스킹할 이메일
 * @returns {string} 마스킹된 이메일
 * @example maskEmail('test@example.com') => 't***@example.com'
 */
export function maskEmail(email) {
  if (!email || !isValidEmail(email)) return email;

  const [local, domain] = email.split('@');
  if (local.length <= 1) return email;

  const masked = local[0] + '*'.repeat(local.length - 1);
  return `${masked}@${domain}`;
}

/**
 * 전화번호 마스킹
 * @param {string} phone - 마스킹할 전화번호
 * @returns {string} 마스킹된 전화번호
 * @example maskPhone('010-1234-5678') => '010-****-5678'
 */
export function maskPhone(phone) {
  if (!phone) return phone;

  // 010-1234-5678 또는 01012345678 형식
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 11) {
    return `${cleaned.slice(0, 3)}-****-${cleaned.slice(7)}`;
  }
  return phone;
}

/**
 * 이름 마스킹
 * @param {string} name - 마스킹할 이름
 * @returns {string} 마스킹된 이름
 * @example maskName('홍길동') => '홍*동'
 */
export function maskName(name) {
  if (!name || name.length <= 1) return name;

  if (name.length === 2) {
    return name[0] + '*';
  }

  return name[0] + '*'.repeat(name.length - 2) + name[name.length - 1];
}

// ==================== 유틸리티 ====================

/**
 * 안전한 JSON 파싱
 * @param {string} json - JSON 문자열
 * @param {*} defaultValue - 파싱 실패 시 기본값
 * @returns {*} 파싱된 객체 또는 기본값
 */
export function safeJsonParse(json, defaultValue = null) {
  try {
    return JSON.parse(json);
  } catch (error) {
    console.error('JSON parse error:', error);
    return defaultValue;
  }
}

/**
 * 안전한 URL 생성 (Open Redirect 방지)
 * @param {string} url - URL 문자열
 * @param {string[]} allowedDomains - 허용된 도메인 목록
 * @returns {string|null} 검증된 URL 또는 null
 */
export function safeUrl(url, allowedDomains = []) {
  if (!url) return null;

  try {
    const urlObj = new URL(url, window.location.origin);

    // 같은 도메인이면 허용
    if (urlObj.origin === window.location.origin) {
      return url;
    }

    // 허용된 도메인 체크
    if (allowedDomains.length > 0) {
      const isAllowed = allowedDomains.some(domain =>
        urlObj.hostname === domain || urlObj.hostname.endsWith(`.${domain}`)
      );
      if (isAllowed) {
        return url;
      }
    }

    // 허용되지 않은 외부 URL
    return null;
  } catch (error) {
    return null;
  }
}
