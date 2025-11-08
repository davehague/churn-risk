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
const { user } = useAuth()
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
