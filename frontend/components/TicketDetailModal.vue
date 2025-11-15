<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="ticketsStore.selectedTicket"
        class="fixed inset-0 z-50 overflow-y-auto"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        @click.self="closeModal"
      >
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"/>

        <!-- Modal Container -->
        <div class="flex min-h-full items-center justify-center p-4">
          <div
            ref="modalRef"
            class="relative bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] flex flex-col"
            @click.stop
          >
            <!-- Header -->
            <div class="px-6 py-4 border-b border-gray-200">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <!-- Sentiment Badge with Confidence -->
                  <div class="mb-3">
                    <span
                      :class="[
                        'inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold',
                        getSentimentColor(ticketsStore.selectedTicket.sentiment_score)
                      ]"
                    >
                      {{ getSentimentLabel(ticketsStore.selectedTicket.sentiment_score) }}
                      <span
                        v-if="ticketsStore.selectedTicket.sentiment_confidence"
                        class="ml-2 opacity-90"
                      >
                        ({{ Math.round(ticketsStore.selectedTicket.sentiment_confidence * 100) }}%)
                      </span>
                    </span>
                  </div>

                  <!-- Subject -->
                  <h2 id="modal-title" class="text-2xl font-bold text-gray-900">
                    {{ ticketsStore.selectedTicket.subject }}
                  </h2>
                </div>

                <!-- Close Button -->
                <button
                  class="ml-4 bg-white rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  aria-label="Close modal"
                  @click="closeModal"
                >
                  <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Body (Scrollable) -->
            <div class="flex-1 overflow-y-auto px-6 py-5 space-y-6">
              <!-- Metadata Section -->
              <div class="grid grid-cols-2 gap-4">
                <!-- Created Date -->
                <div>
                  <div class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                    Created
                  </div>
                  <div class="text-sm text-gray-900">
                    {{ formatFullDate(ticketsStore.selectedTicket.created_at) }}
                  </div>
                </div>

                <!-- Status -->
                <div>
                  <div class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                    Status
                  </div>
                  <div>
                    <span
                      :class="[
                        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                        getStatusColor(ticketsStore.selectedTicket.status)
                      ]"
                    >
                      {{ ticketsStore.selectedTicket.status.toUpperCase() }}
                    </span>
                  </div>
                </div>

                <!-- Company -->
                <div v-if="ticketsStore.selectedTicket.company">
                  <div class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                    Company
                  </div>
                  <div class="text-sm text-gray-900 flex items-center">
                    <svg class="h-4 w-4 mr-1.5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    {{ ticketsStore.selectedTicket.company.name }}
                  </div>
                </div>

                <!-- Contact -->
                <div v-if="ticketsStore.selectedTicket.contact">
                  <div class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                    Contact
                  </div>
                  <div class="text-sm text-gray-900">
                    <div class="flex items-center">
                      <svg class="h-4 w-4 mr-1.5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      {{ ticketsStore.selectedTicket.contact.name }}
                    </div>
                    <div class="flex items-center mt-1 text-gray-600">
                      <svg class="h-4 w-4 mr-1.5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      {{ ticketsStore.selectedTicket.contact.email }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- View in HubSpot Button -->
              <div v-if="ticketsStore.selectedTicket.external_url">
                <a
                  :href="ticketsStore.selectedTicket.external_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg class="mr-2 -ml-1 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  View in HubSpot
                </a>
              </div>

              <!-- Content Section -->
              <div>
                <div class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  Ticket Content
                </div>
                <div class="bg-gray-50 rounded-lg p-4">
                  <p class="text-sm text-gray-900 whitespace-pre-wrap leading-relaxed">{{ ticketsStore.selectedTicket.content }}</p>
                </div>
              </div>

              <!-- Analysis Section -->
              <div v-if="ticketsStore.selectedTicket.sentiment_score">
                <div class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
                  Sentiment Analysis
                </div>
                <div class="bg-blue-50 rounded-lg p-4 space-y-3">
                  <!-- Sentiment -->
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-700">Sentiment:</span>
                    <span
                      :class="[
                        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                        getSentimentColor(ticketsStore.selectedTicket.sentiment_score)
                      ]"
                    >
                      {{ getSentimentLabel(ticketsStore.selectedTicket.sentiment_score) }}
                    </span>
                  </div>

                  <!-- Confidence Progress Bar -->
                  <div v-if="ticketsStore.selectedTicket.sentiment_confidence">
                    <div class="flex items-center justify-between mb-1">
                      <span class="text-sm font-medium text-gray-700">Confidence:</span>
                      <span class="text-sm font-medium text-gray-900">
                        {{ Math.round(ticketsStore.selectedTicket.sentiment_confidence * 100) }}%
                      </span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2.5">
                      <div
                        class="h-2.5 rounded-full transition-all"
                        :class="getConfidenceBarColor(ticketsStore.selectedTicket.sentiment_confidence)"
                        :style="{ width: `${ticketsStore.selectedTicket.sentiment_confidence * 100}%` }"
                      />
                    </div>
                  </div>

                  <!-- Analyzed At -->
                  <div v-if="ticketsStore.selectedTicket.sentiment_analyzed_at" class="flex items-center justify-between text-xs text-gray-600">
                    <span>Analyzed at:</span>
                    <span>{{ formatFullDate(ticketsStore.selectedTicket.sentiment_analyzed_at) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
              <button
                class="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                @click="closeModal"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import type { SentimentScore, TicketStatus } from '~/types/ticket'

const ticketsStore = useTicketsStore()
const modalRef = ref<HTMLElement | null>(null)

// Close modal function
function closeModal() {
  ticketsStore.closeTicket()
}

// ESC key handler
function handleEscape(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    closeModal()
  }
}

// Focus trap handler
function handleFocusTrap(event: KeyboardEvent) {
  if (event.key !== 'Tab' || !modalRef.value) return

  const focusableElements = modalRef.value.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  const firstElement = focusableElements[0] as HTMLElement
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

  if (event.shiftKey && document.activeElement === firstElement) {
    event.preventDefault()
    lastElement.focus()
  } else if (!event.shiftKey && document.activeElement === lastElement) {
    event.preventDefault()
    firstElement.focus()
  }
}

// Watch for modal open/close to manage event listeners
watch(
  () => ticketsStore.selectedTicket,
  (newValue) => {
    if (newValue) {
      // Modal opened - add listeners and prevent body scroll
      document.addEventListener('keydown', handleEscape)
      document.addEventListener('keydown', handleFocusTrap)
      document.body.style.overflow = 'hidden'

      // Focus first focusable element
      nextTick(() => {
        const firstButton = modalRef.value?.querySelector('button') as HTMLElement
        firstButton?.focus()
      })
    } else {
      // Modal closed - remove listeners and restore body scroll
      document.removeEventListener('keydown', handleEscape)
      document.removeEventListener('keydown', handleFocusTrap)
      document.body.style.overflow = ''
    }
  }
)

// Cleanup on unmount
onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
  document.removeEventListener('keydown', handleFocusTrap)
  document.body.style.overflow = ''
})

// Get sentiment badge color classes
function getSentimentColor(sentiment: SentimentScore | null): string {
  switch (sentiment) {
    case 'very_negative':
      return 'bg-red-600 text-white'
    case 'negative':
      return 'bg-red-400 text-white'
    case 'neutral':
      return 'bg-gray-400 text-white'
    case 'positive':
      return 'bg-green-400 text-white'
    case 'very_positive':
      return 'bg-green-600 text-white'
    default:
      return 'bg-gray-400 text-white'
  }
}

// Get sentiment label
function getSentimentLabel(sentiment: SentimentScore | null): string {
  if (!sentiment) return 'UNKNOWN'
  return sentiment.replace('_', ' ').toUpperCase()
}

// Get status badge color
function getStatusColor(status: TicketStatus): string {
  switch (status) {
    case 'new':
      return 'bg-blue-100 text-blue-800'
    case 'open':
      return 'bg-yellow-100 text-yellow-800'
    case 'waiting':
      return 'bg-purple-100 text-purple-800'
    case 'closed':
      return 'bg-gray-100 text-gray-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

// Get confidence bar color based on confidence level
function getConfidenceBarColor(confidence: number): string {
  if (confidence >= 0.8) {
    return 'bg-green-500'
  } else if (confidence >= 0.6) {
    return 'bg-yellow-500'
  } else {
    return 'bg-red-500'
  }
}

// Format full date with timestamp
function formatFullDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZoneName: 'short'
  })
}
</script>

<style scoped>
/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.modal-enter-from .bg-white,
.modal-leave-to .bg-white {
  transform: scale(0.95);
  opacity: 0;
}
</style>
