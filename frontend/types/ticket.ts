export enum TicketStatus {
  NEW = 'new',
  OPEN = 'open',
  WAITING = 'waiting',
  CLOSED = 'closed'
}

export enum SentimentScore {
  VERY_NEGATIVE = 'very_negative',
  NEGATIVE = 'negative',
  NEUTRAL = 'neutral',
  POSITIVE = 'positive',
  VERY_POSITIVE = 'very_positive'
}

export interface Company {
  id: string
  name: string
}

export interface Contact {
  id: string
  name: string
  email: string
}

export interface Ticket {
  id: string
  external_id: string
  subject: string
  content: string
  sentiment_score: SentimentScore | null
  sentiment_confidence: number | null
  sentiment_analyzed_at: string | null
  created_at: string
  status: TicketStatus
  company: Company | null
  contact: Contact | null
  external_url: string | null
}

export interface TicketListResponse {
  tickets: Ticket[]
  total: number
}

export interface ImportTicketsResponse {
  imported: number
  analyzed: number
  skipped: number
  failed: number
}
