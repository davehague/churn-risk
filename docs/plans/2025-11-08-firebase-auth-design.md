# Firebase Authentication Design

**Date:** 2025-11-08
**Status:** Approved
**Type:** Self-service tenant creation with email/password auth

---

## Overview

Implement complete Firebase authentication flow with self-service tenant creation. Users register with email/password, automatically creating a new tenant and becoming the admin. Registration collects email, password, name, company name, and subdomain (auto-suggested but editable).

---

## Backend API

### New Endpoints

**POST `/api/v1/auth/register`**
- **Purpose:** Register new user and create tenant
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePass123",
    "name": "John Doe",
    "company_name": "Acme Corp",
    "subdomain": "acme"
  }
  ```
- **Process:**
  1. Validate subdomain is unique and valid format
  2. Create Firebase user via Admin SDK
  3. Create Tenant record with company_name and subdomain
  4. Create User record linked to Firebase UID and tenant
  5. Set user role to ADMIN
- **Response:** Success message with instructions to login

**POST `/api/v1/auth/check-subdomain`**
- **Purpose:** Real-time subdomain availability check
- **Request Body:**
  ```json
  {
    "subdomain": "acme"
  }
  ```
- **Response:**
  ```json
  {
    "available": true
  }
  ```

### Registration Flow

1. Frontend calls `/check-subdomain` (debounced validation as user types)
2. User submits registration form
3. Backend creates Firebase user, tenant, and database user record
4. Frontend redirects to `/login` with success message
5. User logs in with Firebase Client SDK → receives JWT token
6. Token used for all subsequent API calls

**Key Principle:** Backend creates Firebase user via Admin SDK (server-side), but login happens client-side via Firebase Client SDK. This separates registration (server) from authentication (client).

---

## Frontend Implementation

### Firebase Client SDK Integration

**Plugin** (`frontend/plugins/firebase.client.ts`):
- Initialize Firebase app with config from runtime config
- Export `auth` instance for use across app
- Client-side only (`.client.ts` suffix)

**Composable** (`frontend/composables/useAuth.ts`):
- `signInWithEmailAndPassword()` - login function
- `signOut()` - logout function
- `currentUser` - reactive ref to current Firebase user
- `idToken` - reactive ref to JWT token for API calls
- `onAuthStateChanged` listener to track auth state
- Automatic token refresh (handled by Firebase SDK)

**API Client** (`frontend/composables/useApi.ts`):
- Wrapper around `$fetch` with automatic Authorization header
- Uses `idToken` from `useAuth` composable
- Handles 401 errors by redirecting to login

**Environment Variables** (`.env`):
```
NUXT_PUBLIC_FIREBASE_API_KEY=AIzaSyAsAfrqGZdfEFpMfA7xPPWGck4l9x3PsCM
NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN=churn-risk.firebaseapp.com
NUXT_PUBLIC_FIREBASE_PROJECT_ID=churn-risk
```

---

## Pages & Routing

### Pages

**`/pages/index.vue`** - Landing page:
- Check authentication state
- Authenticated → redirect to `/dashboard`
- Unauthenticated → show hero with "Get Started" button → `/register`

**`/pages/register.vue`** - Registration form:
- Fields: email, password, confirm password, name, company name, subdomain
- Subdomain auto-populated from company name (user can edit)
- Real-time subdomain validation with availability indicator
- Submit → POST to `/api/v1/auth/register`
- Success → redirect to `/login` with success toast
- "Already have an account? Login" link

**`/pages/login.vue`** - Login form:
- Fields: email, password
- Submit → Firebase SDK `signInWithEmailAndPassword()`
- Success → get JWT token → redirect to `/dashboard`
- "Don't have an account? Sign up" link
- No password reset for MVP

### Auth Middleware

**`/middleware/auth.global.ts`**:
- Runs on every route change
- Protected routes without auth → redirect to `/login`
- Logged in user visits `/login` or `/register` → redirect to `/dashboard`

---

## State Management

### Pinia Store (`stores/user.ts`)

**State:**
- `currentUser`: User object from database
- `tenant`: Tenant object
- `loading`: boolean

**Actions:**
- `fetchCurrentUser()`: Calls `/api/v1/me` to get full user + tenant data
- `logout()`: Signs out from Firebase, clears state, redirects to `/login`

### Auth Flow Sequence

1. User logs in → Firebase Client SDK authenticates
2. Receive JWT token from Firebase
3. Call `/api/v1/me` with token to fetch User + Tenant from database
4. Store in Pinia
5. Redirect to `/dashboard`

---

## Validation Rules

### Email
- Valid email format
- Uniqueness enforced by Firebase

### Password
- Minimum 8 characters
- At least one uppercase, one lowercase, one number
- Enforced by Firebase, but show requirements in UI

### Name
- Required
- 2-255 characters

### Company Name
- Required
- 2-255 characters

### Subdomain
- Required
- 3-63 characters
- Lowercase alphanumeric and hyphens only
- Cannot start or end with hyphen
- Regex: `^[a-z0-9][a-z0-9-]*[a-z0-9]$`
- Real-time uniqueness check via API

---

## Error Handling

### Registration Errors

- **Subdomain taken:** Inline validation shows error before submit
- **Email already exists:** Firebase error → "Email already in use"
- **Weak password:** Firebase error → show password requirements
- **Network error:** "Unable to register. Please try again."

### Login Errors

- **Wrong password:** Firebase error → "Invalid email or password"
- **User not found:** "Invalid email or password" (don't reveal which)
- **User in Firebase but not database:** "Account setup incomplete. Contact support."

### Token Errors

- **Expired token:** Automatic refresh by Firebase SDK
- **Invalid token:** Logout user, redirect to `/login`

---

## Testing Strategy

### Backend Tests (`tests/integration/test_auth_registration.py`)

- Test successful registration creates tenant + user
- Test duplicate subdomain rejection
- Test duplicate email rejection
- Test invalid subdomain format rejection
- Test user role is set to ADMIN

### Frontend Manual Testing

- Register new account → verify redirect to login
- Login → verify redirect to dashboard
- Logout → verify redirect to login
- Access protected route while logged out → verify redirect to login
- Subdomain validation → type invalid characters, verify error
- Subdomain availability → try taken subdomain, verify error

**Note:** No automated E2E tests for MVP. Manual testing is sufficient initially.

---

## Implementation Notes

- Backend uses Firebase Admin SDK for user creation (server-side)
- Frontend uses Firebase Client SDK for authentication (client-side)
- JWT tokens are automatically refreshed by Firebase SDK
- No email verification for MVP (can add later)
- No password reset for MVP (can add later)
- No multi-user invitations for MVP (admin is only user initially)

---

## Future Enhancements (Post-MVP)

- Email verification on registration
- Password reset flow
- User invitation system for multi-user tenants
- Social auth providers (Google, GitHub)
- Two-factor authentication
- Session management dashboard
