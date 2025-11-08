 ✅ Already Set (presumably):

  - HUBSPOT_API_KEY - You just added this

  ❓ Need to Configure:

  1. Database:
  DATABASE_URL=postgresql://postgres:password@localhost:5432/churn_risk_dev
  - Do you have PostgreSQL running locally?
  - Or should I help you start it with Docker?

  2. Firebase:
  FIREBASE_PROJECT_ID=your-project-id
  FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
  - Do you have a Firebase project created?
  - Do you have the credentials JSON file downloaded?

  3. OpenRouter:
  OPENROUTER_API_KEY=sk-or-xxx
  - Do you have an OpenRouter account?
  - Have you created an API key?

  4. App Settings (these have defaults, but you might want to customize):
  SECRET_KEY=your-secret-key-change-in-production  # Generate a random string
  CORS_ORIGINS=http://localhost:3000,http://localhost:8000