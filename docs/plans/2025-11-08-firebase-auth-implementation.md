# Firebase Auth Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement self-service user registration and login with Firebase Auth, automatically creating tenants and admin users.

**Architecture:** Backend provides registration API that creates Firebase users via Admin SDK and database records. Frontend uses Firebase Client SDK for login, obtaining JWT tokens for API authentication. Pinia store manages user state.

**Tech Stack:** FastAPI, Firebase Admin SDK, Firebase Client SDK (v10), Vue 3, Nuxt 3, Pinia, Tailwind CSS

---

## Task 1: Backend Registration Schema

**Files:**
- Create: `backend/src/schemas/auth.py`
- Test: `backend/tests/unit/test_auth_schemas.py`

**Step 1: Write schema tests**

Create `backend/tests/unit/test_auth_schemas.py`:

```python
import pytest
from pydantic import ValidationError
from src.schemas.auth import RegisterRequest, CheckSubdomainRequest


def test_register_request_valid():
    """Test valid registration request."""
    data = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "name": "John Doe",
        "company_name": "Acme Corp",
        "subdomain": "acme"
    }
    request = RegisterRequest(**data)
    assert request.email == "test@example.com"
    assert request.subdomain == "acme"


def test_register_request_invalid_subdomain_uppercase():
    """Test subdomain must be lowercase."""
    data = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "name": "John Doe",
        "company_name": "Acme Corp",
        "subdomain": "Acme"
    }
    with pytest.raises(ValidationError):
        RegisterRequest(**data)


def test_register_request_invalid_subdomain_too_short():
    """Test subdomain minimum length."""
    data = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "name": "John Doe",
        "company_name": "Acme Corp",
        "subdomain": "ab"
    }
    with pytest.raises(ValidationError):
        RegisterRequest(**data)


def test_register_request_invalid_subdomain_special_chars():
    """Test subdomain alphanumeric only."""
    data = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "name": "John Doe",
        "company_name": "Acme Corp",
        "subdomain": "acme_corp"
    }
    with pytest.raises(ValidationError):
        RegisterRequest(**data)


def test_check_subdomain_request():
    """Test subdomain check request."""
    request = CheckSubdomainRequest(subdomain="acme")
    assert request.subdomain == "acme"
```

**Step 2: Run tests to verify they fail**

Run:
```bash
cd backend
poetry run pytest tests/unit/test_auth_schemas.py -v
```

Expected: FAIL - module not found

**Step 3: Create auth schemas**

Create `backend/src/schemas/auth.py`:

```python
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class RegisterRequest(BaseModel):
    """Request schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2, max_length=255)
    company_name: str = Field(..., min_length=2, max_length=255)
    subdomain: str = Field(..., min_length=3, max_length=63)

    @field_validator('subdomain')
    @classmethod
    def validate_subdomain(cls, v: str) -> str:
        """Validate subdomain format."""
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', v):
            raise ValueError(
                'Subdomain must be lowercase alphanumeric with hyphens, '
                'and cannot start or end with a hyphen'
            )
        return v


class RegisterResponse(BaseModel):
    """Response schema for successful registration."""
    message: str
    email: str


class CheckSubdomainRequest(BaseModel):
    """Request schema for subdomain availability check."""
    subdomain: str = Field(..., min_length=3, max_length=63)


class CheckSubdomainResponse(BaseModel):
    """Response schema for subdomain availability check."""
    available: bool
    subdomain: str
```

**Step 4: Run tests to verify they pass**

Run:
```bash
poetry run pytest tests/unit/test_auth_schemas.py -v
```

Expected: 5 tests PASS

**Step 5: Commit**

```bash
git add src/schemas/auth.py tests/unit/test_auth_schemas.py
git commit -m "feat: add registration and subdomain check schemas"
```

---

## Task 2: Backend Registration Endpoint

**Files:**
- Create: `backend/src/api/routers/auth.py`
- Modify: `backend/src/main.py`
- Test: `backend/tests/integration/test_auth_registration.py`

**Step 1: Write integration tests**

Create `backend/tests/integration/test_auth_registration.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.base import Base
from src.models.tenant import Tenant
from src.models.user import User, UserRole
from src.core.database import get_db
from src.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def client(test_db):
    """Create test client with overridden database."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_check_subdomain_available(client, test_db):
    """Test checking available subdomain."""
    response = client.post(
        "/api/v1/auth/check-subdomain",
        json={"subdomain": "acme"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is True
    assert data["subdomain"] == "acme"


def test_check_subdomain_taken(client, test_db):
    """Test checking taken subdomain."""
    # Create existing tenant
    tenant = Tenant(name="Acme Corp", subdomain="acme")
    test_db.add(tenant)
    test_db.commit()

    response = client.post(
        "/api/v1/auth/check-subdomain",
        json={"subdomain": "acme"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is False


@patch('src.api.routers.auth.auth.create_user')
def test_register_success(mock_create_user, client, test_db):
    """Test successful user registration."""
    # Mock Firebase user creation
    mock_create_user.return_value = MagicMock(uid="firebase-uid-123")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "john@example.com",
            "password": "SecurePass123",
            "name": "John Doe",
            "company_name": "Acme Corp",
            "subdomain": "acme"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Registration successful. Please log in."
    assert data["email"] == "john@example.com"

    # Verify tenant created
    tenant = test_db.query(Tenant).filter_by(subdomain="acme").first()
    assert tenant is not None
    assert tenant.name == "Acme Corp"

    # Verify user created
    user = test_db.query(User).filter_by(firebase_uid="firebase-uid-123").first()
    assert user is not None
    assert user.email == "john@example.com"
    assert user.name == "John Doe"
    assert user.role == UserRole.ADMIN
    assert user.tenant_id == tenant.id


@patch('src.api.routers.auth.auth.create_user')
def test_register_duplicate_subdomain(mock_create_user, client, test_db):
    """Test registration with duplicate subdomain."""
    # Create existing tenant
    tenant = Tenant(name="Existing Corp", subdomain="acme")
    test_db.add(tenant)
    test_db.commit()

    mock_create_user.return_value = MagicMock(uid="firebase-uid-123")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "john@example.com",
            "password": "SecurePass123",
            "name": "John Doe",
            "company_name": "Acme Corp",
            "subdomain": "acme"
        }
    )

    assert response.status_code == 400
    assert "Subdomain already taken" in response.json()["detail"]


def test_register_invalid_subdomain_format(client, test_db):
    """Test registration with invalid subdomain format."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "john@example.com",
            "password": "SecurePass123",
            "name": "John Doe",
            "company_name": "Acme Corp",
            "subdomain": "Acme_Corp"  # Invalid: uppercase and underscore
        }
    )

    assert response.status_code == 422  # Validation error
```

**Step 2: Run tests to verify they fail**

Run:
```bash
cd backend
poetry run pytest tests/integration/test_auth_registration.py -v
```

Expected: FAIL - router not found

**Step 3: Create auth router**

Create `backend/src/api/routers/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from firebase_admin import auth
from src.core.database import get_db
from src.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    CheckSubdomainRequest,
    CheckSubdomainResponse
)
from src.models.tenant import Tenant, PlanTier
from src.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/check-subdomain", response_model=CheckSubdomainResponse)
async def check_subdomain(
    request: CheckSubdomainRequest,
    db: Session = Depends(get_db)
):
    """Check if subdomain is available."""
    existing = db.query(Tenant).filter(
        Tenant.subdomain == request.subdomain
    ).first()

    return CheckSubdomainResponse(
        available=existing is None,
        subdomain=request.subdomain
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user and create tenant."""
    # Check subdomain availability
    existing_tenant = db.query(Tenant).filter(
        Tenant.subdomain == request.subdomain
    ).first()

    if existing_tenant:
        raise HTTPException(
            status_code=400,
            detail="Subdomain already taken. Please choose another."
        )

    try:
        # Create Firebase user
        firebase_user = auth.create_user(
            email=request.email,
            password=request.password,
            display_name=request.name
        )

        # Create tenant
        tenant = Tenant(
            name=request.company_name,
            subdomain=request.subdomain,
            plan_tier=PlanTier.STARTER
        )
        db.add(tenant)
        db.flush()  # Get tenant ID before creating user

        # Create user
        user = User(
            tenant_id=tenant.id,
            firebase_uid=firebase_user.uid,
            email=request.email,
            name=request.name,
            role=UserRole.ADMIN
        )
        db.add(user)
        db.commit()

        return RegisterResponse(
            message="Registration successful. Please log in.",
            email=request.email
        )

    except auth.EmailAlreadyExistsError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already registered. Please log in."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )
```

**Step 4: Include router in main app**

Modify `backend/src/main.py`:

```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.api.dependencies import get_current_user
from src.api.routers import integrations, auth  # Add auth import
from src.models.user import User

app = FastAPI(
    title="Churn Risk API",
    version="0.1.0",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(integrations.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)  # Add this line


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


@app.get(f"{settings.API_V1_PREFIX}/")
async def root():
    """API root endpoint."""
    return {"message": "Churn Risk API", "version": "0.1.0"}


@app.get(f"{settings.API_V1_PREFIX}/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.value,
        "tenant_id": str(current_user.tenant_id)
    }
```

**Step 5: Run tests to verify they pass**

Run:
```bash
poetry run pytest tests/integration/test_auth_registration.py -v
```

Expected: 5 tests PASS

**Step 6: Commit**

```bash
git add src/api/routers/auth.py tests/integration/test_auth_registration.py src/main.py
git commit -m "feat: add registration and subdomain check endpoints"
```

---

## Task 3: Frontend Firebase SDK Setup

**Files:**
- Create: `frontend/plugins/firebase.client.ts`
- Create: `frontend/composables/useAuth.ts`
- Create: `frontend/composables/useApi.ts`
- Modify: `frontend/package.json`

**Step 1: Install Firebase SDK**

Run:
```bash
cd frontend
npm install firebase
```

Expected: Firebase added to dependencies

**Step 2: Create Firebase plugin**

Create `frontend/plugins/firebase.client.ts`:

```typescript
import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()

  const firebaseConfig = {
    apiKey: config.public.firebaseApiKey,
    authDomain: config.public.firebaseAuthDomain,
    projectId: config.public.firebaseProjectId,
  }

  const app = initializeApp(firebaseConfig)
  const auth = getAuth(app)

  return {
    provide: {
      auth
    }
  }
})
```

**Step 3: Create auth composable**

Create `frontend/composables/useAuth.ts`:

```typescript
import {
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  type User
} from 'firebase/auth'

export const useAuth = () => {
  const { $auth } = useNuxtApp()
  const router = useRouter()

  const user = useState<User | null>('firebase-user', () => null)
  const idToken = useState<string | null>('id-token', () => null)
  const loading = useState<boolean>('auth-loading', () => true)

  // Initialize auth state listener
  const initAuth = () => {
    onAuthStateChanged($auth, async (firebaseUser) => {
      user.value = firebaseUser

      if (firebaseUser) {
        // Get fresh token
        idToken.value = await firebaseUser.getIdToken()
      } else {
        idToken.value = null
      }

      loading.value = false
    })
  }

  const signIn = async (email: string, password: string) => {
    try {
      const credential = await signInWithEmailAndPassword($auth, email, password)
      idToken.value = await credential.user.getIdToken()
      return credential.user
    } catch (error: any) {
      throw new Error(error.message)
    }
  }

  const signOut = async () => {
    try {
      await firebaseSignOut($auth)
      user.value = null
      idToken.value = null
      router.push('/login')
    } catch (error: any) {
      throw new Error(error.message)
    }
  }

  return {
    user: readonly(user),
    idToken: readonly(idToken),
    loading: readonly(loading),
    signIn,
    signOut,
    initAuth
  }
}
```

**Step 4: Create API composable**

Create `frontend/composables/useApi.ts`:

```typescript
import type { UseFetchOptions } from 'nuxt/app'

export const useApi = <T>(url: string, options: UseFetchOptions<T> = {}) => {
  const config = useRuntimeConfig()
  const { idToken } = useAuth()

  const defaults: UseFetchOptions<T> = {
    baseURL: config.public.apiBase,
    headers: idToken.value
      ? { Authorization: `Bearer ${idToken.value}` }
      : {},
    onResponseError({ response }) {
      if (response.status === 401) {
        // Token expired or invalid, redirect to login
        navigateTo('/login')
      }
    }
  }

  return useFetch(url, { ...defaults, ...options })
}
```

**Step 5: Commit**

```bash
git add plugins/firebase.client.ts composables/useAuth.ts composables/useApi.ts package.json package-lock.json
git commit -m "feat: add Firebase SDK and auth composables"
```

---

## Task 4: Registration Page

**Files:**
- Create: `frontend/pages/register.vue`
- Create: `frontend/types/auth.ts`

**Step 1: Create auth types**

Create `frontend/types/auth.ts`:

```typescript
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
```

**Step 2: Create registration page**

Create `frontend/pages/register.vue`:

```vue
<template>
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
        Create your account
      </h2>
      <p class="mt-2 text-center text-sm text-gray-600">
        Already have an account?
        <NuxtLink to="/login" class="font-medium text-blue-600 hover:text-blue-500">
          Sign in
        </NuxtLink>
      </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- Email -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">
              Email address
            </label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <!-- Name -->
          <div>
            <label for="name" class="block text-sm font-medium text-gray-700">
              Full name
            </label>
            <input
              id="name"
              v-model="form.name"
              type="text"
              required
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <!-- Company Name -->
          <div>
            <label for="companyName" class="block text-sm font-medium text-gray-700">
              Company name
            </label>
            <input
              id="companyName"
              v-model="form.companyName"
              type="text"
              required
              @input="onCompanyNameChange"
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <!-- Subdomain -->
          <div>
            <label for="subdomain" class="block text-sm font-medium text-gray-700">
              Subdomain
            </label>
            <div class="mt-1 flex rounded-md shadow-sm">
              <input
                id="subdomain"
                v-model="form.subdomain"
                type="text"
                required
                pattern="[a-z0-9][a-z0-9-]*[a-z0-9]"
                @input="onSubdomainChange"
                class="flex-1 block w-full border border-gray-300 rounded-l-md py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              <span class="inline-flex items-center px-3 rounded-r-md border border-l-0 border-gray-300 bg-gray-50 text-gray-500 text-sm">
                .yourapp.com
              </span>
            </div>
            <p v-if="subdomainChecking" class="mt-1 text-sm text-gray-500">
              Checking availability...
            </p>
            <p v-else-if="subdomainAvailable === true" class="mt-1 text-sm text-green-600">
              ✓ Available
            </p>
            <p v-else-if="subdomainAvailable === false" class="mt-1 text-sm text-red-600">
              ✗ This subdomain is already taken
            </p>
            <p class="mt-1 text-xs text-gray-500">
              Lowercase letters, numbers, and hyphens only
            </p>
          </div>

          <!-- Password -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              minlength="8"
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            <p class="mt-1 text-xs text-gray-500">
              At least 8 characters with uppercase, lowercase, and number
            </p>
          </div>

          <!-- Confirm Password -->
          <div>
            <label for="confirmPassword" class="block text-sm font-medium text-gray-700">
              Confirm password
            </label>
            <input
              id="confirmPassword"
              v-model="form.confirmPassword"
              type="password"
              required
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            <p v-if="form.confirmPassword && form.password !== form.confirmPassword" class="mt-1 text-sm text-red-600">
              Passwords do not match
            </p>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="rounded-md bg-red-50 p-4">
            <p class="text-sm text-red-800">{{ error }}</p>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="!isFormValid || submitting"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {{ submitting ? 'Creating account...' : 'Create account' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { RegisterFormData, RegisterRequest, SubdomainCheckResponse } from '~/types/auth'

const router = useRouter()
const config = useRuntimeConfig()

const form = reactive<RegisterFormData>({
  email: '',
  password: '',
  confirmPassword: '',
  name: '',
  companyName: '',
  subdomain: ''
})

const error = ref<string | null>(null)
const submitting = ref(false)
const subdomainChecking = ref(false)
const subdomainAvailable = ref<boolean | null>(null)
let subdomainCheckTimeout: NodeJS.Timeout | null = null

const isFormValid = computed(() => {
  return (
    form.email &&
    form.password &&
    form.confirmPassword &&
    form.name &&
    form.companyName &&
    form.subdomain &&
    form.password === form.confirmPassword &&
    form.password.length >= 8 &&
    subdomainAvailable.value === true
  )
})

const slugify = (text: string): string => {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

const onCompanyNameChange = () => {
  if (!form.subdomain) {
    form.subdomain = slugify(form.companyName)
    checkSubdomain()
  }
}

const onSubdomainChange = () => {
  form.subdomain = form.subdomain.toLowerCase()
  checkSubdomain()
}

const checkSubdomain = async () => {
  if (!form.subdomain || form.subdomain.length < 3) {
    subdomainAvailable.value = null
    return
  }

  // Debounce
  if (subdomainCheckTimeout) {
    clearTimeout(subdomainCheckTimeout)
  }

  subdomainCheckTimeout = setTimeout(async () => {
    subdomainChecking.value = true

    try {
      const response = await $fetch<SubdomainCheckResponse>(
        `${config.public.apiBase}/api/v1/auth/check-subdomain`,
        {
          method: 'POST',
          body: { subdomain: form.subdomain }
        }
      )
      subdomainAvailable.value = response.available
    } catch (err) {
      console.error('Subdomain check failed:', err)
      subdomainAvailable.value = null
    } finally {
      subdomainChecking.value = false
    }
  }, 500)
}

const handleSubmit = async () => {
  if (!isFormValid.value) return

  error.value = null
  submitting.value = true

  try {
    const payload: RegisterRequest = {
      email: form.email,
      password: form.password,
      name: form.name,
      company_name: form.companyName,
      subdomain: form.subdomain
    }

    await $fetch(`${config.public.apiBase}/api/v1/auth/register`, {
      method: 'POST',
      body: payload
    })

    // Success - redirect to login
    router.push({
      path: '/login',
      query: { registered: 'true', email: form.email }
    })
  } catch (err: any) {
    console.error('Registration failed:', err)
    error.value = err.data?.detail || 'Registration failed. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>
```

**Step 3: Test registration page manually**

Run:
```bash
npm run dev
```

Navigate to http://localhost:3000/register

Expected:
- Form displays correctly
- Company name auto-populates subdomain
- Subdomain check shows availability
- Validation works on all fields

**Step 4: Commit**

```bash
git add pages/register.vue types/auth.ts
git commit -m "feat: add registration page with subdomain validation"
```

---

## Task 5: Login Page

**Files:**
- Create: `frontend/pages/login.vue`

**Step 1: Create login page**

Create `frontend/pages/login.vue`:

```vue
<template>
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
        Sign in to your account
      </h2>
      <p class="mt-2 text-center text-sm text-gray-600">
        Don't have an account?
        <NuxtLink to="/register" class="font-medium text-blue-600 hover:text-blue-500">
          Sign up
        </NuxtLink>
      </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
        <!-- Success message from registration -->
        <div v-if="registered" class="mb-4 rounded-md bg-green-50 p-4">
          <p class="text-sm text-green-800">
            Registration successful! Please sign in with your credentials.
          </p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- Email -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">
              Email address
            </label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              autocomplete="email"
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <!-- Password -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              autocomplete="current-password"
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <!-- Error Message -->
          <div v-if="error" class="rounded-md bg-red-50 p-4">
            <p class="text-sm text-red-800">{{ error }}</p>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="!form.email || !form.password || loading"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {{ loading ? 'Signing in...' : 'Sign in' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const { signIn } = useAuth()

const form = reactive({
  email: (route.query.email as string) || '',
  password: ''
})

const error = ref<string | null>(null)
const loading = ref(false)
const registered = computed(() => route.query.registered === 'true')

const handleSubmit = async () => {
  error.value = null
  loading.value = true

  try {
    await signIn(form.email, form.password)

    // Success - redirect to dashboard
    router.push('/dashboard')
  } catch (err: any) {
    console.error('Login failed:', err)

    // Parse Firebase error
    if (err.message.includes('invalid-credential') || err.message.includes('user-not-found')) {
      error.value = 'Invalid email or password'
    } else if (err.message.includes('too-many-requests')) {
      error.value = 'Too many failed login attempts. Please try again later.'
    } else {
      error.value = 'Login failed. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>
```

**Step 2: Test login page manually**

Navigate to http://localhost:3000/login

Expected:
- Form displays correctly
- Email pre-filled if coming from registration
- Success message shown if registered=true
- Error handling works for invalid credentials

**Step 3: Commit**

```bash
git add pages/login.vue
git commit -m "feat: add login page with Firebase authentication"
```

---

## Task 6: User State Management

**Files:**
- Create: `frontend/stores/user.ts`
- Create: `frontend/types/user.ts`

**Step 1: Create user types**

Create `frontend/types/user.ts`:

```typescript
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
```

**Step 2: Create user store**

Create `frontend/stores/user.ts`:

```typescript
import { defineStore } from 'pinia'
import type { User, Tenant } from '~/types/user'

export const useUserStore = defineStore('user', {
  state: () => ({
    currentUser: null as User | null,
    tenant: null as Tenant | null,
    loading: false
  }),

  actions: {
    async fetchCurrentUser() {
      const { idToken } = useAuth()
      const config = useRuntimeConfig()

      if (!idToken.value) {
        this.currentUser = null
        this.tenant = null
        return
      }

      this.loading = true

      try {
        const data = await $fetch<User>(`${config.public.apiBase}/api/v1/me`, {
          headers: {
            Authorization: `Bearer ${idToken.value}`
          }
        })

        this.currentUser = data

        // TODO: Fetch tenant data separately if needed
        // For now, tenant_id is in user data
      } catch (error) {
        console.error('Failed to fetch user:', error)
        this.currentUser = null
        this.tenant = null
      } finally {
        this.loading = false
      }
    },

    async logout() {
      const { signOut } = useAuth()

      this.currentUser = null
      this.tenant = null

      await signOut()
    }
  }
})
```

**Step 3: Commit**

```bash
git add stores/user.ts types/user.ts
git commit -m "feat: add user state management with Pinia"
```

---

## Task 7: Auth Middleware & App Layout

**Files:**
- Create: `frontend/middleware/auth.global.ts`
- Create: `frontend/layouts/default.vue`
- Create: `frontend/app.vue`
- Create: `frontend/pages/index.vue`
- Create: `frontend/pages/dashboard.vue`

**Step 1: Create auth middleware**

Create `frontend/middleware/auth.global.ts`:

```typescript
export default defineNuxtRouteMiddleware((to) => {
  const { user, loading, initAuth } = useAuth()

  // Initialize auth listener on first run
  if (process.client && loading.value) {
    initAuth()
  }

  // Public routes that don't require auth
  const publicRoutes = ['/', '/login', '/register']
  const isPublicRoute = publicRoutes.includes(to.path)

  // Wait for auth to initialize
  if (loading.value) {
    return
  }

  // Redirect to login if accessing protected route without auth
  if (!isPublicRoute && !user.value) {
    return navigateTo('/login')
  }

  // Redirect to dashboard if accessing auth pages while logged in
  if ((to.path === '/login' || to.path === '/register') && user.value) {
    return navigateTo('/dashboard')
  }
})
```

**Step 2: Create default layout**

Create `frontend/layouts/default.vue`:

```vue
<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Navigation -->
    <nav v-if="user" class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <div class="flex-shrink-0 flex items-center">
              <h1 class="text-xl font-bold text-gray-900">Churn Risk</h1>
            </div>
            <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
              <NuxtLink
                to="/dashboard"
                class="border-blue-500 text-gray-900 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                Dashboard
              </NuxtLink>
            </div>
          </div>
          <div class="flex items-center">
            <span class="text-sm text-gray-700 mr-4">{{ currentUser?.name }}</span>
            <button
              @click="handleLogout"
              class="text-sm text-gray-700 hover:text-gray-900"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Page Content -->
    <main>
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
const { user, signOut } = useAuth()
const userStore = useUserStore()

const currentUser = computed(() => userStore.currentUser)

const handleLogout = async () => {
  await userStore.logout()
}

// Fetch user data when logged in
watch(user, async (newUser) => {
  if (newUser) {
    await userStore.fetchCurrentUser()
  }
}, { immediate: true })
</script>
```

**Step 3: Update app.vue**

Modify `frontend/app.vue`:

```vue
<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup lang="ts">
const { initAuth } = useAuth()

onMounted(() => {
  initAuth()
})
</script>
```

**Step 4: Create landing page**

Create `frontend/pages/index.vue`:

```vue
<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center px-4">
    <div class="text-center">
      <h1 class="text-5xl font-bold text-gray-900 mb-4">
        Churn Risk Detection
      </h1>
      <p class="text-xl text-gray-600 mb-8">
        Analyze support tickets and identify at-risk customers
      </p>
      <NuxtLink
        to="/register"
        class="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-blue-700 transition"
      >
        Get Started
      </NuxtLink>
      <p class="mt-4 text-sm text-gray-600">
        Already have an account?
        <NuxtLink to="/login" class="text-blue-600 hover:text-blue-700">
          Sign in
        </NuxtLink>
      </p>
    </div>
  </div>
</template>
```

**Step 5: Create dashboard page**

Create `frontend/pages/dashboard.vue`:

```vue
<template>
  <div class="py-10">
    <header>
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 class="text-3xl font-bold leading-tight text-gray-900">
          Dashboard
        </h1>
      </div>
    </header>
    <main>
      <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
        <div class="px-4 py-8 sm:px-0">
          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">Welcome, {{ user?.name }}!</h2>
            <p class="text-gray-600">
              You're signed in as <span class="font-medium">{{ user?.email }}</span>
            </p>
            <p class="text-gray-600 mt-2">
              Role: <span class="font-medium capitalize">{{ user?.role }}</span>
            </p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'default'
})

const userStore = useUserStore()
const user = computed(() => userStore.currentUser)
</script>
```

**Step 6: Test full flow manually**

Run backend:
```bash
cd backend
poetry run uvicorn src.main:app --reload --port 8000
```

Run frontend:
```bash
cd frontend
npm run dev
```

Test flow:
1. Navigate to http://localhost:3000
2. Click "Get Started" → should go to /register
3. Fill out registration form → submit
4. Should redirect to /login with success message
5. Login with credentials → should go to /dashboard
6. Refresh page → should stay logged in
7. Click logout → should go to /login
8. Try to access /dashboard without login → should redirect to /login

Expected: All flows work correctly

**Step 7: Commit**

```bash
git add middleware/auth.global.ts layouts/default.vue app.vue pages/index.vue pages/dashboard.vue
git commit -m "feat: add auth middleware, layout, and landing/dashboard pages"
```

---

## Task 8: Final Integration Testing

**Step 1: Run all backend tests**

Run:
```bash
cd backend
poetry run pytest -v
```

Expected: All tests pass (including new auth tests)

**Step 2: Test end-to-end registration flow**

1. Clear Firebase Auth users (if testing with existing data)
2. Clear database: `poetry run alembic downgrade base && poetry run alembic upgrade head`
3. Register new user via frontend
4. Verify in Firebase Console that user exists
5. Verify in database that Tenant and User records exist
6. Login with new credentials
7. Verify dashboard shows correct user data

**Step 3: Test error cases**

1. Try to register with existing email → should show error
2. Try to register with taken subdomain → should show error
3. Try to login with wrong password → should show error
4. Try to access /dashboard when logged out → should redirect to /login

**Step 4: Update documentation**

Create `backend/docs/dev/auth-setup.md`:

```markdown
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
```

**Step 5: Final commit**

```bash
git add docs/dev/auth-setup.md
git commit -m "docs: add authentication setup guide"
```

---

## Verification Checklist

Before marking this task complete:

- [ ] All backend tests pass
- [ ] User can register with email/password
- [ ] Subdomain validation works (real-time check)
- [ ] Subdomain auto-populates from company name
- [ ] Registration creates Tenant and User in database
- [ ] Registration creates Firebase user
- [ ] User can login with credentials
- [ ] Login redirects to dashboard
- [ ] Dashboard shows correct user data
- [ ] Logout works and redirects to login
- [ ] Auth middleware prevents unauthorized access
- [ ] Refresh preserves login state
- [ ] Error messages display correctly
- [ ] Password validation works
- [ ] Duplicate email/subdomain handled correctly

---

## Plan Complete

All tasks ready for execution with superpowers:executing-plans or superpowers:subagent-driven-development.
