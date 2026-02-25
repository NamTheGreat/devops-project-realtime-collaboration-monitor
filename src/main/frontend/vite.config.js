/**
 * vite.config.js — Vite configuration for the Git Collaboration Monitor dashboard.
 *
 * Configures React plugin, dev server proxy to the backend, and build output.
 */
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/webhook': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
      '/events': 'http://localhost:8000',
      '/stats': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
});
