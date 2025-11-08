<template>
  <div class="min-h-screen bg-gray-100 py-12 px-4">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-4xl font-bold text-gray-900 mb-8">
        Churn Risk App - API Test Page
      </h1>

      <!-- Backend Health Check -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <h2 class="text-2xl font-semibold mb-4">Backend Health</h2>
        <button
          @click="testHealth"
          class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Test Health Endpoint
        </button>
        <div v-if="healthStatus" class="mt-4 p-4 rounded" :class="healthStatus.success ? 'bg-green-50' : 'bg-red-50'">
          <pre class="text-sm">{{ JSON.stringify(healthStatus, null, 2) }}</pre>
        </div>
      </div>

      <!-- API Root -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <h2 class="text-2xl font-semibold mb-4">API Root</h2>
        <button
          @click="testApiRoot"
          class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Test API Root
        </button>
        <div v-if="apiRootStatus" class="mt-4 p-4 rounded" :class="apiRootStatus.success ? 'bg-green-50' : 'bg-red-50'">
          <pre class="text-sm">{{ JSON.stringify(apiRootStatus, null, 2) }}</pre>
        </div>
      </div>

      <!-- HubSpot OAuth -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <h2 class="text-2xl font-semibold mb-4">HubSpot OAuth</h2>
        <button
          @click="testHubSpotOAuth"
          class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
        >
          Get OAuth Authorization URL
        </button>
        <div v-if="oauthStatus" class="mt-4">
          <div class="p-4 rounded" :class="oauthStatus.success ? 'bg-green-50' : 'bg-red-50'">
            <pre class="text-sm">{{ JSON.stringify(oauthStatus, null, 2) }}</pre>
          </div>
          <a
            v-if="oauthStatus.authorization_url"
            :href="oauthStatus.authorization_url"
            target="_blank"
            class="mt-4 inline-block bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
          >
            Open HubSpot Authorization →
          </a>
        </div>
      </div>

      <!-- Test Summary -->
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-2xl font-semibold mb-4">Test Summary</h2>
        <div class="space-y-2">
          <div class="flex items-center">
            <span class="font-medium w-48">Backend Server:</span>
            <span :class="healthStatus?.success ? 'text-green-600' : 'text-gray-400'">
              {{ healthStatus?.success ? '✅ Running' : '⏳ Not tested' }}
            </span>
          </div>
          <div class="flex items-center">
            <span class="font-medium w-48">API Root:</span>
            <span :class="apiRootStatus?.success ? 'text-green-600' : 'text-gray-400'">
              {{ apiRootStatus?.success ? '✅ Working' : '⏳ Not tested' }}
            </span>
          </div>
          <div class="flex items-center">
            <span class="font-medium w-48">HubSpot OAuth:</span>
            <span :class="oauthStatus?.authorization_url ? 'text-green-600' : 'text-gray-400'">
              {{ oauthStatus?.authorization_url ? '✅ Configured' : '⏳ Not tested' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const healthStatus = ref<any>(null)
const apiRootStatus = ref<any>(null)
const oauthStatus = ref<any>(null)

const API_URL = 'http://localhost:8000'

async function testHealth() {
  try {
    const response = await fetch(`${API_URL}/health`)
    const data = await response.json()
    healthStatus.value = {
      success: true,
      status: response.status,
      data
    }
  } catch (error: any) {
    healthStatus.value = {
      success: false,
      error: error.message
    }
  }
}

async function testApiRoot() {
  try {
    const response = await fetch(`${API_URL}/api/v1/`)
    const data = await response.json()
    apiRootStatus.value = {
      success: true,
      status: response.status,
      data
    }
  } catch (error: any) {
    apiRootStatus.value = {
      success: false,
      error: error.message
    }
  }
}

async function testHubSpotOAuth() {
  try {
    const response = await fetch(`${API_URL}/api/v1/integrations/hubspot/authorize`)
    const data = await response.json()
    oauthStatus.value = {
      success: true,
      status: response.status,
      ...data
    }
  } catch (error: any) {
    oauthStatus.value = {
      success: false,
      error: error.message
    }
  }
}
</script>
