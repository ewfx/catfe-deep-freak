import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  // server: {
  //   proxy: {
  //     '/register-api': 'http://localhost:8000',
  //     '/run-tests': 'http://localhost:8000',
  //     '/openapi.json': 'http://localhost:8000', // Add this line
  //   },
  // },
  plugins: [react()],
})