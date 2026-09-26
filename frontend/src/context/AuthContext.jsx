import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, tokenStore } from '../services/api'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState(tokenStore.get() ? 'loading' : 'anon') // loading | authed | anon

  const refresh = useCallback(async () => {
    if (!tokenStore.get()) { setUser(null); setStatus('anon'); return null }
    try {
      const u = await api.me()
      setUser(u); setStatus('authed'); return u
    } catch (e) {
      if (e.status === 401) { tokenStore.clear(); setUser(null); setStatus('anon') }
      else setStatus('error')
      return null
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  useEffect(() => {
    const onUnauth = () => { setUser(null); setStatus('anon') }
    window.addEventListener('sb:unauthorized', onUnauth)
    return () => window.removeEventListener('sb:unauthorized', onUnauth)
  }, [])

  const accept = (res) => { tokenStore.set(res.access_token); setUser(res.user); setStatus('authed'); return res.user }
  const login = async (email, password) => accept(await api.login({ email, password }))
  const register = async (b) => accept(await api.register(b))
  const demoLogin = async () => accept(await api.demoLogin())
  const logout = async () => {
    try { await api.logout() } catch { /* token already invalid */ }
    tokenStore.clear(); setUser(null); setStatus('anon')
  }

  return (
    <AuthCtx.Provider value={{ user, setUser, status, login, register, demoLogin, logout, refresh }}>
      {children}
    </AuthCtx.Provider>
  )
}

export const useAuth = () => useContext(AuthCtx)
