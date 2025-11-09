<template>
  <div class="py-10">
    <header>
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="md:flex md:items-center md:justify-between">
          <div class="flex-1 min-w-0">
            <h1 class="text-3xl font-bold leading-tight text-gray-900">
              Support Tickets
            </h1>
          </div>
          <div class="mt-4 flex md:mt-0 md:ml-4">
            <button
              @click="handleRefresh"
              :disabled="ticketsStore.importing || !hasHubSpotIntegration"
              class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <svg v-if="!ticketsStore.importing" class="mr-2 -ml-1 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <svg v-else class="animate-spin mr-2 -ml-1 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ ticketsStore.importing ? 'Importing...' : 'Refresh Tickets' }}
            </button>
          </div>
        </div>
        <div v-if="ticketsStore.lastSync" class="mt-2 text-sm text-gray-500">
          Last synced: {{ formatLastSync(ticketsStore.lastSync) }}
        </div>
      </div>
    </header>

    <main>
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <!-- OAuth Success/Error Messages -->
        <div v-if="oauthSuccess" class="mt-6 rounded-md bg-green-50 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <p class="text-sm text-green-800">HubSpot connected successfully!</p>
            </div>
            <div class="ml-auto pl-3">
              <button @click="oauthSuccess = false" class="inline-flex text-green-500 hover:text-green-700">
                <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div v-if="oauthError" class="mt-6 rounded-md bg-red-50 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <p class="text-sm text-red-800">{{ oauthErrorMessage || 'Failed to connect to HubSpot' }}</p>
            </div>
            <div class="ml-auto pl-3">
              <button @click="oauthError = false" class="inline-flex text-red-500 hover:text-red-700">
                <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- HubSpot Connection Banner -->
        <div v-if="!hasHubSpotIntegration && !checkingIntegration" class="mt-6 rounded-lg bg-blue-50 border border-blue-200 p-6">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="ml-3 flex-1">
              <h3 class="text-sm font-medium text-blue-800">Connect HubSpot to Import Tickets</h3>
              <div class="mt-2 text-sm text-blue-700">
                <p>Connect your HubSpot account to start analyzing support tickets and detecting churn risk.</p>
              </div>
              <div class="mt-4">
                <button
                  @click="connectHubSpot"
                  :disabled="connecting"
                  class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {{ connecting ? 'Connecting...' : 'Connect HubSpot' }}
                </button>
              </div>
            </div>
          </div>
        </div>
        <!-- Tab Navigation -->
        <div class="border-b border-gray-200 mt-6">
          <nav class="-mb-px flex space-x-8">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
              ]"
            >
              {{ tab.label }}
              <span
                :class="[
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-600'
                    : 'bg-gray-100 text-gray-900',
                  'ml-2 py-0.5 px-2.5 rounded-full text-xs font-medium'
                ]"
              >
                {{ tab.count }}
              </span>
            </button>
          </nav>
        </div>

        <!-- Error Message -->
        <div v-if="ticketsStore.error" class="mt-6 rounded-md bg-red-50 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <p class="text-sm text-red-800">{{ ticketsStore.error }}</p>
            </div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="ticketsStore.loading && !ticketsStore.tickets.length" class="mt-6">
          <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <div v-for="i in 6" :key="i" class="bg-white rounded-lg shadow p-6 animate-pulse">
              <div class="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div class="h-3 bg-gray-200 rounded w-full mb-2"></div>
              <div class="h-3 bg-gray-200 rounded w-5/6 mb-2"></div>
              <div class="h-3 bg-gray-200 rounded w-4/6"></div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="!ticketsStore.loading && filteredTickets.length === 0" class="mt-6">
          <div class="text-center py-12">
            <svg class="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No tickets found</h3>
            <p class="mt-1 text-sm text-gray-500">
              {{ activeTab === 'all' ? 'No tickets from the last 7 days' : `No ${activeTab} tickets` }}
            </p>
            <div class="mt-6">
              <button
                @click="handleRefresh"
                :disabled="ticketsStore.importing"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {{ ticketsStore.importing ? 'Importing...' : 'Import Tickets' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Ticket Grid -->
        <div v-else class="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="ticket in filteredTickets"
            :key="ticket.id"
            @click="handleTicketClick(ticket)"
            class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer p-6"
          >
            <!-- Sentiment Badge -->
            <div class="mb-3">
              <span
                :class="[
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                  getSentimentColor(ticket.sentiment_score)
                ]"
              >
                {{ getSentimentLabel(ticket.sentiment_score) }}
              </span>
            </div>

            <!-- Subject -->
            <h3 class="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
              {{ ticket.subject }}
            </h3>

            <!-- Content Preview -->
            <p class="text-sm text-gray-600 mb-4 line-clamp-3">
              {{ truncateContent(ticket.content) }}
            </p>

            <!-- Metadata -->
            <div class="space-y-2 text-sm text-gray-500">
              <div v-if="ticket.company" class="flex items-center">
                <svg class="h-4 w-4 mr-1.5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                {{ ticket.company.name }}
              </div>

              <div class="flex items-center">
                <svg class="h-4 w-4 mr-1.5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ formatRelativeDate(ticket.hubspot_created_at || ticket.created_at) }}
              </div>

              <div v-if="ticket.sentiment_confidence" class="flex items-center text-xs">
                <svg class="h-4 w-4 mr-1.5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                {{ Math.round(ticket.sentiment_confidence * 100) }}% confidence
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Ticket Detail Modal -->
    <TicketDetailModal />
  </div>
</template>

<script setup lang="ts">
import type { Ticket } from '~/types/ticket'

definePageMeta({
  layout: 'default'
})

const ticketsStore = useTicketsStore()
const activeTab = ref('all')
const hasHubSpotIntegration = ref(false)
const checkingIntegration = ref(true)
const connecting = ref(false)
const oauthSuccess = ref(false)
const oauthError = ref(false)
const oauthErrorMessage = ref('')

const { idToken, loading: authLoading } = useAuth()

// Check for OAuth callback success/error in URL
const route = useRoute()
if (route.query.hubspot === 'connected') {
  oauthSuccess.value = true
} else if (route.query.hubspot === 'error') {
  oauthError.value = true
  oauthErrorMessage.value = route.query.message as string || 'Failed to connect to HubSpot'
}

// Watch for auth to be ready, then check integrations (only once)
let hasCheckedIntegration = false
watch(authLoading, async (loading) => {
  if (!loading && idToken.value && !hasCheckedIntegration) {
    hasCheckedIntegration = true
    await checkHubSpotIntegration()
  }
}, { immediate: true })

// Check if user has HubSpot integration
async function checkHubSpotIntegration() {
  const config = useRuntimeConfig()

  console.log('[HubSpot Check] Starting integration check...')

  if (!idToken.value) {
    console.log('[HubSpot Check] No auth token available')
    checkingIntegration.value = false
    return
  }

  checkingIntegration.value = true
  try {
    console.log('[HubSpot Check] Fetching integrations from API...')
    const data = await $fetch<any[]>(`${config.public.apiBase}/api/v1/integrations`, {
      headers: {
        Authorization: `Bearer ${idToken.value}`
      }
    })

    console.log('[HubSpot Check] Received integrations:', data)

    if (data && Array.isArray(data)) {
      // Log what each integration looks like
      data.forEach((int: any, i: number) => {
        console.log(`[HubSpot Check] Integration ${i}:`, {
          type: int.type,
          status: int.status,
          full: int
        })
      })

      const hubspotIntegration = data.find((int: any) => {
        console.log('[HubSpot Check] Checking integration type:', int.type, 'against hubspot')
        return int.type === 'hubspot'
      })
      console.log('[HubSpot Check] HubSpot integration found:', hubspotIntegration)

      hasHubSpotIntegration.value = data.some((int: any) => int.type === 'hubspot' && int.status === 'active')
      console.log('[HubSpot Check] Has active HubSpot integration:', hasHubSpotIntegration.value)
    }
  } catch (error) {
    console.error('[HubSpot Check] Failed to check integrations:', error)
  } finally {
    checkingIntegration.value = false
    console.log('[HubSpot Check] Check complete. Has integration:', hasHubSpotIntegration.value)
  }
}

// Connect to HubSpot
async function connectHubSpot() {
  const config = useRuntimeConfig()

  if (!idToken.value) {
    oauthError.value = true
    oauthErrorMessage.value = 'You must be logged in to connect HubSpot'
    return
  }

  connecting.value = true
  try {
    const data = await $fetch<{ authorization_url: string }>(`${config.public.apiBase}/api/v1/integrations/hubspot/authorize`, {
      headers: {
        Authorization: `Bearer ${idToken.value}`
      }
    })

    if (data && data.authorization_url) {
      // Redirect to HubSpot OAuth page
      window.location.href = data.authorization_url
    }
  } catch (error) {
    console.error('Failed to get authorization URL:', error)
    oauthError.value = true
    oauthErrorMessage.value = 'Failed to start OAuth flow'
  } finally {
    connecting.value = false
  }
}

// Tab configuration
const tabs = computed(() => [
  { id: 'all', label: 'All Tickets', count: ticketsStore.sortedTickets.length },
  { id: 'negative', label: 'Negative', count: ticketsStore.negativeTickets.length },
  { id: 'positive', label: 'Positive', count: ticketsStore.positiveTickets.length },
  { id: 'neutral', label: 'Neutral', count: ticketsStore.neutralTickets.length }
])

// Filter tickets based on active tab
const filteredTickets = computed(() => {
  switch (activeTab.value) {
    case 'negative':
      return ticketsStore.negativeTickets
    case 'positive':
      return ticketsStore.positiveTickets
    case 'neutral':
      return ticketsStore.neutralTickets
    default:
      return ticketsStore.sortedTickets
  }
})

// Get sentiment badge color classes
function getSentimentColor(sentiment: string | null): string {
  switch (sentiment) {
    case 'very_negative':
      return 'bg-red-100 text-red-800'
    case 'negative':
      return 'bg-red-50 text-red-700'
    case 'neutral':
      return 'bg-gray-100 text-gray-800'
    case 'positive':
      return 'bg-green-50 text-green-700'
    case 'very_positive':
      return 'bg-green-100 text-green-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

// Get sentiment label
function getSentimentLabel(sentiment: string | null): string {
  if (!sentiment) return 'Unknown'
  return sentiment.replace('_', ' ').toUpperCase()
}

// Truncate content to 150 characters
function truncateContent(content: string): string {
  if (content.length <= 150) return content
  return content.substring(0, 150) + '...'
}

// Format relative date
function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays > 0) {
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  } else if (diffHours > 0) {
    return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  } else if (diffMins > 0) {
    return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
  } else {
    return 'Just now'
  }
}

// Format last sync timestamp
function formatLastSync(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 1000 / 60)

  if (diffMins < 1) {
    return 'Just now'
  } else if (diffMins < 60) {
    return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
  } else {
    const hours = Math.floor(diffMins / 60)
    return `${hours} hour${hours > 1 ? 's' : ''} ago`
  }
}

// Handle ticket card click
function handleTicketClick(ticket: Ticket) {
  ticketsStore.selectTicket(ticket)
}

// Handle refresh button
async function handleRefresh() {
  await ticketsStore.importTickets()
}

// Auto-fetch logic on mount
onMounted(async () => {
  // Check if HubSpot is connected
  await checkHubSpotIntegration()

  // Only fetch tickets if HubSpot is connected
  if (hasHubSpotIntegration.value) {
    // First, try to fetch existing tickets
    await ticketsStore.fetchTickets()

    // If no tickets found, automatically import
    if (ticketsStore.tickets.length === 0) {
      await ticketsStore.importTickets()
    }
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
