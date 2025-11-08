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
