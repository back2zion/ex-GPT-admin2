/**
 * Vitest 테스트 환경 설정
 */

import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Jest-DOM matchers 확장
expect.extend(matchers);

// 각 테스트 후 자동 정리
afterEach(() => {
  cleanup();
});

// LocalStorage Mock with actual storage
const localStorageMock = (() => {
  let store = {};

  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: vi.fn((key) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((index) => {
      const keys = Object.keys(store);
      return keys[index] || null;
    }),
  };
})();

global.localStorage = localStorageMock;

// NavigationPreloadManager Mock (브라우저 전용 API)
global.NavigationPreloadManager = undefined;
