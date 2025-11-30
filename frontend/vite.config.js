import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  const plugins = [react()];

  // Only use basicSsl in development mode
  if (mode === 'development') {
    plugins.push(basicSsl());
  }

  return {
    plugins,
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom', 'axios'],
            ui: ['lucide-react', 'jspdf', 'jspdf-autotable', 'xlsx']
          }
        }
      }
    }
  };
})
