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
