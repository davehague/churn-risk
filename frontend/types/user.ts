export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'member' | 'viewer'
  tenant_id: string
}

export interface Tenant {
  id: string
  name: string
  subdomain: string
  plan_tier: string
}
