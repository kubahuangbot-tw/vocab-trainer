<template>
  <div class="max-w-2xl mx-auto p-4 pt-8">
    <!-- Settings bar -->
    <div class="bg-white rounded-xl shadow p-4 mb-6 flex flex-wrap gap-3 items-end">
      <div>
        <label class="text-xs text-gray-500 block mb-1">難度</label>
        <div class="flex gap-1">
          <select v-model="settings.difficulty_min" class="border rounded px-2 py-1 text-sm">
            <option v-for="l in levels" :key="l" :value="l">{{ l }}</option>
          </select>
          <span class="py-1 text-gray-400">—</span>
          <select v-model="settings.difficulty_max" class="border rounded px-2 py-1 text-sm">
            <option v-for="l in levels" :key="l" :value="l">{{ l }}</option>
          </select>
        </div>
      </div>
      <div>
        <label class="text-xs text-gray-500 block mb-1">題數</label>
        <select v-model="settings.question_count" class="border rounded px-2 py-1 text-sm">
          <option v-for="n in [5, 10, 15, 20, 30]" :key="n" :value="n">{{ n }}</option>
        </select>
      </div>
      <div>
        <label class="text-xs text-gray-500 block mb-1">模式</label>
        <select v-model="settings.mode" class="border rounded px-2 py-1 text-sm">
          <option value="random">隨機</option>
          <option value="weak">弱點</option>
          <option value="mixed">混合</option>
        </select>
      </div>
      <button @click="startQuiz" class="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-1.5 rounded-lg transition ml-auto">
        🚀 開始
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-16 text-gray-500">載入題目中...</div>

    <!-- Finished -->
    <div v-else-if="finished" class="bg-white rounded-xl shadow p-6 text-center">
      <div class="text-5xl mb-3">🏁</div>
      <h2 class="text-2xl font-bold mb-2">完成！</h2>
      <p class="text-3xl font-bold text-indigo-600 mb-1">{{ correctCount }} / {{ questions.length }}</p>
      <p class="text-gray-500 mb-6">正確率 {{ Math.round(correctCount / questions.length * 100) }}%</p>
      <div class="space-y-2 text-left mb-6">
        <div
          v-for="r in results" :key="r.word"
          class="flex items-start gap-2 text-sm p-2 rounded-lg"
          :class="r.correct ? 'bg-green-50' : 'bg-red-50'"
        >
          <span>{{ r.correct ? '✅' : '❌' }}</span>
          <div>
            <span class="font-semibold">{{ r.word }}</span>
            <span v-if="!r.correct" class="text-gray-500 ml-2">→ {{ r.correct_answer }}</span>
          </div>
        </div>
      </div>
      <button @click="startQuiz" class="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg transition">
        🔁 再測一次
      </button>
    </div>

    <!-- Quiz card -->
    <div v-else-if="current" class="bg-white rounded-xl shadow p-6">
      <div class="flex justify-between items-center mb-4 text-sm text-gray-500">
        <span>題目 {{ currentIndex + 1 }} / {{ questions.length }}</span>
        <span class="bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded font-mono">{{ current.cefr }}</span>
      </div>

      <!-- Progress bar -->
      <div class="h-1.5 bg-gray-100 rounded mb-6">
        <div
          class="h-1.5 bg-indigo-500 rounded transition-all"
          :style="{ width: `${(currentIndex / questions.length) * 100}%` }"
        />
      </div>

      <!-- Word + TTS button -->
      <div class="flex items-center justify-center gap-3 mb-4">
        <h2 class="text-4xl font-bold text-gray-800 tracking-wide">
          {{ current.word }}
        </h2>
        <button
          @click="playTTS(current.word)"
          :disabled="ttsLoading"
          class="text-indigo-400 hover:text-indigo-600 disabled:opacity-40 transition text-2xl"
          title="聽發音"
        >
          {{ ttsLoading ? '⏳' : '🔊' }}
        </button>
      </div>

      <!-- Example sentence (hidden by default) -->
      <div class="mb-6 text-center">
        <button
          v-if="current.example_sentence && !showExample"
          @click="showExample = true"
          class="text-xs text-indigo-400 hover:text-indigo-600 border border-indigo-200 hover:border-indigo-400 rounded-full px-3 py-1 transition"
        >
          💡 顯示例句
        </button>
        <div
          v-if="current.example_sentence && showExample"
          class="bg-indigo-50 border border-indigo-100 rounded-xl px-4 py-3 text-sm text-gray-700 italic"
        >
          "{{ current.example_sentence }}"
        </div>
      </div>

      <!-- Options -->
      <div class="grid grid-cols-2 gap-3">
        <button
          v-for="opt in current.options"
          :key="opt"
          @click="answer(opt)"
          :disabled="answered"
          :class="optionClass(opt)"
          class="py-3 px-4 rounded-xl text-sm font-medium transition border-2 text-left"
        >
          {{ opt }}
        </button>
      </div>

      <!-- Feedback -->
      <div v-if="answered" class="mt-4">
        <p v-if="lastCorrect" class="text-green-600 font-semibold">✅ 正確！</p>
        <p v-else class="text-red-600 font-semibold">❌ 錯誤！正確答案：{{ current.correct_answer }}</p>
        <button @click="next" class="mt-4 w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2.5 rounded-lg transition font-medium">
          下一題 ➡️
        </button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-16 text-gray-400">
      <div class="text-5xl mb-3">📚</div>
      <p>點擊「開始」來開始測驗</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../api'

const STORAGE_KEY = 'quiz_state'

const levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
const settings = ref({ difficulty_min: 'A1', difficulty_max: 'C1', question_count: 10, mode: 'random' })

const questions = ref([])
const currentIndex = ref(0)
const results = ref([])
const answered = ref(false)
const selectedOpt = ref(null)
const lastCorrect = ref(false)
const loading = ref(false)
const finished = ref(false)
const ttsLoading = ref(false)
const showExample = ref(false)

const current = computed(() => questions.value[currentIndex.value] || null)
const correctCount = computed(() => results.value.filter(r => r.correct).length)

// Save quiz state to sessionStorage whenever it changes
function saveState() {
  if (questions.value.length === 0) return
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
    questions: questions.value,
    currentIndex: currentIndex.value,
    results: results.value,
    answered: answered.value,
    selectedOpt: selectedOpt.value,
    lastCorrect: lastCorrect.value,
    finished: finished.value,
  }))
}

function clearState() {
  sessionStorage.removeItem(STORAGE_KEY)
}

// Load on mount: restore quiz state + preferences
onMounted(async () => {
  // Restore in-progress quiz first
  const saved = sessionStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      const s = JSON.parse(saved)
      if (s.questions?.length && !s.finished) {
        questions.value = s.questions
        currentIndex.value = s.currentIndex ?? 0
        results.value = s.results ?? []
        answered.value = s.answered ?? false
        selectedOpt.value = s.selectedOpt ?? null
        lastCorrect.value = s.lastCorrect ?? false
        finished.value = false
      } else if (s.finished) {
        clearState()
      }
    } catch {}
  }

  // Load user preferences
  try {
    const { data } = await api.get('/users/preferences')
    if (data) {
      settings.value = {
        difficulty_min: data.difficulty_min || 'A1',
        difficulty_max: data.difficulty_max || 'C1',
        question_count: data.question_count || 10,
        mode: data.mode || 'random',
      }
    }
  } catch {}
})

async function startQuiz() {
  try { await api.put('/users/preferences', settings.value) } catch {}

  clearState()
  loading.value = true
  finished.value = false
  results.value = []
  currentIndex.value = 0
  answered.value = false
  selectedOpt.value = null
  showExample.value = false
  try {
    const { data } = await api.get('/quiz/questions', {
      params: {
        count: settings.value.question_count,
        difficulty_min: settings.value.difficulty_min,
        difficulty_max: settings.value.difficulty_max,
        mode: settings.value.mode,
      }
    })
    questions.value = data.questions
    saveState()
  } finally {
    loading.value = false
  }
}

async function answer(opt) {
  if (answered.value) return
  answered.value = true
  selectedOpt.value = opt
  const q = current.value
  const { data } = await api.post('/quiz/answer', {
    word: q.word,
    selected: opt,
    correct_answer: q.correct_answer,
  })
  lastCorrect.value = data.correct
  results.value.push(data)
  saveState()
}

function next() {
  answered.value = false
  selectedOpt.value = null
  showExample.value = false
  if (currentIndex.value + 1 >= questions.value.length) {
    finished.value = true
    clearState()
  } else {
    currentIndex.value++
    saveState()
  }
}

async function playTTS(word) {
  if (ttsLoading.value) return
  ttsLoading.value = true
  try {
    const res = await api.get(`/quiz/tts/${encodeURIComponent(word)}`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const audio = new Audio(url)
    audio.play()
    audio.onended = () => URL.revokeObjectURL(url)
  } catch {}
  finally {
    ttsLoading.value = false
  }
}

function optionClass(opt) {
  if (!answered.value) return 'border-gray-200 bg-white hover:bg-indigo-50 hover:border-indigo-400 cursor-pointer'
  const q = current.value
  const isCorrect = opt === q.correct_answer
  if (isCorrect) return 'border-green-500 bg-green-50 text-green-700 cursor-default'
  if (opt === selectedOpt.value) return 'border-red-400 bg-red-50 text-red-700 cursor-default'
  return 'border-gray-200 bg-gray-50 text-gray-400 cursor-default'
}
</script>
