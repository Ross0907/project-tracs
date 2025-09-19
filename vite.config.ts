import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // GitHub Pages base path. Use env when set (CI), otherwise "/" for local/dev.
  // Set PUBLIC_BASE_PATH to "/<repo-name>/" in GitHub Actions for Pages deploys.
  base: process.env.PUBLIC_BASE_PATH || "/",
}));
