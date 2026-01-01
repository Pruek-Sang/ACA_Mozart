import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    // ═══════════════════════════════════════════════════════════════
    // Custom rules: hooks = ERROR (blocks CI), any type = WARN only
    // ═══════════════════════════════════════════════════════════════
    rules: {
      // 🔴 CRITICAL: React Hooks violations MUST block CI
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      // 🟡 NON-CRITICAL: Allow 'any' type for now (legacy code)
      '@typescript-eslint/no-explicit-any': 'warn',
    },
  },
])
