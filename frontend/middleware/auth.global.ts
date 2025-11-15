export default defineNuxtRouteMiddleware((to) => {
  const { user, loading, initAuth } = useAuth()

  // Initialize auth listener on first run
  if (import.meta.client && loading.value) {
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
