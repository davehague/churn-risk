export enum IntegrationType {
  HUBSPOT = 'hubspot',
  ZENDESK = 'zendesk',
  HELPSCOUT = 'helpscout'
}

export enum IntegrationStatus {
  ACTIVE = 'active',
  ERROR = 'error',
  DISCONNECTED = 'disconnected'
}

export interface Integration {
  id: string
  type: IntegrationType
  status: IntegrationStatus
  last_synced_at: string | null
  created_at: string
}
