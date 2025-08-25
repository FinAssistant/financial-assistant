import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  base: '/',
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/auth': {
        target: 'http://0.0.0.0:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://0.0.0.0:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../backend/app/static',
    emptyOutDir: true,
    sourcemap: true,
  },
  preview: {
    port: 4173,
    host: true,
  },
})