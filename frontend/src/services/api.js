import axios from 'axios'

const getUserId = () => {
  const stored = localStorage.getItem('health-assistant-user')
  if (stored) return stored
  const defaultUser = 'demo-user'
  localStorage.setItem('health-assistant-user', defaultUser)
  return defaultUser
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'X-User-Id': getUserId(),
  },
})

export const setActiveUser = (value) => {
  localStorage.setItem('health-assistant-user', value)
  api.defaults.headers['X-User-Id'] = value
}

export default api
