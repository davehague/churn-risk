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
