import { defineStore } from 'pinia'
import type { User, Tenant } from '~/types/user'

export const useUserStore = defineStore('user', {
  state: () => ({
    currentUser: null as User | null,
    tenant: null as Tenant | null,
    loading: false
  }),

  actions: {
    async fetchCurrentUser() {
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
      } catch (error) {
        console.error('Failed to fetch user:', error)
        this.currentUser = null
        this.tenant = null
      } finally {
        this.loading = false
      }
    },

    async logout() {
      const { signOut } = useAuth()

      this.currentUser = null
      this.tenant = null

      await signOut()
    }
  }
})
