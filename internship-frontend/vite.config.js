import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/upload-resume': 'http://127.0.0.1:8000',
      '/job-description': 'http://127.0.0.1:8000',
      '/match-skills': 'http://127.0.0.1:8000',
      '/generate-email': 'http://127.0.0.1:8000',
    },
  },
})