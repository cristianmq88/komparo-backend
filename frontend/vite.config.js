import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El proxy /api evita problemas de CORS en desarrollo: las llamadas a
// /api/* se redirigen al backend de FastAPI definido en VITE_API_URL.
export default defineConfig(({ mode }) => {
  const apiTarget = process.env.VITE_API_URL || "http://localhost:8000";
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  };
});
