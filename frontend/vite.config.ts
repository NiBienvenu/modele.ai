// Vite configuration.
// In development, calls to /question and /response are forwarded to the
// backend, so the browser sees a single origin (no CORS setup needed).
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const backend = env.BACKEND_URL || "http://localhost:4444";
  return {
    plugins: [react()],
    server: {
      port: 5555,
      strictPort: true,
      proxy: {
        "/question": backend,
        "/response": backend,
        "/conversations": backend,
      },
    },
  };
});
