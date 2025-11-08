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

**Issue:** "User exists in Firebase but not in database"
**Solution:** This means registration partially failed. Delete the Firebase user and try again.

**Issue:** Token expired
**Solution:** Firebase SDK automatically refreshes tokens. If it fails, user will be logged out.
