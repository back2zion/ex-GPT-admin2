import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import svgr from "vite-plugin-svgr";
import { readFileSync } from "fs";
import yaml from "js-yaml";
import path from "path";

// application.yml에서 context-path 읽기
const yamlContent = readFileSync("../src/main/resources/application.yml", "utf8");
const config = yaml.load(yamlContent);
const contextPath = config.server?.servlet?.["context-path"] ?? "/";

export default defineConfig(() => {
  return {
    // 개발·배포 모두 동일한 base 경로 지정
    base: contextPath,
    plugins: [react(), svgr()],
    define: {
      CONTEXT_PATH: JSON.stringify(contextPath), // 전역 상수로 주입
    },
    resolve: {
      alias: {
        "@assets": path.resolve(__dirname, "src/assets"),
        "@pages": path.resolve(__dirname, "src/pages"),
        "@styles": path.resolve(__dirname, "src/styles"),
        "@api": path.resolve(__dirname, "src/components/api"),
        "@common": path.resolve(__dirname, "src/components/common"),
        "@content": path.resolve(__dirname, "src/components/content"),
        "@layout": path.resolve(__dirname, "src/components/layout"),
        "@modals": path.resolve(__dirname, "src/components/modals"),
        "@store": path.resolve(__dirname, "src/components/store"),
        "@utils": path.resolve(__dirname, "src/components/utils"),
      },
    },
    build: {
      target: "es2015",
    },

    server: {
      port: 5173,
      proxy: {
        [contextPath + "/api"]: {
          target: "http://localhost:8010",
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(contextPath, ''),
        },
      },
    },
  };
});
