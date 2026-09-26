// Thin API client. All requests carry the JWT and the user's timezone (so "today" and daily trends
// use local days). Errors are normalised into user-friendly messages.
const BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')
const TOKEN_KEY = 'sb_token'

export const tokenStore = {
  get: () => { try { return localStorage.getItem(TOKEN_KEY) } catch { return null } },
  set: (t) => { try { localStorage.setItem(TOKEN_KEY, t) } catch { /* private mode */ } },
  clear: () => { try { localStorage.removeItem(TOKEN_KEY) } catch { /* ignore */ } },
}

export class ApiError extends Error {
  constructor(message, status, data) { super(message); this.status = status; this.data = data }
}

const tz = (() => { try { return Intl.DateTimeFormat().resolvedOptions().timeZone } catch { return 'UTC' } })()

export async function request(path, { method = 'GET', body, form, raw, signal } = {}) {
  const headers = { 'X-Timezone': tz }
  const token = tokenStore.get()
  if (token) headers.Authorization = `Bearer ${token}`
  let payload
  if (form) payload = form
  else if (body !== undefined) { headers['Content-Type'] = 'application/json'; payload = JSON.stringify(body) }
  let res
  try {
    res = await fetch(`${BASE}${path}`, { method, headers, body: payload, signal })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new ApiError('Unable to connect. Please try again.', 0)
  }
  if (res.status === 401 && token) {
    tokenStore.clear()
    window.dispatchEvent(new Event('sb:unauthorized'))
  }
  if (raw && res.ok) return res
  if (res.status === 204) return null
  let data = null
  try { data = await res.json() } catch { /* non-JSON */ }
  if (!res.ok) {
    const msg = typeof data?.detail === 'string' ? data.detail
      : res.status >= 500 ? 'Something went wrong on our side. Please try again.'
      : 'That request could not be completed.'
    throw new ApiError(msg, res.status, data)
  }
  return data
}

export const api = {
  register: (b) => request('/auth/register', { method: 'POST', body: b }),
  login: (b) => request('/auth/login', { method: 'POST', body: b }),
  demoLogin: () => request('/auth/demo', { method: 'POST' }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
  profileOptions: () => request('/profile/options'),
  profile: () => request('/profile'),
  saveProfile: (b) => request('/profile', { method: 'PUT', body: b }),
  goals: () => request('/goals'),
  saveGoal: (b) => request('/goals', { method: 'POST', body: b }),
  updateGoal: (id, b) => request(`/goals/${id}`, { method: 'PUT', body: b }),
  settings: () => request('/settings'),
  saveSettings: (b) => request('/settings', { method: 'PUT', body: b }),
  sendTestReport: (period) => request(`/settings/notifications/send-test?period=${period}`, { method: 'POST' }),
  outbox: () => request('/settings/notifications/outbox'),
  ocr: (file, lang = 'eng') => { const f = new FormData(); f.append('image', file); return request(`/ocr/extract?lang=${lang}`, { method: 'POST', form: f }) },
  preview: (ingredients) => request('/analysis/preview', { method: 'POST', body: { ingredients } }),
  analyze: (b) => request('/analysis/analyze', { method: 'POST', body: b }),
  result: (id) => request(`/analysis/${id}`),
  recentChecks: (n = 5) => request(`/analysis/recent?limit=${n}`),
  searchFoods: (q, signal) => request(`/foods/search?q=${encodeURIComponent(q)}&limit=20`, { signal }),
  food: (id) => request(`/foods/${id}`),
  dishes: () => request('/eating-out/dishes'),
  logFood: (b) => request('/logs', { method: 'POST', body: b }),
  history: (params) => request(`/history?${new URLSearchParams(params)}`),
  historyItem: (id) => request(`/history/${id}`),
  updateLog: (id, b) => request(`/logs/${id}`, { method: 'PUT', body: b }),
  deleteLog: (id) => request(`/logs/${id}`, { method: 'DELETE' }),
  exportLogs: (format) => request(`/logs/export?format=${format}`, { raw: true }),
  clearLogs: () => request('/logs/clear', { method: 'POST', body: { confirm_text: 'CLEAR' } }),
  dashboard: () => request('/dashboard'),
  trends: (window) => request(`/trends?window=${window}`),
  pendingSymptoms: () => request('/symptoms/pending'),
  submitSymptom: (b) => request('/symptoms', { method: 'POST', body: b }),
  consultProviders: () => request('/consult/providers'),
  attention: () => request('/consult/attention'),
  household: (text) => request('/household/analyze', { method: 'POST', body: { text } }),
  updateAccount: (b) => request('/account', { method: 'PUT', body: b }),
  exportAccount: () => request('/account/export'),
  deleteAccount: (b) => request('/account/delete', { method: 'POST', body: b }),
  resetDemo: () => request('/demo/reset', { method: 'POST' }),
}
