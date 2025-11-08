import type { UseFetchOptions } from 'nuxt/app'

export const useApi = <T>(url: string, options: UseFetchOptions<T> = {}) => {
  const config = useRuntimeConfig()
  const { idToken } = useAuth()

  const defaults: UseFetchOptions<T> = {
    baseURL: config.public.apiBase,
    onRequest({ options }) {
      if (idToken.value) {
        const headers = options.headers || {}
        ;(options.headers as any) = {
          ...headers,
          Authorization: `Bearer ${idToken.value}`
        }
      }
    },
    onResponseError({ response }) {
      if (response.status === 401) {
        // Token expired or invalid, redirect to login
        navigateTo('/login')
      }
    }
  }

  return useFetch(url, { ...defaults, ...options })
}
