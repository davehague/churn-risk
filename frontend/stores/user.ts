import { defineStore } from 'pinia'
import type { User, Tenant } from '~/types/user'

export const useUserStore = defineStore('user', {
  state: () => ({
    currentUser: null as User | null,
    tenant: null as Tenant | null,
    loading: false
  }),

  actions: {
    async fetchCurrentUser(): Promise<void> {
      const { idToken } = useAuth()
      const config = useRuntimeConfig()

      if (!idToken.value) {
        this.currentUser = null
        this.tenant = null
        return
      }

      this.loading = true

      try {
        const data = await $fetch<User>(`${config.public.apiBase}/api/v1/me`, {
          headers: {
            Authorization: `Bearer ${idToken.value}`
          }
        })

        this.currentUser = data

        // TODO: Fetch tenant data separately if needed
        // For now, tenant_id is in user data
      } catch (error: unknown) {
        console.error('Failed to fetch user:', error)

        // Handle 401 - token expired or invalid
        if ((error as any)?.statusCode === 401) {
          const { signOut } = useAuth()
          await signOut()
        }

        this.currentUser = null
        this.tenant = null

      } finally {
        this.loading = false
      }
    },

    async logout(): Promise<void> {
      const { signOut } = useAuth()

      this.currentUser = null
      this.tenant = null

      await signOut()
    }
  }
})
