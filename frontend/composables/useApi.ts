import type { UseFetchOptions } from 'nuxt/app'

export const useApi = <T>(url: string, options: UseFetchOptions<T> = {}) => {
  const config = useRuntimeConfig()
  const { idToken } = useAuth()

  const defaults: UseFetchOptions<T> = {
    baseURL: config.public.apiBase,
    onRequest({ options }) {
      if (idToken.value) {
        // Merge headers - ofetch accepts plain objects despite Headers typing
        const currentHeaders = options.headers instanceof Headers
          ? Object.fromEntries(options.headers.entries())
          : (options.headers || {});

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (options.headers as any) = {
          ...currentHeaders,
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
