<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-500 to-purple-600 p-4">
    <div class="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm">
      <div class="text-center mb-8">
        <div class="text-5xl mb-2">📚</div>
        <h1 class="text-2xl font-bold text-gray-800">VocabTrainer</h1>
        <p class="text-gray-500 text-sm mt-1">多人單字測驗系統</p>
      </div>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">用戶名</label>
          <input
            v-model="username"
            type="text"
            required
            placeholder="輸入用戶名"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">密碼</label>
          <input
            v-model="password"
            type="password"
            placeholder="輸入密碼"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition"
        >
          {{ loading ? '登入中...' : '🔐 登入' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || '登入失敗，請確認用戶名和密碼'
  } finally {
    loading.value = false
  }
}
</script>
