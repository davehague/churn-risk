# HubSpot OAuth App Setup Guide

**Last Updated:** 2025-11-08
**Status:** Production-ready OAuth configuration

---

## Overview

This guide walks through creating a HubSpot OAuth app using the HubSpot CLI. This enables our multi-tenant SaaS app to authenticate with customer HubSpot accounts and access their support ticket data.

**Prerequisites:**
- HubSpot CLI installed: `npm install -g @hubspot/cli@latest`
- Access to a HubSpot account with app creation permissions
- Terminal access

---

## Step 1: Initialize HubSpot CLI

Authenticate the HubSpot CLI with your HubSpot developer account.

```bash
cd /Users/davidhague/source/churn-risk-app
hs init
```

**Interactive Prompts:**

1. **Choose authentication method:**
   ```
   ? Choose your preferred method of authentication
   ❯ Open HubSpot to copy your personal access key
     Enter existing personal access key
   ```
   - Select: **"Open HubSpot to copy your personal access key"**

2. **Browser opens automatically:**
   - Log in to your HubSpot account (e.g., FlxPoint)
   - HubSpot will display your personal access key
   - Copy the key

3. **Paste the key:**
   ```
   ? Personal access key:
   ```
   - Paste the copied access key
   - Press Enter

4. **Name this account:**
   ```
   ? Enter a unique name for this account:
   ```
   - Enter: **flxpoint** (or your company name)
   - Press Enter

**Result:** Creates `hubspot.config.yml` with your authenticated account.

**Verify Authentication:**
```bash
hs account list
```

You should see your account listed as the default.

---

## Step 2: Create OAuth App Project

Navigate to the HubSpot app directory and create a new project.

```bash
cd /Users/davidhague/source/churn-risk-app/hs-churn-risk
hs project create
```

**Interactive Prompts:**

1. **Base content type:**
   ```
   ? What base content would you like to use?
   ❯ App
     Website theme
     Blog theme
   ```
   - Select: **App**

2. **Distribution type:**
   ```
   ? Where would you like to distribute your app?
   ❯ Marketplace - available for everyone
     Restrict installation to specific HubSpot accounts
   ```
   - Select: **Restrict installation to specific HubSpot accounts**
   - (For MVP, restrict to FlxPoint; change to Marketplace for public launch)

3. **Authentication method:**
   ```
   ? What authentication method would you like to use?
   ❯ OAuth
     Static tokens
   ```
   - Select: **OAuth**

4. **Features to include:**
   ```
   ? What features would you like to use? (Press Space to select, Enter to confirm)
   ◯ Card
   ◯ App Function
   ◯ Settings
   ◯ Webhooks
   ◯ Custom Workflow Action
   ```
   - **Press Enter** without selecting any (we'll configure manually)

5. **Project name:**
   ```
   ? What would you like to name your project?
   ```
   - Enter: **churn-risk-app** (or preferred name)

**Result:** Creates project structure with:
- `public-app.json` - App configuration
- `src/` - App code (if features selected)
- Other boilerplate files

---

## Step 3: Configure OAuth App

Edit the generated `public-app.json` to configure OAuth scopes and settings.

**Location:** `/Users/davidhague/source/churn-risk-app/hs-churn-risk/public-app.json`

### Required Configuration

```json
{
  "name": "Churn Risk App",
  "description": "AI-powered churn risk detection from support tickets",
  "scopes": {
    "required": [
      "crm.objects.contacts.read",
      "crm.objects.companies.read",
      "tickets"
    ]
  },
  "redirectUrls": [
    "http://localhost:8000/api/v1/integrations/hubspot/callback",
    "https://your-production-domain.com/api/v1/integrations/hubspot/callback"
  ],
  "public": false
}
```

### Scope Explanations

| Scope | Purpose |
|-------|---------|
| `crm.objects.contacts.read` | Read contact information associated with support tickets |
| `crm.objects.companies.read` | Read company data for churn risk analysis |
| `tickets` | Read and write access to support tickets |

### Redirect URIs

**Development:**
- `http://localhost:8000/api/v1/integrations/hubspot/callback`

**Production:**
- `https://api.churnriskapp.com/api/v1/integrations/hubspot/callback` (or your domain)

**Important:** Add both development and production URIs before deploying.

---

## Step 4: Upload App to HubSpot

Deploy your app configuration to HubSpot.

```bash
cd /Users/davidhague/source/churn-risk-app/hs-churn-risk
hs project upload
```

**What happens:**
- App configuration uploaded to HubSpot
- Automatic build triggered
- App becomes available in your HubSpot account

**Expected Output:**
```
✔ Project uploaded successfully
✔ Build completed
✔ App is ready for installation
```

---

## Step 5: Get OAuth Credentials

Retrieve the Client ID and Client Secret for your app.

```bash
hs project open
```

**What happens:**
- Opens your app's configuration page in your browser
- Navigate to the **"Auth"** tab

**Copy the following:**
1. **Client ID** - Public identifier (e.g., `a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6`)
2. **Client Secret** - Private key (e.g., `1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p`)

⚠️ **Keep the Client Secret secure!** Never commit it to version control.

---

## Step 6: Configure Backend Environment

Add OAuth credentials to your backend `.env` file.

**File:** `/Users/davidhague/source/churn-risk-app/backend/.env`

```bash
# HubSpot OAuth (Production)
HUBSPOT_CLIENT_ID=a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6
HUBSPOT_CLIENT_SECRET=1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p
HUBSPOT_REDIRECT_URI=http://localhost:8000/api/v1/integrations/hubspot/callback

# Remove or comment out the API key (no longer needed)
# HUBSPOT_API_KEY=da5f1b31-8414-4193-aec3-c5c84dfe2cd3
```

### Update `.env.example`

```bash
# HubSpot OAuth (Production)
HUBSPOT_CLIENT_ID=your-client-id
HUBSPOT_CLIENT_SECRET=your-client-secret
HUBSPOT_REDIRECT_URI=http://localhost:8000/api/v1/integrations/hubspot/callback

# HubSpot API Key (deprecated - only for legacy testing)
# HUBSPOT_API_KEY=your-api-key
```

---

## Step 7: Test OAuth Flow

### Backend Endpoints

Your FastAPI backend already has OAuth endpoints configured:

1. **Get Authorization URL:**
   ```
   GET /api/v1/integrations/hubspot/authorize
   ```
   Returns the HubSpot OAuth URL to redirect users to.

2. **OAuth Callback:**
   ```
   POST /api/v1/integrations/hubspot/callback
   ```
   Handles the callback from HubSpot after user authorizes.

### Manual Test (Using cURL)

**Step 1: Get Authorization URL**
```bash
curl http://localhost:8000/api/v1/integrations/hubspot/authorize
```

**Response:**
```json
{
  "authorization_url": "https://app.hubspot.com/oauth/authorize?client_id=...&redirect_uri=...&scope=..."
}
```

**Step 2: Open URL in Browser**
- Copy the `authorization_url`
- Open in your browser
- Log in to HubSpot and authorize the app
- You'll be redirected to your callback URL with a `code` parameter

**Step 3: Exchange Code for Token**
```bash
curl -X POST http://localhost:8000/api/v1/integrations/hubspot/callback \
  -H "Content-Type: application/json" \
  -d '{
    "code": "CODE_FROM_REDIRECT",
    "redirect_uri": "http://localhost:8000/api/v1/integrations/hubspot/callback"
  }'
```

**Success Response:**
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "integration_type": "hubspot",
  "status": "active",
  "created_at": "2025-11-08T..."
}
```

The access token and refresh token are stored securely in the database.

---

## Step 8: Install App (Optional)

If you want to install the app on your HubSpot account:

```bash
hs project open
```

Navigate to the **"Install"** tab and click **"Install app"**.

This is useful for testing webhooks and other features that require an installed app.

---

## Troubleshooting

### Error: "Invalid client_id"

**Cause:** Client ID in `.env` doesn't match the app's Client ID.

**Fix:**
1. Run `hs project open`
2. Go to "Auth" tab
3. Copy the correct Client ID
4. Update `.env`

### Error: "Redirect URI mismatch"

**Cause:** The redirect URI in the OAuth request doesn't match what's configured in `public-app.json`.

**Fix:**
1. Ensure `HUBSPOT_REDIRECT_URI` in `.env` matches `redirectUrls` in `public-app.json`
2. Re-upload the app: `hs project upload`

### Error: "Insufficient scopes"

**Cause:** App doesn't have required permissions.

**Fix:**
1. Edit `public-app.json` and add missing scopes to `scopes.required`
2. Re-upload: `hs project upload`
3. Re-install the app (tokens need to be regenerated with new scopes)

### Token Expired

**Cause:** Access tokens expire after 6 hours.

**Fix:** Our backend automatically handles token refresh using the `refresh_token`. See `HubSpotClient.refresh_access_token()` in `backend/src/integrations/hubspot.py`.

---

## Production Checklist

Before deploying to production:

- [ ] Update `redirectUrls` in `public-app.json` with production domain
- [ ] Upload updated config: `hs project upload`
- [ ] Update `HUBSPOT_REDIRECT_URI` in production environment variables
- [ ] Store `HUBSPOT_CLIENT_SECRET` in GCP Secret Manager (not .env)
- [ ] Test OAuth flow on production domain
- [ ] Set up webhook endpoints for real-time ticket ingestion
- [ ] Configure webhook subscriptions in `public-app.json`
- [ ] Consider changing distribution from "Restrict" to "Marketplace" for public launch

---

## Useful Commands

| Command | Description |
|---------|-------------|
| `hs account list` | List authenticated HubSpot accounts |
| `hs project upload` | Deploy app configuration changes |
| `hs project open` | Open app settings in browser |
| `hs project create` | Create a new app project |
| `hs auth` | Re-authenticate with HubSpot |

---

## Related Documentation

- [HubSpot OAuth Documentation](https://developers.hubspot.com/docs/api/working-with-oauth)
- [HubSpot CLI Documentation](https://developers.hubspot.com/docs/cli/getting-started)
- [Backend OAuth Implementation](../../backend/src/api/routers/integrations.py)
- [Future OAuth Work](../future-work/oauth-implementation.md)

---

## Notes

**Developer API Key vs OAuth:**
- Developer API Keys are deprecated and have limited permissions
- OAuth is the recommended authentication method for all new apps
- OAuth supports multi-tenant scenarios (multiple customers)

**Private Apps vs Public Apps:**
- Private Apps: Quick testing, single account, access token authentication
- Public Apps (OAuth): Production, multi-account, full OAuth flow
- We're using Public Apps for production-ready multi-tenant support

---

**Created:** 2025-11-08
**Last Tested:** 2025-11-08
**Owner:** David Hague
