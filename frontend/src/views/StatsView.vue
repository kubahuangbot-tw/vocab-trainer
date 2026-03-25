<template>
  <div class="max-w-2xl mx-auto p-4 pt-8">
    <h1 class="text-2xl font-bold mb-6">📊 學習統計</h1>

    <div v-if="loading" class="text-gray-500 text-center py-16">載入中...</div>

    <div v-else-if="stats" class="space-y-4">
      <!-- Estimated level -->
      <div class="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white text-center shadow">
        <p class="text-sm opacity-80 mb-1">估算英文程度</p>
        <p class="text-5xl font-bold">{{ stats.estimated_level || '—' }}</p>
        <p class="text-sm opacity-70 mt-2">根據 {{ stats.tested_count }} 題測試</p>
      </div>

      <!-- Stats grid -->
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-white rounded-xl shadow p-4 text-center">
          <p class="text-3xl font-bold text-green-500">{{ stats.total_correct }}</p>
          <p class="text-sm text-gray-500 mt-1">累計答對</p>
        </div>
        <div class="bg-white rounded-xl shadow p-4 text-center">
          <p class="text-3xl font-bold text-red-400">{{ stats.total_errors }}</p>
          <p class="text-sm text-gray-500 mt-1">累計答錯</p>
        </div>
        <div class="bg-white rounded-xl shadow p-4 text-center">
          <p class="text-3xl font-bold text-indigo-500">{{ stats.accuracy }}%</p>
          <p class="text-sm text-gray-500 mt-1">整體正確率</p>
        </div>
        <div class="bg-white rounded-xl shadow p-4 text-center">
          <p class="text-3xl font-bold text-orange-400">{{ stats.recent_errors_7d }}</p>
          <p class="text-sm text-gray-500 mt-1">近 7 天答錯</p>
        </div>
      </div>

      <!-- Add word -->
      <div class="bg-white rounded-xl shadow p-4">
        <h2 class="font-semibold mb-3">➕ 新增單字</h2>
        <div class="flex gap-2">
          <input
            v-model="newWord"
            @keyup.enter="addWord"
            type="text"
            placeholder="輸入英文單字"
            class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            @click="addWord"
            :disabled="addingWord"
            class="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition"
          >
            {{ addingWord ? '...' : '新增' }}
          </button>
        </div>
        <p v-if="addMsg" class="text-sm mt-2" :class="addOk ? 'text-green-600' : 'text-red-500'">{{ addMsg }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const stats = ref(null)
const loading = ref(true)
const newWord = ref('')
const addingWord = ref(false)
const addMsg = ref('')
const addOk = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.get('/users/stats')
    stats.value = data
  } finally {
    loading.value = false
  }
})

async function addWord() {
  if (!newWord.value.trim()) return
  addingWord.value = true
  addMsg.value = ''
  try {
    const { data } = await api.post('/words/add', { word: newWord.value.trim() })
    addMsg.value = data.message
    addOk.value = true
    newWord.value = ''
  } catch (e) {
    addMsg.value = e.response?.data?.detail || '新增失敗'
    addOk.value = false
  } finally {
    addingWord.value = false
  }
}
</script>
