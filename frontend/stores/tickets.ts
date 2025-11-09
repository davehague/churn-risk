import { defineStore } from 'pinia'
import type {
  Ticket,
  TicketListResponse,
  ImportTicketsResponse,
  SentimentScore
} from '~/types/ticket'

interface TicketsState {
  tickets: Ticket[]
  loading: boolean
  importing: boolean
  selectedTicket: Ticket | null
  lastSync: Date | null
  error: string | null
}

export const useTicketsStore = defineStore('tickets', {
  state: (): TicketsState => ({
    tickets: [],
    loading: false,
    importing: false,
    selectedTicket: null,
    lastSync: null,
    error: null
  }),

  getters: {
    /**
     * Filter tickets by negative sentiment (negative or very_negative)
     */
    negativeTickets: (state): Ticket[] => {
      return state.tickets.filter(ticket =>
        ticket.sentiment_score === 'negative' ||
        ticket.sentiment_score === 'very_negative'
      )
    },

    /**
     * Filter tickets by positive sentiment (positive or very_positive)
     */
    positiveTickets: (state): Ticket[] => {
      return state.tickets.filter(ticket =>
        ticket.sentiment_score === 'positive' ||
        ticket.sentiment_score === 'very_positive'
      )
    },

    /**
     * Filter tickets by neutral sentiment
     */
    neutralTickets: (state): Ticket[] => {
      return state.tickets.filter(ticket =>
        ticket.sentiment_score === 'neutral'
      )
    },

    /**
     * Get tickets sorted by creation date (newest first)
     */
    sortedTickets: (state): Ticket[] => {
      return [...state.tickets].sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
    }
  },

  actions: {
    /**
     * Fetch tickets from the backend with optional sentiment filter
     * @param sentiment - Optional sentiment filter (positive, negative, neutral, very_positive, very_negative)
     * @param limit - Maximum number of tickets to fetch (default: 100)
     * @param offset - Pagination offset (default: 0)
     */
    async fetchTickets(
      sentiment?: SentimentScore,
      limit: number = 100,
      offset: number = 0
    ): Promise<void> {
      const { idToken } = useAuth()
      const config = useRuntimeConfig()

      if (!idToken.value) {
        this.error = 'Not authenticated'
        return
      }

      this.loading = true
      this.error = null

      try {
        // Build query parameters
        const params: Record<string, string> = {
          limit: limit.toString(),
          offset: offset.toString()
        }

        if (sentiment) {
          params.sentiment = sentiment
        }

        const queryString = new URLSearchParams(params).toString()
        const url = `${config.public.apiBase}/api/v1/tickets?${queryString}`

        const data = await $fetch<TicketListResponse>(url, {
          headers: {
            Authorization: `Bearer ${idToken.value}`
          }
        })

        this.tickets = data.tickets
        this.lastSync = new Date()
      } catch (error: any) {
        console.error('Failed to fetch tickets:', error)
        this.error = error.message || 'Failed to fetch tickets'

        // Handle 401 - token expired or invalid
        if (error?.statusCode === 401) {
          const { signOut } = useAuth()
          await signOut()
        }
      } finally {
        this.loading = false
      }
    },

    /**
     * Import tickets from HubSpot and analyze with AI
     * This triggers the backend to fetch tickets from the last 7 days
     */
    async importTickets(): Promise<ImportTicketsResponse | null> {
      const { idToken } = useAuth()
      const config = useRuntimeConfig()

      if (!idToken.value) {
        this.error = 'Not authenticated'
        return null
      }

      this.importing = true
      this.error = null

      try {
        const data = await $fetch<ImportTicketsResponse>(
          `${config.public.apiBase}/api/v1/tickets/import`,
          {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${idToken.value}`
            }
          }
        )

        // After successful import, fetch the updated tickets
        await this.fetchTickets()

        return data
      } catch (error: any) {
        console.error('Failed to import tickets:', error)
        this.error = error.message || 'Failed to import tickets'

        // Handle specific error cases
        if (error?.statusCode === 401) {
          const { signOut } = useAuth()
          await signOut()
        } else if (error?.statusCode === 404) {
          this.error = 'HubSpot integration not connected. Please connect HubSpot first.'
        } else if (error?.statusCode === 429) {
          this.error = 'Rate limit reached. Please try again later.'
        }

        return null
      } finally {
        this.importing = false
      }
    },

    /**
     * Select a ticket to display in the detail modal
     * @param ticket - The ticket to select
     */
    selectTicket(ticket: Ticket): void {
      this.selectedTicket = ticket
    },

    /**
     * Close the ticket detail modal
     */
    closeTicket(): void {
      this.selectedTicket = null
    },

    /**
     * Clear all tickets and reset state
     */
    clearTickets(): void {
      this.tickets = []
      this.selectedTicket = null
      this.lastSync = null
      this.error = null
    }
  }
})
