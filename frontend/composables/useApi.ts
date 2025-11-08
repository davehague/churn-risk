import type { UseFetchOptions } from 'nuxt/app'

export const useApi = <T>(url: string, options: UseFetchOptions<T> = {}) => {
  const config = useRuntimeConfig()
  const { idToken } = useAuth()

  const defaults: UseFetchOptions<T> = {
    baseURL: config.public.apiBase,
    headers: idToken.value
      ? { Authorization: `Bearer ${idToken.value}` }
      : {},
    onResponseError({ response }) {
      if (response.status === 401) {
        // Token expired or invalid, redirect to login
        navigateTo('/login')
      }
    }
  }

  return useFetch(url, { ...defaults, ...options })
}
