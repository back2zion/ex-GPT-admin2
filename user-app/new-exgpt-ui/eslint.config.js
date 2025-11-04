import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import jsxA11y from "eslint-plugin-jsx-a11y";
import prettier from "eslint-plugin-prettier";
import prettierConfig from "eslint-config-prettier";

import { defineConfig, globalIgnores } from "eslint/config";

export default defineConfig([
  globalIgnores(["dist"]),
  {
    files: ["vite.config.js"],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  },
  {
    files: ["**/*.{js,jsx}"],
    plugins: {
      "jsx-a11y": jsxA11y,
      prettier,
    },
    extends: [
      js.configs.recommended,
      reactHooks.configs["recommended-latest"],
      reactRefresh.configs.vite,
      prettierConfig,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: { ...globals.browser, CONTEXT_PATH: "readonly" },
      parserOptions: {
        ecmaVersion: "latest",
        ecmaFeatures: { jsx: true },
        sourceType: "module",
      },
    },
    rules: {
      "no-unused-vars": ["error", { varsIgnorePattern: "^[A-Z_]" }],

      // 접근성 강화 규칙 (WCAG 2.1 Level AA 기반)
      "jsx-a11y/alt-text": "error", // 이미지에 alt 필수
      "jsx-a11y/anchor-is-valid": "error", // 링크 유효성
      "jsx-a11y/aria-role": "error", // ARIA 역할 정확성
      "jsx-a11y/label-has-associated-control": [
        "error",
        {
          assert: "either",
          depth: 3,
        },
      ],
      "jsx-a11y/no-autofocus": "warn", // 자동 포커스 금지
      "jsx-a11y/interactive-supports-focus": "warn", // 인터랙티브 요소에 포커스 가능해야 함
      "jsx-a11y/heading-has-content": "error", // 제목 요소에 콘텐츠 필수
      "jsx-a11y/tabindex-no-positive": "error", // tabIndex는 0 또는 -1만 허용
      "jsx-a11y/no-redundant-roles": "warn", // 중복된 role 사용 금지

      "prettier/prettier": "warn",
    },
  },
]);
