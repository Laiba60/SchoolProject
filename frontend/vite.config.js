import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Same-origin in development: the browser talks to Vite, Vite forwards /api and /media to Django.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000',
    },
  },
});
