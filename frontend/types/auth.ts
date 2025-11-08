export interface RegisterFormData {
  email: string
  password: string
  confirmPassword: string
  name: string
  companyName: string
  subdomain: string
}

export interface RegisterRequest {
  email: string
  password: string
  name: string
  company_name: string
  subdomain: string
}

export interface SubdomainCheckResponse {
  available: boolean
  subdomain: string
}
