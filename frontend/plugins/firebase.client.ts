import { initializeApp, getApps } from 'firebase/app'
import { getAuth } from 'firebase/auth'

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()

  const firebaseConfig = {
    apiKey: config.public.firebaseApiKey,
    authDomain: config.public.firebaseAuthDomain,
    projectId: config.public.firebaseProjectId,
  }

  const app = getApps().length === 0
    ? initializeApp(firebaseConfig)
    : getApps()[0]
  const auth = getAuth(app)

  return {
    provide: {
      auth
    }
  }
})
