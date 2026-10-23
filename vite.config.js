import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// Mirror the original's /int/ locale prefix so links match refire.com paths.
export default defineConfig({ plugins: [react()], base: '/' , server: { open: false } })
