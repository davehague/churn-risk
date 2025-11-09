# Frontend Development Guide

This file provides guidance to Claude Code when working with the frontend codebase.

## Project Overview

Vue 3 / Nuxt 3 application for the Churn Risk SaaS platform. Uses Firebase Client SDK for authentication and connects to FastAPI backend.

## Tech Stack

- **Framework**: Nuxt 3 (Vue 3 with Composition API)
- **State Management**: Pinia
- **Authentication**: Firebase Client SDK
- **Styling**: Tailwind CSS
- **API Client**: Native `$fetch` (Nuxt's built-in fetch wrapper)

## Authentication Pattern

**CRITICAL**: All authenticated API calls MUST use this exact pattern:

```typescript
async function myApiCall() {
  const { idToken } = useAuth()
  const config = useRuntimeConfig()

  if (!idToken.value) {
    console.error('No auth token available')
    return
  }

  try {
    const data = await $fetch<ResponseType>(`${config.public.apiBase}/api/v1/endpoint`, {
      headers: {
        Authorization: `Bearer ${idToken.value}`
      }
    })

    // Handle response
  } catch (error) {
    console.error('API call failed:', error)
    // Handle error
  }
}
```

**DO NOT**:
- ❌ Use `useFetch` with `useRequestHeaders(['cookie'])` - This doesn't send the Firebase token
- ❌ Hardcode the base URL - Always use `config.public.apiBase`
- ❌ Forget to check if `idToken.value` exists before making the call
- ❌ Use cookies for authentication - We use Bearer tokens

**DO**:
- ✅ Use `$fetch` for all API calls
- ✅ Get token from `useAuth()` composable
- ✅ Add `Authorization: Bearer ${idToken.value}` header to EVERY authenticated request
- ✅ Use `config.public.apiBase` for the API base URL
- ✅ Check `idToken.value` exists before making requests

## Common Patterns

### Making Authenticated API Calls

**Reference Implementation**: See `stores/user.ts` line 25 for the canonical example.

```typescript
// GET request
const data = await $fetch<User>(`${config.public.apiBase}/api/v1/me`, {
  headers: {
    Authorization: `Bearer ${idToken.value}`
  }
})

// POST request
const result = await $fetch<Response>(`${config.public.apiBase}/api/v1/tickets/import`, {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${idToken.value}`
  },
  body: { /* payload */ }
})
```

### Using Pinia Stores

```typescript
// In component
const ticketsStore = useTicketsStore()
const userStore = useUserStore()

// Access state
ticketsStore.tickets
userStore.currentUser

// Call actions
await ticketsStore.fetchTickets()
await userStore.fetchCurrentUser()
```

### Page Structure

```vue
<template>
  <!-- UI here -->
</template>

<script setup lang="ts">
// Imports
import type { MyType } from '~/types/mytype'

// Define page meta
definePageMeta({
  layout: 'default'
})

// Reactive state
const loading = ref(false)

// Composables
const { idToken } = useAuth()
const config = useRuntimeConfig()

// Functions
async function myFunction() {
  // Implementation
}

// Lifecycle
onMounted(async () => {
  // Initialization
})
</script>
```

## Project Structure

```
frontend/
├── pages/           # File-based routing
│   ├── index.vue    # Landing page (/)
│   ├── login.vue    # Login page (/login)
│   ├── register.vue # Registration (/register)
│   └── dashboard.vue # Dashboard (/dashboard)
├── components/      # Reusable components
├── composables/     # Composition API composables
│   └── useAuth.ts   # Firebase auth composable
├── stores/          # Pinia stores
│   ├── user.ts      # User state
│   └── tickets.ts   # Tickets state
├── types/           # TypeScript type definitions
├── layouts/         # Layout components
└── public/          # Static assets
```

## API Integration

### Base URL Configuration

The API base URL is configured in `nuxt.config.ts`:

```typescript
runtimeConfig: {
  public: {
    apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000'
  }
}
```

Access it with:
```typescript
const config = useRuntimeConfig()
const apiUrl = config.public.apiBase
```

### Error Handling

Always handle 401 errors (expired/invalid tokens):

```typescript
try {
  const data = await $fetch(/* ... */)
} catch (error: any) {
  if (error?.statusCode === 401) {
    const { signOut } = useAuth()
    await signOut()
    navigateTo('/login')
  }
}
```

## Firebase Authentication

### Auth Composable

The `useAuth()` composable provides:
- `user` - Current Firebase user (reactive)
- `idToken` - Current Firebase ID token (reactive)
- `isAuthenticated` - Boolean state
- `signIn(email, password)` - Sign in method
- `signUp(email, password)` - Sign up method
- `signOut()` - Sign out method

### Protected Routes

Use middleware to protect routes:

```typescript
definePageMeta({
  middleware: 'auth' // Requires authentication
})
```

## Common Components

### TicketDetailModal

Displays ticket details in a modal. Controlled by the tickets store:

```typescript
// Show modal
ticketsStore.selectTicket(ticket)

// Modal automatically shows when selectedTicket is set
```

## Styling Guidelines

### Tailwind CSS

Use Tailwind utility classes for all styling:

```vue
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <h1 class="text-3xl font-bold text-gray-900">Title</h1>
</div>
```

### Responsive Design

Always consider mobile-first responsive design:
- `sm:` - Small screens (640px+)
- `md:` - Medium screens (768px+)
- `lg:` - Large screens (1024px+)
- `xl:` - Extra large screens (1280px+)

## Development Commands

```bash
npm run dev         # Start dev server (localhost:3000)
npm run build       # Production build
npm run typecheck   # TypeScript validation
npm run lint        # ESLint
```

## TypeScript

### Type Definitions

Types are defined in `types/` directory:
- `types/user.ts` - User and Tenant types
- `types/ticket.ts` - Ticket and related types

### Type Imports

```typescript
import type { User, Tenant } from '~/types/user'
import type { Ticket } from '~/types/ticket'
```

## Key Reminders

1. **Always use `$fetch` with `Authorization: Bearer ${idToken.value}` for authenticated API calls**
2. Never hardcode API URLs - use `config.public.apiBase`
3. Check `idToken.value` exists before making authenticated requests
4. Handle 401 errors by signing out and redirecting to login
5. Use Pinia stores for shared state
6. Follow mobile-first responsive design
7. Use TypeScript types from `types/` directory
8. Use Tailwind CSS for all styling

## OAuth Flow (HubSpot Integration)

When implementing OAuth flows:

1. **Authorization Request**:
   ```typescript
   // Get auth URL from backend (authenticated request!)
   const data = await $fetch(`${config.public.apiBase}/api/v1/integrations/hubspot/authorize`, {
     headers: {
       Authorization: `Bearer ${idToken.value}`
     }
   })

   // Redirect to OAuth provider
   window.location.href = data.authorization_url
   ```

2. **Callback Handling**:
   ```typescript
   // Backend handles callback and redirects back to frontend with query params
   const route = useRoute()

   if (route.query.hubspot === 'connected') {
     // Show success message
   } else if (route.query.hubspot === 'error') {
     // Show error message
   }
   ```

3. **Check Integration Status**:
   ```typescript
   // Always use authenticated request
   const integrations = await $fetch(`${config.public.apiBase}/api/v1/integrations`, {
     headers: {
       Authorization: `Bearer ${idToken.value}`
     }
   })
   ```

## Debugging

### Common Issues

**403 Forbidden on API calls**:
- ❌ Missing or incorrect `Authorization` header
- ✅ Add `Authorization: Bearer ${idToken.value}` to headers

**401 Unauthorized**:
- Token expired or invalid
- User not logged in
- Sign out and redirect to login

**CORS errors**:
- Backend CORS not configured correctly
- Check `CORS_ORIGINS` in backend `.env`

### Browser Console

Check these in browser console:
```javascript
// Check if user is logged in
const { user, idToken } = useAuth()
console.log('User:', user.value)
console.log('Token:', idToken.value)

// Check API base URL
const config = useRuntimeConfig()
console.log('API Base:', config.public.apiBase)
```

## Testing

When making changes that affect authentication or API calls:

1. Test login/logout flow
2. Test protected routes redirect to login when not authenticated
3. Test API calls with valid token
4. Test API calls handle 401 errors correctly
5. Test OAuth flows complete successfully

## References

- **Nuxt 3 Docs**: https://nuxt.com
- **Vue 3 Docs**: https://vuejs.org
- **Pinia Docs**: https://pinia.vuejs.org
- **Firebase Client SDK**: https://firebase.google.com/docs/web/setup
- **Tailwind CSS**: https://tailwindcss.com
