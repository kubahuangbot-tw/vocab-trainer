import { defineStore } from 'pinia'
import api from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    username: localStorage.getItem('username') || null,
    isAdmin: localStorage.getItem('isAdmin') === 'true',
  }),
  getters: {
    isLoggedIn: s => !!s.token,
  },
  actions: {
    async login(username, password) {
      const form = new URLSearchParams({ username, password })
      const { data } = await api.post('/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      this.token = data.access_token
      this.username = data.username
      this.isAdmin = data.is_admin
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('username', data.username)
      localStorage.setItem('isAdmin', data.is_admin)
    },
    logout() {
      this.token = null
      this.username = null
      this.isAdmin = false
      localStorage.clear()
    }
  }
})
