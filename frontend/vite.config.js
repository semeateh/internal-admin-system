import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue2";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  },
  server: {
    host: "127.0.0.1",
    port: 5001
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          "base-vendor": ["vue", "vue-router", "axios"],
          "element-ui-vendor": ["element-ui"]
        }
      }
    }
  }
});
