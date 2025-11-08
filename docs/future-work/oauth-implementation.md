# HubSpot OAuth Implementation (Future Work)

**Status:** Not implemented in MVP
**Priority:** High (required for production)
**Estimated Effort:** 2-3 days

## Current State

We're using HubSpot's **Developer API Key** for testing/development:
- Simple authentication with `HUBSPOT_API_KEY`
- Works for all API calls (tickets, companies, contacts)
- Good for smoke testing and development
- **Not suitable for production** (keys expire, no per-user auth)

## What We Need to Build

### 1. HubSpot App Configuration
- Create a HubSpot App in the developer portal
- Get OAuth Client ID and Client Secret
- Configure redirect URI (callback endpoint)
- Request proper scopes:
  - `crm.objects.contacts.read`
  - `crm.objects.companies.read`
  - `tickets` (read/write)
  - `crm.schemas.contacts.read`
  - `webhooks` (for real-time updates)

### 2. Backend Changes

**Update Integration Model** (`backend/src/models/integration.py`):
```python
class Integration(Base):
    # Add OAuth token fields
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Encrypt tokens at rest
    def set_access_token(self, token: str):
        self.access_token = encrypt(token)  # Use GCP Secret Manager or similar
```

**Token Refresh Logic** (`backend/src/integrations/hubspot.py`):
```python
async def ensure_valid_token(integration: Integration) -> str:
    """Check if token is expired, refresh if needed."""
    if integration.token_expires_at < datetime.now(timezone.utc):
        # Refresh the token
        new_tokens = await HubSpotClient.refresh_access_token(integration.refresh_token)
        # Update database
        integration.access_token = new_tokens['access_token']
        integration.refresh_token = new_tokens['refresh_token']
        integration.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=new_tokens['expires_in'])
        db.commit()
    return integration.access_token
```

**Router Updates** (`backend/src/api/routers/integrations.py`):
- Uncomment OAuth endpoints (already scaffolded in Task 5)
- Add error handling for OAuth failures
- Add CSRF protection (state parameter)

### 3. Frontend Changes

**Onboarding Flow** (`frontend/pages/onboarding/hubspot.vue`):
```vue
<template>
  <div>
    <h2>Connect Your HubSpot Account</h2>
    <p>We need access to your support tickets to analyze churn risk.</p>

    <button @click="connectHubSpot">
      Connect HubSpot
    </button>
  </div>
</template>

<script setup>
const connectHubSpot = async () => {
  // Get authorization URL from backend
  const { url } = await $fetch('/api/v1/integrations/hubspot/authorize')

  // Redirect user to HubSpot OAuth page
  window.location.href = url
}
</script>
```

**Callback Handler** (`frontend/pages/oauth/hubspot/callback.vue`):
```vue
<script setup>
const route = useRoute()
const router = useRouter()

onMounted(async () => {
  const { code, state } = route.query

  if (!code) {
    // Handle error
    return router.push('/onboarding?error=oauth_failed')
  }

  try {
    // Send code to backend to exchange for tokens
    await $fetch('/api/v1/integrations/hubspot/callback', {
      method: 'POST',
      body: { code, redirect_uri: window.location.origin + '/oauth/hubspot/callback' }
    })

    // Redirect to next onboarding step
    router.push('/onboarding/analyze')
  } catch (error) {
    console.error('OAuth callback failed:', error)
    router.push('/onboarding?error=oauth_failed')
  }
})
</script>
```

### 4. Security Considerations

**CSRF Protection:**
- Generate random `state` parameter before redirect
- Store in session/localStorage
- Validate on callback

**Token Storage:**
- Never expose tokens to frontend
- Encrypt tokens at rest in database
- Use GCP Secret Manager for production
- Rotate tokens regularly

**Scopes:**
- Request minimum necessary scopes
- Document why each scope is needed
- Handle scope changes gracefully

### 5. Testing Plan

**Manual Testing:**
1. Start OAuth flow from onboarding page
2. Verify redirect to HubSpot works
3. Grant permissions on HubSpot page
4. Verify callback succeeds and tokens stored
5. Test token refresh logic (set expiry to 1 minute)
6. Test revoked token handling

**Automated Testing:**
- Mock OAuth endpoints in tests
- Test token refresh logic
- Test error cases (denied access, invalid code, etc.)

### 6. Migration Path

**From Developer API Key to OAuth:**

1. Keep both authentication methods during transition
2. Add `auth_type` field to Integration model (`api_key` vs `oauth`)
3. Update HubSpotClient to check auth type:
```python
@classmethod
def from_integration(cls, integration: Integration):
    if integration.auth_type == "api_key":
        return cls(api_key=integration.api_key)
    else:
        return cls(access_token=integration.access_token)
```
4. Migrate existing integrations after OAuth is tested

### 7. Rollout Checklist

- [ ] Create HubSpot App in developer portal
- [ ] Add OAuth client credentials to `.env`
- [ ] Update Integration model with token fields
- [ ] Implement token refresh logic
- [ ] Add CSRF protection
- [ ] Build frontend OAuth flow
- [ ] Test with FlxPoint HubSpot account
- [ ] Document scope requirements
- [ ] Add error handling for common failures
- [ ] Set up monitoring for token refresh failures
- [ ] Update onboarding documentation
- [ ] Migrate from API key to OAuth

## References

- [HubSpot OAuth Documentation](https://developers.hubspot.com/docs/api/working-with-oauth)
- [HubSpot App Scopes](https://developers.hubspot.com/docs/api/working-with-oauth#scopes)
- Task 5 implementation: `backend/src/api/routers/integrations.py`

---

**Created:** 2025-11-07
**Last Updated:** 2025-11-07
