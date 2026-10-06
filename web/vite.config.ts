import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development, requests to /api go to the Flask server, so the browser never needs CORS.
// Set API_PROXY_TARGET if your API runs elsewhere (macOS often uses port 5000 for AirPlay).
const apiTarget = process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:5000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
