import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

let api_ip = "172.20.10.2"

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://'+api_ip+':8001',
        changeOrigin: true,
        secure: false
      }
    }
  }
})