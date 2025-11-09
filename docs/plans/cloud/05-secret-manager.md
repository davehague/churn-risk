# 05 - Secret Manager Setup

**Estimated Time:** 20-25 minutes
**Cost:** Free (first 6 secrets, then $0.06/secret/month)
**Prerequisites:** Guides 01-04 completed

---

## Overview

Store sensitive credentials securely in Google Cloud Secret Manager. This is more secure than environment variables and provides audit logging.

**What You'll Store:**
- Firebase credentials JSON
- HubSpot OAuth client secret
- OpenRouter API key
- Cloud SQL database password

**Why Secret Manager:**
- ✅ Encrypted at rest and in transit
- ✅ Version control for secrets
- ✅ Audit logging (who accessed what, when)
- ✅ Fine-grained IAM permissions
- ✅ Automatic rotation support

---

## Step 1: Enable Secret Manager API

### 1.1 Enable via gcloud

```bash
gcloud services enable secretmanager.googleapis.com
```

**Expected output:**
```
Operation "operations/..." finished successfully.
```

### 1.2 Verify API Enabled

```bash
gcloud services list --enabled | grep secretmanager
```

**Should show:**
```
secretmanager.googleapis.com  Secret Manager API
```

---

## Step 2: Create Secrets

### 2.1 Firebase Credentials

**Prepare the secret value:**

Your Firebase credentials are in `firebase-credentials.json` (at project root).

**Create secret:**

```bash
gcloud secrets create firebase-credentials \
    --replication-policy="automatic" \
    --data-file="../firebase-credentials.json"
```

**Expected output:**
```
Created version [1] of the secret [firebase-credentials].
```

**Important:** We use `--data-file` because the credentials are JSON format (multi-line).

### 2.2 HubSpot OAuth Client Secret

**Get the value from your .env file:**

```bash
# View your current HubSpot client secret
grep HUBSPOT_CLIENT_SECRET backend/.env
```

**Create secret:**

```bash
echo -n "YOUR_HUBSPOT_CLIENT_SECRET" | gcloud secrets create hubspot-client-secret \
    --replication-policy="automatic" \
    --data-file=-
```

**Example:**
```bash
echo -n "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p" | gcloud secrets create hubspot-client-secret \
    --replication-policy="automatic" \
    --data-file=-
```

**Expected output:**
```
Created version [1] of the secret [hubspot-client-secret].
```

**Note:** `echo -n` prevents adding a newline character. `-` means read from stdin.

### 2.3 OpenRouter API Key

```bash
echo -n "YOUR_OPENROUTER_API_KEY" | gcloud secrets create openrouter-api-key \
    --replication-policy="automatic" \
    --data-file=-
```

**Example:**
```bash
echo -n "sk-or-v1-abc123def456..." | gcloud secrets create openrouter-api-key \
    --replication-policy="automatic" \
    --data-file=-
```

### 2.4 Database Password

Use the `churn_risk_app` user password you created in Guide 04:

```bash
echo -n "YOUR_DATABASE_PASSWORD" | gcloud secrets create database-password \
    --replication-policy="automatic" \
    --data-file=-
```

**Example:**
```bash
echo -n "aB3#xY9$mN2&qL5" | gcloud secrets create database-password \
    --replication-policy="automatic" \
    --data-file=-
```

### 2.5 Application Secret Key

Generate a secure secret key for your application:

```bash
# Generate a random secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copy the output, then create secret:**

```bash
echo -n "YOUR_GENERATED_SECRET_KEY" | gcloud secrets create app-secret-key \
    --replication-policy="automatic" \
    --data-file=-
```

---

## Step 3: Verify Secrets Created

### 3.1 List All Secrets

```bash
gcloud secrets list
```

**Expected output:**
```
NAME                     CREATED              REPLICATION_POLICY  LOCATIONS
app-secret-key          2025-11-09T...       automatic           -
database-password       2025-11-09T...       automatic           -
firebase-credentials    2025-11-09T...       automatic           -
hubspot-client-secret   2025-11-09T...       automatic           -
openrouter-api-key      2025-11-09T...       automatic           -
```

### 3.2 Test Accessing a Secret

```bash
gcloud secrets versions access latest --secret="hubspot-client-secret"
```

**Should output:** Your HubSpot client secret value

**Test Firebase credentials:**

```bash
gcloud secrets versions access latest --secret="firebase-credentials"
```

**Should output:** Your Firebase JSON (formatted)

---

## Step 4: Grant Cloud Run Access to Secrets

### 4.1 Understand Service Accounts

Cloud Run services run as a **service account** (like a robot user). This account needs permission to read your secrets.

**Default service account:**
```
PROJECT_NUMBER-compute@developer.gserviceaccount.com
```

### 4.2 Get Your Project Number

```bash
gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)"
```

**Save this number** - you'll need it.

**Example output:**
```
123456789012
```

### 4.3 Grant Secret Access Permissions

**For each secret, grant access to the default service account:**

```bash
# Get your project number first
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")

# Grant access to all secrets
for SECRET in firebase-credentials hubspot-client-secret openrouter-api-key database-password app-secret-key; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

**Expected output for each:**
```
Updated IAM policy for secret [SECRET_NAME].
```

**What this does:**
- Grants Cloud Run permission to read (but not modify) each secret
- Uses the default Compute Engine service account
- Role `secretmanager.secretAccessor` = read-only access

### 4.4 Verify Permissions

```bash
gcloud secrets get-iam-policy firebase-credentials
```

**Should show:**
```yaml
bindings:
- members:
  - serviceAccount:123456789012-compute@developer.gserviceaccount.com
  role: roles/secretmanager.secretAccessor
```

---

## Step 5: Test Secret Access Locally (Optional)

### 5.1 Install Python Client Library

If not already installed:

```bash
cd backend
poetry add google-cloud-secret-manager
```

### 5.2 Create Test Script

Create `backend/test_secrets.py`:

```python
#!/usr/bin/env python3
"""Test accessing secrets from Secret Manager."""

from google.cloud import secretmanager
import os

def access_secret(secret_id: str, project_id: str) -> str:
    """Access a secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

if __name__ == "__main__":
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or input("Enter project ID: ")
    
    print(f"Testing Secret Manager access for project: {project_id}\n")
    
    secrets_to_test = [
        "hubspot-client-secret",
        "openrouter-api-key",
        "database-password",
        "app-secret-key",
    ]
    
    for secret_id in secrets_to_test:
        try:
            value = access_secret(secret_id, project_id)
            print(f"✅ {secret_id}: Retrieved ({len(value)} characters)")
        except Exception as e:
            print(f"❌ {secret_id}: Failed - {e}")
    
    # Test Firebase credentials (JSON)
    try:
        firebase_json = access_secret("firebase-credentials", project_id)
        import json
        parsed = json.loads(firebase_json)
        print(f"✅ firebase-credentials: Valid JSON with {len(parsed)} keys")
    except Exception as e:
        print(f"❌ firebase-credentials: Failed - {e}")
```

### 5.3 Run Test Script

```bash
cd backend
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
poetry run python test_secrets.py
```

**Expected output:**
```
Testing Secret Manager access for project: churn-risk-prod-123456

✅ hubspot-client-secret: Retrieved (36 characters)
✅ openrouter-api-key: Retrieved (48 characters)
✅ database-password: Retrieved (15 characters)
✅ app-secret-key: Retrieved (43 characters)
✅ firebase-credentials: Valid JSON with 12 keys
```

---

## Step 6: Update Application Code to Use Secrets

### 6.1 Create Secret Manager Helper

Create `backend/src/core/secrets.py`:

```python
"""Secret Manager integration for production secrets."""

import os
import json
from typing import Optional
from google.cloud import secretmanager
from functools import lru_cache


class SecretManager:
    """Handle secret retrieval from Google Cloud Secret Manager."""
    
    def __init__(self, project_id: Optional[str] = None):
        """Initialize Secret Manager client."""
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
        
        self.client = secretmanager.SecretManagerServiceClient()
    
    @lru_cache(maxsize=32)
    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        """
        Retrieve a secret from Secret Manager.
        
        Uses LRU cache to avoid repeated API calls.
        
        Args:
            secret_id: Name of the secret
            version: Version to retrieve (default: latest)
        
        Returns:
            Secret value as string
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
        
        try:
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            raise RuntimeError(f"Failed to access secret {secret_id}: {e}")
    
    def get_json_secret(self, secret_id: str) -> dict:
        """Retrieve a secret and parse as JSON."""
        secret_value = self.get_secret(secret_id)
        return json.loads(secret_value)


# Singleton instance
_secret_manager: Optional[SecretManager] = None


def get_secret_manager() -> SecretManager:
    """Get or create Secret Manager singleton."""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager
```

### 6.2 Update Config to Use Secrets (Production Only)

Modify `backend/src/core/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    
    # Firebase
    FIREBASE_PROJECT_ID: str
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None  # Only for local dev
    
    # ... rest of your settings ...
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    def get_firebase_credentials(self) -> dict:
        """
        Get Firebase credentials from file (local) or Secret Manager (production).
        """
        # Local development - use file
        if self.ENVIRONMENT == "development" and self.FIREBASE_CREDENTIALS_PATH:
            import json
            with open(self.FIREBASE_CREDENTIALS_PATH) as f:
                return json.load(f)
        
        # Production - use Secret Manager
        from src.core.secrets import get_secret_manager
        sm = get_secret_manager()
        return sm.get_json_secret("firebase-credentials")


settings = Settings()
```

**Note:** We'll fully integrate this in the Cloud Run deployment guide.

---

## Step 7: Secret Rotation Strategy (Best Practice)

### 7.1 Understanding Secret Versions

Secret Manager supports versioning:
- Each update creates a new version
- Old versions remain accessible
- You can pin to specific versions or use "latest"

### 7.2 Rotate a Secret (Example)

If you need to rotate the HubSpot secret:

```bash
echo -n "NEW_HUBSPOT_SECRET" | gcloud secrets versions add hubspot-client-secret \
    --data-file=-
```

**This creates version 2 without deleting version 1.**

### 7.3 View All Versions

```bash
gcloud secrets versions list hubspot-client-secret
```

**Output:**
```
NAME  STATE    CREATED              DESTROYED
2     enabled  2025-11-09T...       -
1     enabled  2025-11-09T...       -
```

### 7.4 Disable Old Version

```bash
gcloud secrets versions disable 1 --secret="hubspot-client-secret"
```

---

## Verification Checklist

Before proceeding:

- [ ] Secret Manager API enabled
- [ ] All 5 secrets created (firebase, hubspot, openrouter, database, app-key)
- [ ] Service account has secretAccessor role for all secrets
- [ ] Can access secrets via gcloud CLI
- [ ] Test script runs successfully (optional)
- [ ] Secret helper code created (optional)

---

## Secrets Summary

**Save this information:**

```
Secret Name               Purpose
-------------------       ----------------------------------
firebase-credentials      Firebase Admin SDK credentials (JSON)
hubspot-client-secret     HubSpot OAuth client secret
openrouter-api-key        OpenRouter API key
database-password         Cloud SQL application user password
app-secret-key            FastAPI secret key for JWT signing
```

---

## Costs Incurred

**Secret Manager pricing:**
- First 6 secrets: **Free**
- Additional secrets: $0.06/secret/month
- Secret access operations: $0.03 per 10,000 accesses

**Current cost:** $0 (you have 5 secrets, under free tier limit)

---

## Troubleshooting

### Problem: "Permission denied" when creating secrets

**Solution:**
```bash
# Verify you're authenticated
gcloud auth list

# Check you have permission
gcloud projects get-iam-policy $(gcloud config get-value project) \
    --flatten="bindings[].members" \
    --filter="bindings.members:user:YOUR_EMAIL"
```

### Problem: Can't access secrets via test script

**Solution:**
- Ensure Application Default Credentials are set: `gcloud auth application-default login`
- Check GOOGLE_CLOUD_PROJECT is set: `echo $GOOGLE_CLOUD_PROJECT`
- Verify Secret Manager API is enabled

### Problem: "Secret not found" error

**Solution:**
```bash
# List all secrets
gcloud secrets list

# Check if secret exists with correct name
# Secret names are case-sensitive
```

### Problem: Cloud Run can't access secrets

**Solution:**
- Verify service account has secretAccessor role
- Check you used the correct project number (not project ID)
- Ensure you granted access to all required secrets

---

## Security Best Practices

**Do:**
- ✅ Use Secret Manager for all sensitive data
- ✅ Grant least privilege (secretAccessor, not admin)
- ✅ Enable audit logging (automatic)
- ✅ Rotate secrets periodically
- ✅ Use specific versions in critical deployments

**Don't:**
- ❌ Store secrets in code or .env files in production
- ❌ Grant overly broad permissions
- ❌ Share secrets via email or chat
- ❌ Use same secrets across environments (dev/staging/prod)
- ❌ Commit secrets to git

---

## Next Steps

With secrets securely stored, you're ready to run database migrations on Cloud SQL.

**→ Next:** [06 - Database Migration](06-database-migration.md)

---

## Additional Resources

- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Best Practices](https://cloud.google.com/secret-manager/docs/best-practices)
- [Python Client Library](https://cloud.google.com/python/docs/reference/secretmanager/latest)
- [IAM Roles](https://cloud.google.com/secret-manager/docs/access-control)
