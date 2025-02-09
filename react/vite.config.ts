import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from "tailwindcss"

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: {
      plugins: [tailwindcss],
    },
  },
  build: {
    outDir: '../aquillm/aquillm/static/js/dist/',
    assetsDir: '',
    manifest: true,
    rollupOptions: {
      input: {
        main: './src/main.tsx',
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]'
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/ingest_pdf': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/ingest_vtt': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/insert_arxiv': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/search': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      }
    }
  },
})