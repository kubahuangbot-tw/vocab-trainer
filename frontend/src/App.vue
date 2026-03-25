<template>
  <div class="min-h-screen bg-gray-50">
    <nav v-if="auth.isLoggedIn" class="bg-indigo-600 text-white px-4 py-3 flex items-center justify-between shadow">
      <div class="flex items-center gap-2 font-bold text-lg">
        📚 VocabTrainer
      </div>
      <div class="flex items-center gap-4 text-sm">
        <router-link to="/" class="hover:text-indigo-200">測驗</router-link>
        <router-link to="/stats" class="hover:text-indigo-200">成績</router-link>
        <router-link v-if="auth.isAdmin" to="/admin" class="hover:text-indigo-200">管理</router-link>
        <span class="text-indigo-200">👤 {{ auth.username }}</span>
        <button @click="logout" class="text-indigo-200 hover:text-white">登出</button>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>
