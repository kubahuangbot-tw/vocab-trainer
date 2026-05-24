# VocabTrainer v3 — 架構說明

## 系統架構

```
Internet
   │
   ▼
NAS (Synology, 192.168.1.106)
   │
   ├── [Docker] vocabtrainer-frontend  (nginx)
   │     port 8501 (HTTP, LAN)
   │     port 7443 (HTTPS, 對外)  ← vocab.kubahuang.synology.me:7443
   │     SSL: /usr/syno/etc/certificate/system/default/
   │
   ├── [Docker] vocabtrainer-backend   (FastAPI / uvicorn)
   │     port 8000 (container 內部，由 nginx proxy 轉發)
   │     volume: ./data → /data  (word_images 在此)
   │
   └── [Docker] vocabtrainer-postgres  (PostgreSQL 17)
         port 5432 (container 內部)
         volume: ./data/postgres → /var/lib/postgresql/data
```

## 目錄結構

```
vocabtrainer_v3/
│
├── docker-compose.yml          ← 全服務啟動設定
├── deploy_nas.sh               ← 部署腳本
├── run_nightly.sh              ← 每日 3am 排程腳本（Task Scheduler 呼叫）
│
├── backend/                    ← FastAPI 後端
│   ├── main.py                 ← 應用入口，路由掛載
│   ├── storage_postgres.py     ← ★ 唯一 DB 存取層（PostgreSQL）
│   ├── storage_sqlite.py       ← 舊版相容層（trainer.py / users.py 仍引用）
│   ├── auth.py                 ← JWT 認證
│   ├── trainer.py              ← 出題邏輯（難度、弱點模式）
│   ├── users.py                ← 使用者管理
│   ├── words.py                ← 單字輔助函數
│   ├── routers/
│   │   ├── auth.py             ← POST /api/auth/login
│   │   ├── words.py            ← GET/POST /api/words/*
│   │   ├── quiz.py             ← GET /api/quiz/*
│   │   └── users.py            ← GET/POST /api/users/*
│   ├── config.py               ← 路徑常數
│   └── requirements.txt
│
├── frontend/                   ← Vue 3 + Vite + TailwindCSS
│   ├── src/
│   │   ├── views/
│   │   │   ├── QuizView.vue    ← 主測驗介面（含建議定義、圖片顯示）
│   │   │   ├── AdminView.vue   ← 管理介面（刪除單字、用戶管理）
│   │   │   └── LoginView.vue
│   │   ├── api.js              ← 所有後端 API 呼叫
│   │   └── stores/             ← Pinia 狀態管理
│   ├── nginx.conf              ← nginx 反向代理設定
│   └── Dockerfile
│
├── data/                       ← 持久化資料（volume mount）
│   ├── postgres/               ← PostgreSQL 資料檔（勿手動修改）
│   ├── word_images/            ← ~9,400 張單字圖片 ({word}.jpg)
│   ├── ssl-fullchain.pem       ← SSL 憑證（從 Synology 掛載）
│   └── ssl-privkey.pem
│
├── nightly_review.py           ← 每日自動審核腳本（Gemini API）
├── review_suggestions.py       ← 手動審核腳本（定義建議 + 例句品質）
├── download_word_images.py     ← 補抓缺少的單字圖片
├── example_sentences.py        ← 補生成缺少的例句
│
├── logs/                       ← nightly_review.py 輸出 log
│
└── archive/                    ← 舊版備份（不再使用）
    ├── old_streamlit/          ← 舊 Streamlit UI（已被 Vue 取代）
    ├── old_scripts/            ← 舊匯入/翻譯腳本（一次性任務已完成）
    └── old_data/
        ├── vocab.db            ← 舊 SQLite 備份（已遷移到 PostgreSQL）
        └── supabase_backup.sql ← 舊 Supabase 備份（已遷移到本機 PG）
```

## 資料庫

- **引擎**：PostgreSQL 17（Docker container `vocabtrainer-postgres`）
- **連線字串**：`postgresql://postgres:LFHGDXKg22rnSDPO@postgres:5432/vocabtrainer`
- **直接查詢**（NAS SSH）：
  ```bash
  docker exec vocabtrainer-postgres psql -U postgres -d vocabtrainer -c "SELECT COUNT(*) FROM words;"
  ```
- **Tables**：

| Table | 說明 |
|---|---|
| words | 10,824 個單字（word, meaning, cefr, example_sentence, image_path, suggested_meaning） |
| users | 4 位使用者（含 admin） |
| user_progress | 學習進度 |
| wrong_records | 答錯記錄 |
| error_details | 錯誤詳細 |
| test_history | 測驗歷史 |
| word_sets | 單字集 |
| word_set_members | 單字集成員 |
| user_preferences | 用戶設定 |
| word_removal_votes | 用戶投票移除記錄 |
| word_image_bad_votes | 用戶回報圖片不良 |

## 主要 API 端點

| Method | Path | 說明 |
|---|---|---|
| POST | /api/auth/login | 登入，回傳 JWT |
| GET | /api/quiz/question | 取得測驗題目 |
| POST | /api/quiz/answer | 提交答案 |
| GET | /api/words/search | 搜尋單字（Admin） |
| POST | /api/words/suggest | 提交定義建議 |
| DELETE | /api/words/{id} | 刪除單字（Admin） |
| GET | /api/words/pending-suggestions | 待審核定義建議 |
| GET | /api/words/pending-sentences | 待審核例句 |
| POST | /api/words/{id}/review-suggestion | 審核定義建議 |
| POST | /api/words/{id}/review-sentence | 審核例句 |

## 部署指令

```bash
cd /volume1/botfoler/vocabtrainer_v3

# 全部重啟
/usr/local/bin/docker-compose up -d

# 只重建後端
/usr/local/bin/docker-compose build --no-cache backend && /usr/local/bin/docker-compose up -d backend

# 只重建前端
/usr/local/bin/docker-compose build --no-cache frontend && /usr/local/bin/docker-compose up -d frontend

# 查看 log
/usr/local/bin/docker-compose logs -f backend
```

## 每日自動審核（Nightly Review）

腳本：`/volume1/botfoler/vocabtrainer_v3/run_nightly.sh`

設定排程（Synology Task Scheduler）：
- 控制台 → 工作排程器 → 新增 → 使用者定義腳本
- 帳號：kubabot，時間：每天 03:00
- 指令：`/volume1/botfoler/vocabtrainer_v3/run_nightly.sh`

執行內容：
1. 移除投票審核（heuristic，0 token）
2. Meta 例句偵測（regex，0 token）
3. 建議定義審核（Gemini 2.5 Flash，批次 10 個/call）
4. 例句品質審核（Gemini，每週日才執行，100 筆/次）

LLM：Gemini 2.5 Flash（免費額度 1500 req/day，月費幾乎為 $0）

## 外部服務

| 服務 | 用途 |
|---|---|
| Gemini 2.5 Flash API | 單字品質審核（nightly_review） |
| Synology SSL 憑證 | HTTPS for vocab.kubahuang.synology.me:7443 |

**已停用**：~~Supabase~~、~~MiniMax API~~、~~Streamlit~~
