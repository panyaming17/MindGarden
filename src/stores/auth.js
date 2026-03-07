import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null,
    tokenExpiry: localStorage.getItem('token_expiry') || null
  }),
  getters: {
    isAuthenticated: (state) => {
      if (!state.token || !state.tokenExpiry) {
        return false
      }
      return Date.now() < parseInt(state.tokenExpiry)
    },
    getToken: (state) => state.token,
    getUser: (state) => state.user
  },
  actions: {
    setToken(token, expiry) {
      this.token = token
      this.tokenExpiry = expiry
      localStorage.setItem('access_token', token)
      localStorage.setItem('token_expiry', expiry)
    },
    setUser(user) {
      this.user = user
      localStorage.setItem('user', JSON.stringify(user))
    },
    logout() {
      this.token = null
      this.user = null
      this.tokenExpiry = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      localStorage.removeItem('token_expiry')
    }
  }
})