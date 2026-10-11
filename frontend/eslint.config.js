import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';
import { defineConfig, globalIgnores } from 'eslint/config';

export default defineConfig([
  globalIgnores([
    'dist',
    'node_modules',
    'playwright-report',
    'test-results',
    'coverage',
  ]),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      // Разрешаем any — данные API типизировать будем позже, отдельным PR.
      '@typescript-eslint/no-explicit-any': 'off',

      // setState внутри useEffect — React 19+ предупреждает о каскадных рендерах,
      // но в нашем коде это осознанное решение. Отключаем.
      'react-hooks/set-state-in-effect': 'off',

      // Missing dependency в useEffect — оставляем как warning (не блокирует CI).
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
]);