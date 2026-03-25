# VocabTrainer — Roblox 整合指南

此文件說明如何在 Roblox 遊戲中使用 `vocab_for_roblox.json` 單字資料庫。

---

## 檔案說明

**檔案：** `vocab_for_roblox.json`
**單字數量：** 10,844 個
**編碼：** UTF-8
**格式：** JSON Array，每個元素代表一個單字

---

## 資料結構

```json
[
  {
    "word": "abundant",
    "word_type": "adjective",
    "meaning": "大量的；豐富的",
    "cefr": "b2",
    "difficulty": 4,
    "example_sentence": "The region has abundant natural resources."
  },
  ...
]
```

### 欄位說明

| 欄位 | 型別 | 說明 |
|------|------|------|
| `word` | string | 英文單字 |
| `word_type` | string | 詞性（`noun`, `verb`, `adjective`, `adverb`，可能為 null） |
| `meaning` | string | 中文意思 |
| `cefr` | string | CEFR 等級（`a1`, `a2`, `b1`, `b2`, `c1`, `c2`，**全小寫**） |
| `difficulty` | integer | 難度數字（1=A1, 2=A2, 3=B1, 4=B2, 5=C1, 6=C2） |
| `example_sentence` | string | 英文例句（可能為 null） |

### CEFR 等級對照

| difficulty | cefr | 程度 |
|-----------|------|------|
| 1 | a1 | 初學 |
| 2 | a2 | 基礎 |
| 3 | b1 | 中級 |
| 4 | b2 | 中高級 |
| 5 | c1 | 高級 |
| 6 | c2 | 精通 |

---

## 在 Roblox 中載入資料

### 方法 A：從 HTTP API 取得（推薦，即時資料）

透過 VocabTrainer 後端 API 取得單字（需要網路權限）：

```lua
local HttpService = game:GetService("HttpService")

-- 取得指定難度的題目（含選項）
local function getQuizQuestions(diffMin, diffMax, count)
    local url = string.format(
        "https://vocab.kubahuang.synology.me/api/quiz/questions?difficulty_min=%s&difficulty_max=%s&count=%d&mode=random",
        diffMin, diffMax, count
    )
    -- 登入取得 token（用 guest 帳號）
    local loginRes = HttpService:RequestAsync({
        Url = "https://vocab.kubahuang.synology.me/api/auth/login",
        Method = "POST",
        Headers = { ["Content-Type"] = "application/x-www-form-urlencoded" },
        Body = "username=guest&password="
    })
    local token = HttpService:JSONDecode(loginRes.Body).access_token

    local res = HttpService:RequestAsync({
        Url = url,
        Method = "GET",
        Headers = { Authorization = "Bearer " .. token }
    })
    return HttpService:JSONDecode(res.Body).questions
end

-- 回傳格式：
-- questions[i].word          -- 單字
-- questions[i].options       -- 四個選項（中文）
-- questions[i].correct_answer -- 正確答案
-- questions[i].cefr          -- 等級
-- questions[i].example_sentence -- 例句
```

### 方法 B：用靜態 JSON 檔（離線，需先放到 Roblox）

由於 Roblox 沙盒限制，靜態 JSON 需透過以下方式之一放入遊戲：
1. 放進 `ReplicatedStorage` 的 `StringValue`（適合小資料集）
2. 透過 HTTP 從你的 NAS 下載（同方法 A，但取整份 JSON）

```lua
-- 範例：從 NAS 下載整份 JSON
local HttpService = game:GetService("HttpService")
local res = HttpService:GetAsync("https://vocab.kubahuang.synology.me/static/vocab_for_roblox.json")
local words = HttpService:JSONDecode(res)

-- 篩選 B1 等級單字
local b1Words = {}
for _, w in ipairs(words) do
    if w.cefr == "b1" then
        table.insert(b1Words, w)
    end
end
```

---

## 常用操作範例（Lua）

### 隨機抽取指定難度的單字

```lua
local function getRandomWords(words, cefr, count)
    local filtered = {}
    for _, w in ipairs(words) do
        if w.cefr == cefr then
            table.insert(filtered, w)
        end
    end
    -- Fisher-Yates shuffle
    for i = #filtered, 2, -1 do
        local j = math.random(i)
        filtered[i], filtered[j] = filtered[j], filtered[i]
    end
    local result = {}
    for i = 1, math.min(count, #filtered) do
        table.insert(result, filtered[i])
    end
    return result
end

local quiz = getRandomWords(words, "b1", 10)
```

### 出選擇題（從 API 方法 A 已包含選項）

```lua
-- API 已自動產生 4 個選項，直接用：
for _, q in ipairs(questions) do
    print("單字：" .. q.word)
    print("選項：")
    for i, opt in ipairs(q.options) do
        print(i .. ". " .. opt)
    end
    print("正確：" .. q.correct_answer)
end
```

---

## 統計資料

| CEFR | 單字數 |
|------|--------|
| A1 | 732 |
| A2 | 1,002 |
| B1 | 4,630 |
| B2 | 3,093 |
| C1 | 1,128 |
| C2 | 259 |
| **總計** | **10,844** |

---

## 後端 API 端點總覽

Base URL: `https://vocab.kubahuang.synology.me`

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/auth/login` | POST | 登入取得 JWT token |
| `/api/quiz/questions` | GET | 取得測驗題目（含選項） |
| `/api/quiz/answer` | POST | 提交答案、記錄進度 |
| `/api/quiz/tts/{word}` | GET | 取得單字發音 MP3 |
| `/api/users/stats` | GET | 取得學習統計 |
