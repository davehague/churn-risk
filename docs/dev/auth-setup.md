# Authentication Setup

## Overview

The app uses Firebase Authentication for user login and JWT tokens for API authentication.

## User Registration Flow

1. User fills out registration form in frontend
2. Frontend validates subdomain availability via `/api/v1/auth/check-subdomain`
3. User submits registration
4. Backend creates Firebase user via Admin SDK
5. Backend creates Tenant and User records in database
6. User is redirected to login page
7. User logs in via Firebase Client SDK
8. Frontend gets JWT token from Firebase
9. Frontend uses token for all API requests

## Environment Variables

**Backend (.env):**
```
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
```

**Frontend (.env):**
```
NUXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NUXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
```

## Testing

Run auth tests:
```bash
cd backend
poetry run pytest tests/integration/test_auth_registration.py -v
```

## Troubleshooting

**Issue:** "The default Firebase app does not exist"
**Solution:** Check that `FIREBASE_CREDENTIALS_PATH` points to the correct location. If backend is in `backend/` subdirectory and credentials are in project root, use `../firebase-credentials.json` (not `./firebase-credentials.json`).

**Issue:** "No auth provider found for the given identifier (CONFIGURATION_NOT_FOUND)"
**Solution:** Enable Email/Password authentication in Firebase Console:
1. Go to Firebase Console → Authentication → Sign-in method
2. Click on "Email/Password"
3. Enable the first toggle (Email/Password)
4. Save

**Issue:** "User exists in Firebase but not in database"
**Solution:** This means registration partially failed. Delete the Firebase user and try again.

**Issue:** Token expired
**Solution:** Firebase SDK automatically refreshes tokens. If it fails, user will be logged out.

**Issue:** Dashboard shows "Welcome, !" with no user data
**Solution:** This was fixed in commit 79ca45c. The login flow now explicitly calls `fetchCurrentUser()` after Firebase authentication. If you still see this, check browser console for 401 errors on `/api/v1/me` endpoint.

**Issue:** Firebase re-initialization error during development (HMR)
**Solution:** This is already handled in `plugins/firebase.client.ts` with `getApps()` guard. If you see this error, verify the plugin has: `const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0]`
