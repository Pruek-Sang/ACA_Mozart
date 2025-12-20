import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// NOTE: Deck UI entry point removed from production build to fix CI/CD
// Deck UI can still be run locally with: vite --config vite.config.deck.ts
export default defineConfig({
  plugins: [react()],
})
