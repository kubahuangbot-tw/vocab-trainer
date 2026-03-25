<template>
  <div class="max-w-2xl mx-auto p-4 pt-8">
    <h1 class="text-2xl font-bold mb-6">👷 管理員</h1>

    <div v-if="!auth.isAdmin" class="text-red-500 text-center py-16">無管理員權限</div>

    <div v-else class="space-y-6">
      <!-- Create user -->
      <div class="bg-white rounded-xl shadow p-5">
        <h2 class="font-semibold mb-4">➕ 新增用戶</h2>
        <div class="space-y-3">
          <input v-model="form.username" type="text" placeholder="用戶名"
            class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          <input v-model="form.password" type="password" placeholder="密碼"
            class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          <input v-model="form.display_name" type="text" placeholder="顯示名稱（可選）"
            class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          <button @click="createUser" :disabled="creating"
            class="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm transition">
            {{ creating ? '建立中...' : '建立用戶' }}
          </button>
          <p v-if="createMsg" class="text-sm" :class="createOk ? 'text-green-600' : 'text-red-500'">{{ createMsg }}</p>
        </div>
      </div>

      <!-- User list -->
      <div class="bg-white rounded-xl shadow p-5">
        <h2 class="font-semibold mb-4">👥 用戶列表</h2>
        <div v-if="loadingUsers" class="text-gray-400 text-sm">載入中...</div>
        <div v-else class="divide-y">
          <div v-for="u in users" :key="u.id" class="py-3 flex items-center gap-3">
            <span class="text-lg">{{ u.is_admin ? '👑' : '👤' }}</span>
            <div>
              <p class="font-medium text-sm">{{ u.username }}</p>
              <p v-if="u.display_name && u.display_name !== u.username" class="text-xs text-gray-400">{{ u.display_name }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const auth = useAuthStore()
const users = ref([])
const loadingUsers = ref(true)
const form = ref({ username: '', password: '', display_name: '' })
const creating = ref(false)
const createMsg = ref('')
const createOk = ref(true)

onMounted(async () => {
  if (!auth.isAdmin) return
  try {
    const { data } = await api.get('/users/list')
    users.value = data
  } finally {
    loadingUsers.value = false
  }
})

async function createUser() {
  if (!form.value.username || !form.value.password) return
  creating.value = true
  createMsg.value = ''
  try {
    const { data } = await api.post('/users/create', form.value)
    users.value.push(data)
    createMsg.value = `用戶 ${data.username} 建立成功`
    createOk.value = true
    form.value = { username: '', password: '', display_name: '' }
  } catch (e) {
    createMsg.value = e.response?.data?.detail || '建立失敗'
    createOk.value = false
  } finally {
    creating.value = false
  }
}
</script>
