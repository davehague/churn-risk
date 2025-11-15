// @ts-check
import { createConfigForNuxt } from '@nuxt/eslint-config/flat'

export default createConfigForNuxt(
  // Nuxt-specific options
  {},
  // Custom rules
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.vue'],
    rules: {
      // TypeScript Best Practices (Pragmatic Configuration)

      // Allow 'any' in catch blocks and as function parameters - common real-world pattern
      '@typescript-eslint/no-explicit-any': ['warn', {
        ignoreRestArgs: true
      }],

      // Unused variables - allow underscore prefix for intentionally unused vars
      '@typescript-eslint/no-unused-vars': ['error', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrorsIgnorePattern: '^_'
      }],

      // Vue 3 best practices - keep as errors since they prevent bugs
      'vue/require-v-for-key': 'error',
      'vue/no-mutating-props': 'error',
      'vue/prefer-import-from-vue': 'error',

      // Disable overly pedantic Vue formatting rules
      'vue/first-attribute-linebreak': 'off'
    }
  },
  // Vue component files - more lenient since they're template-focused
  {
    files: ['**/*.vue'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn'
    }
  }
)
