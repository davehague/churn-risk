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
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Sign in failed'
      throw new Error(message)
    }
  }

  const signOut = async () => {
    try {
      await firebaseSignOut($auth)
      user.value = null
      idToken.value = null
      router.push('/login')
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Sign out failed'
      throw new Error(message)
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
