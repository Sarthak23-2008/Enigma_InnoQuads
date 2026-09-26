import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Local dev: /api is proxied to the FastAPI backend so no CORS setup is needed.
    proxy: { '/api': { target: process.env.VITE_DEV_API_TARGET || 'http://localhost:8000', changeOrigin: true } },
  },
  build: {
    rollupOptions: {
      output: { manualChunks: { react: ['react', 'react-dom', 'react-router-dom'], charts: ['recharts'] } },
    },
  },
})
