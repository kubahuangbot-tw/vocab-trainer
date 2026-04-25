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

      <!-- Word management -->
      <div class="bg-white rounded-xl shadow p-5">
        <h2 class="font-semibold mb-4">🗑️ 單字管理</h2>
        <div class="flex gap-2 mb-3">
          <input v-model="wordSearch" type="text" placeholder="搜尋單字..."
            class="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            @keyup.enter="searchWords" />
          <button @click="searchWords" class="bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded-lg text-sm transition">
            搜尋
          </button>
        </div>
        <div v-if="wordResults.length" class="divide-y max-h-72 overflow-y-auto">
          <div v-for="w in wordResults" :key="w.id" class="py-2.5 flex items-start gap-2">
            <div class="flex-1 min-w-0">
              <span class="font-semibold text-sm">{{ w.word }}</span>
              <span class="text-xs text-gray-400 ml-2">{{ w.cefr }}</span>
              <p class="text-xs text-gray-600 truncate">{{ w.meaning }}</p>
              <p v-if="w.suggested_meaning" class="text-xs text-indigo-600">💡 建議：{{ w.suggested_meaning }}</p>
            </div>
            <button @click="deleteWord(w)" class="text-red-400 hover:text-red-600 text-xs px-2 py-1 border border-red-200 hover:border-red-400 rounded transition shrink-0">
              刪除
            </button>
          </div>
        </div>
        <p v-if="wordDeleteMsg" class="text-xs mt-2" :class="wordDeleteOk ? 'text-green-600' : 'text-red-500'">{{ wordDeleteMsg }}</p>
      </div>

      <!-- Removal candidates -->
      <div class="bg-white rounded-xl shadow p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-semibold">🚩 移除候選</h2>
          <button @click="loadRemovalCandidates" :disabled="loadingCandidates"
            class="text-xs bg-gray-100 hover:bg-gray-200 disabled:opacity-50 px-3 py-1.5 rounded-lg transition">
            {{ loadingCandidates ? '載入中...' : '重新整理' }}
          </button>
        </div>
        <div v-if="!loadingCandidates && removalCandidates.length === 0" class="text-gray-400 text-sm text-center py-4">
          目前沒有移除候選
        </div>
        <div v-if="removalCandidates.length" class="divide-y max-h-72 overflow-y-auto mb-3">
          <div v-for="w in removalCandidates" :key="w.id" class="py-2.5 flex items-start gap-2">
            <div class="flex-1 min-w-0">
              <span class="font-semibold text-sm">{{ w.word }}</span>
              <span class="text-xs text-gray-400 ml-2">{{ w.cefr }}</span>
              <span class="ml-2 text-xs text-red-500 font-medium">🚩 {{ w.removal_vote_count }} 票</span>
              <p class="text-xs text-gray-600 truncate">{{ w.meaning }}</p>
            </div>
            <button @click="deleteCandidateWord(w)"
              class="text-red-400 hover:text-red-600 text-xs px-2 py-1 border border-red-200 hover:border-red-400 rounded transition shrink-0">
              刪除
            </button>
          </div>
        </div>
        <button v-if="removalCandidates.length > 1" @click="deleteAllCandidates"
          class="text-xs bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 px-3 py-1.5 rounded-lg transition">
          🗑️ 刪除全部 ({{ removalCandidates.length }})
        </button>
        <p v-if="candidateMsg" class="text-xs mt-2" :class="candidateOk ? 'text-green-600' : 'text-red-500'">{{ candidateMsg }}</p>
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
const wordSearch = ref('')
const wordResults = ref([])
const wordDeleteMsg = ref('')
const wordDeleteOk = ref(true)
const removalCandidates = ref([])
const loadingCandidates = ref(false)
const candidateMsg = ref('')
const candidateOk = ref(true)

onMounted(async () => {
  if (!auth.isAdmin) return
  try {
    const { data } = await api.get('/users/list')
    users.value = data
  } finally {
    loadingUsers.value = false
  }
  loadRemovalCandidates()
})

async function loadRemovalCandidates() {
  loadingCandidates.value = true
  try {
    const { data } = await api.get('/words/removal-candidates', { params: { min_votes: 1 } })
    removalCandidates.value = data
  } finally {
    loadingCandidates.value = false
  }
}

async function deleteCandidateWord(w) {
  if (!confirm(`確定要刪除「${w.word}」嗎？`)) return
  candidateMsg.value = ''
  try {
    await api.delete(`/words/${w.id}`)
    removalCandidates.value = removalCandidates.value.filter(x => x.id !== w.id)
    candidateMsg.value = `已刪除「${w.word}」`
    candidateOk.value = true
  } catch (e) {
    candidateMsg.value = e.response?.data?.detail || '刪除失敗'
    candidateOk.value = false
  }
}

async function deleteAllCandidates() {
  if (!confirm(`確定要刪除全部 ${removalCandidates.value.length} 個候選單字嗎？`)) return
  candidateMsg.value = ''
  let deleted = 0, failed = 0
  for (const w of [...removalCandidates.value]) {
    try {
      await api.delete(`/words/${w.id}`)
      removalCandidates.value = removalCandidates.value.filter(x => x.id !== w.id)
      deleted++
    } catch {
      failed++
    }
  }
  candidateMsg.value = `已刪除 ${deleted} 個${failed ? `，失敗 ${failed} 個` : ''}`
  candidateOk.value = failed === 0
}

async function searchWords() {
  if (!wordSearch.value.trim()) return
  wordDeleteMsg.value = ''
  const { data } = await api.get('/words/search', { params: { q: wordSearch.value } })
  wordResults.value = data
}

async function deleteWord(w) {
  if (!confirm(`確定要刪除「${w.word}」嗎？`)) return
  wordDeleteMsg.value = ''
  try {
    await api.delete(`/words/${w.id}`)
    wordResults.value = wordResults.value.filter(x => x.id !== w.id)
    wordDeleteMsg.value = `已刪除「${w.word}」`
    wordDeleteOk.value = true
  } catch (e) {
    wordDeleteMsg.value = e.response?.data?.detail || '刪除失敗'
    wordDeleteOk.value = false
  }
}

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

