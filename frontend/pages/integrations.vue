<template>
  <div class="py-10">
      <header>
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 class="text-3xl font-bold leading-tight text-gray-900">
            Integrations
          </h1>
          <p class="mt-2 text-sm text-gray-600">
            Connect external services to import and analyze support tickets
          </p>
        </div>
      </header>

      <main>
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
          <!-- Success/Error Messages -->
          <div v-if="successMessage" class="mb-6 rounded-md bg-green-50 p-4">
            <div class="flex">
              <div class="flex-shrink-0">
                <CheckCircle2 class="h-5 w-5 text-green-400" />
              </div>
              <div class="ml-3">
                <p class="text-sm text-green-800">{{ successMessage }}</p>
              </div>
              <div class="ml-auto pl-3">
                <button class="inline-flex text-green-500 hover:text-green-700" @click="successMessage = ''">
                  <X class="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>

          <div v-if="errorMessage" class="mb-6 rounded-md bg-red-50 p-4">
            <div class="flex">
              <div class="flex-shrink-0">
                <AlertCircle class="h-5 w-5 text-red-400" />
              </div>
              <div class="ml-3">
                <p class="text-sm text-red-800">{{ errorMessage }}</p>
              </div>
              <div class="ml-auto pl-3">
                <button class="inline-flex text-red-500 hover:text-red-700" @click="errorMessage = ''">
                  <X class="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>

          <!-- Integrations List -->
          <div class="bg-white shadow overflow-hidden sm:rounded-md">
            <ul class="divide-y divide-gray-200">
              <!-- HubSpot Integration -->
              <li>
                <div class="px-4 py-4 sm:px-6">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center">
                      <div class="flex-shrink-0">
                        <img class="h-12 w-12" src="/HubSpot/HubSpot_Symbol_0.svg" alt="HubSpot">
                      </div>
                      <div class="ml-4">
                        <h3 class="text-lg font-medium text-gray-900">HubSpot</h3>
                        <p class="text-sm text-gray-500">Import support tickets and customer data</p>
                        <div v-if="hubspotIntegration" class="mt-1 flex items-center text-sm">
                          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <CheckCircle2 class="-ml-0.5 mr-1.5 h-3 w-3 text-green-400" />
                            Connected
                          </span>
                          <span class="ml-3 text-gray-500">
                            Since {{ formatDate(hubspotIntegration.created_at) }}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div class="flex space-x-3">
                      <button
                        v-if="!hubspotIntegration"
                        :disabled="loading"
                        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                        @click="connectHubSpot"
                      >
                        <Loader2 v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4" />
                        Connect
                      </button>
                      <button
                        v-else
                        :disabled="loading"
                        class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                        @click="disconnectHubSpot"
                      >
                        Disconnect
                      </button>
                    </div>
                  </div>
                </div>
              </li>

              <!-- Placeholder for future integrations -->
              <li class="bg-gray-50">
                <div class="px-4 py-4 sm:px-6">
                  <p class="text-sm text-gray-500 text-center">
                    More integrations coming soon...
                  </p>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </main>
  </div>
</template>

<script setup lang="ts">
import { CheckCircle2, AlertCircle, X, Loader2 } from 'lucide-vue-next'
import type { Integration } from '~/types/integration'

// Note: Auth protection handled by auth.global.ts middleware

const { idToken, signOut } = useAuth()
const config = useRuntimeConfig()
const route = useRoute()

// State
const loading = ref(false)
const hubspotIntegration = ref<Integration | null>(null)
const successMessage = ref('')
const errorMessage = ref('')

// Handle OAuth callback messages
if (route.query.hubspot === 'connected') {
  successMessage.value = 'HubSpot connected successfully! You can now import tickets.'
}
if (route.query.hubspot === 'error') {
  errorMessage.value = route.query.message as string || 'Failed to connect HubSpot'
}

// Fetch integrations on mount
onMounted(async () => {
  await fetchIntegrations()
})

async function fetchIntegrations() {
  if (!idToken.value) {
    console.error('No auth token')
    return
  }

  try {
    const integrations = await $fetch<Integration[]>(`${config.public.apiBase}/api/v1/integrations`, {
      headers: {
        Authorization: `Bearer ${idToken.value}`
      }
    })

    hubspotIntegration.value = integrations.find(i => i.type === 'hubspot') || null
  } catch (error: unknown) {
    const apiError = error as { statusCode?: number }
    console.error('Failed to fetch integrations:', error)
    if (apiError.statusCode === 401) {
      await signOut()
      navigateTo('/login')
    }
  }
}

async function connectHubSpot() {
  if (!idToken.value) {
    errorMessage.value = 'Please log in to connect HubSpot'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const data = await $fetch<{ authorization_url: string }>(`${config.public.apiBase}/api/v1/integrations/hubspot/authorize`, {
      headers: {
        Authorization: `Bearer ${idToken.value}`
      }
    })

    // Redirect to HubSpot OAuth
    window.location.href = data.authorization_url
  } catch (error: unknown) {
    const apiError = error as { data?: { detail?: string } }
    console.error('Failed to get HubSpot auth URL:', error)
    errorMessage.value = apiError.data?.detail || 'Failed to connect to HubSpot'
    loading.value = false
  }
}

async function disconnectHubSpot() {
  if (!hubspotIntegration.value || !idToken.value) {
    return
  }

  if (!confirm('Are you sure you want to disconnect HubSpot? This will stop ticket imports.')) {
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    await $fetch(`${config.public.apiBase}/api/v1/integrations/${hubspotIntegration.value.id}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${idToken.value}`
      }
    })

    successMessage.value = 'HubSpot disconnected successfully'
    hubspotIntegration.value = null
  } catch (error: unknown) {
    const apiError = error as { data?: { detail?: string } }
    console.error('Failed to disconnect HubSpot:', error)
    errorMessage.value = apiError.data?.detail || 'Failed to disconnect HubSpot'
  } finally {
    loading.value = false
  }
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>
