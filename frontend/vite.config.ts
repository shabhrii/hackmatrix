import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

import fs from 'fs'
import path from 'path'

let backendTarget = 'http://127.0.0.1:8000'
try {
  const portsJsonPath = path.resolve(__dirname, '../.ports.json')
  if (fs.existsSync(portsJsonPath)) {
    const ports = JSON.parse(fs.readFileSync(portsJsonPath, 'utf-8'))
    if (ports.backend) {
      backendTarget = `http://127.0.0.1:${ports.backend}`
    }
  }
} catch (e) {
  // ignore
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
