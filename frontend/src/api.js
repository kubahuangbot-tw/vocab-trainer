import axios from 'axios'
import { Capacitor } from '@capacitor/core'

export const serverOrigin = Capacitor.isNativePlatform()
  ? 'https://vocab.kubahuang.synology.me:7443'
  : ''

const baseURL = serverOrigin + '/api'

const api = axios.create({ baseURL })

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
