# VocabTrainer 開發日誌

## 目前版本
- **App 版號**：`2026.0425.2`（顯示於 nav bar）
- **APK 最新版**：`VocabTrainer-2026.0425.2.apk`（NAS: `/volume1/botfoler/`）
- **Backend**：FastAPI + SQLite（quiz）/ PostgreSQL Supabase（users/words）
- **Frontend**：Vue 3 + Vite + Capacitor 8（Android APK）
- **圖片來源**：Cloudflare R2（`https://pub-b6b3766953db4ce69c3b6d781c16e708.r2.dev`）

---

## APK 版本紀錄

| 版本 | 日期 | 內容 |
|---|---|---|
| 2026.0416.1 | 2026-04-16 | 初版，空白頁問題（API URL 未設定）|
| 2026.0416.2 | 2026-04-16 | 修正 API URL：APK 版改用完整 NAS URL |
| 2026.0416.3 | 2026-04-16 | 修正版號顯示（v3.1-release → 2026.0416.2）|
| 2026.0421.1 | 2026-04-21 | 新增「🚩 建議移除此題」按鈕（QuizView）+ Admin 移除候選區塊 |
| 2026.0421.2 | 2026-04-21 | 嘗試修圖片（錯誤：加 serverOrigin，根本原因未找到）|
| 2026.0421.3 | 2026-04-21 | 加 debug：圖片失敗顯示 URL（輔助定位問題）|
| 2026.0421.4 | 2026-04-21 | 修圖片：NAS quiz.py 改用 R2 URL；但 🚩 按鈕 template 遺失 |
| 2026.0421.5 | 2026-04-21 | 修復 🚩 建議移除按鈕遺失；更新版號 |
| 2026.0421.6 | 2026-04-21 | 新增 📝 建議例句功能；更新版號 |
| 2026.0421.7 | 2026-04-25 | 新增 🤷 我不知道按鈕（答題前顯示，選後算答錯）|
| 2026.0425.1 | 2026-04-25 | 修正版號命名（改用 build 當天日期）|
| 2026.0425.2 | 2026-04-25 | 新增 🖼️ 建議換圖按鈕（只在有圖片時顯示，投票制）|

---

## Build 流程

```bash
cd /home/deck/study/vocab_trainer/frontend
npm run build
npx cap sync android
ANDROID_HOME=~/Android/Sdk ./android/gradlew -p android assembleDebug

# 命名並上傳
cp android/app/build/outputs/apk/debug/app-debug.apk /tmp/VocabTrainer-YYYY.MMDD.N.apk
scp -i ~/.ssh/nas_key /tmp/VocabTrainer-YYYY.MMDD.N.apk kubabot@192.168.1.109:/volume1/botfoler/
```

---

## 已實作功能

### Quiz 頁面（答題後出現）
- 🗑️ 建議移除（投票制，防重複）
- 🖼️ 圖片不符（投票制，只在有圖片時顯示）
- ✏️ 建議定義（輸入更好的中文定義）
- 📝 建議例句（只在有例句時顯示）
- 🔊 TTS 發音（APK 用 Capacitor native TTS，網頁用 Web Speech API）
- 💡 顯示例句（答題前可展開）

### Admin 頁面
- ➕ 新增用戶
- 👥 用戶列表
- 🗳️ 被投票移除的單字（依票數排序，可直接刪除）← **2026-04-16 新增**
- 🗑️ 單字管理（手動搜尋刪除）

---

## 遇到的問題紀錄

### [2026-04-16] APK 空白頁
- **症狀**：點「開始」後測驗頁面空白
- **原因**：`src/api.js` 的 `baseURL` 預設為 `/api`（相對路徑），在 APK 中變成 `file:///api`，無法連線
- **修法**：偵測 `Capacitor.isNativePlatform()`，APK 改用完整 URL `https://vocab.kubahuang.synology.me:7443/api`

### [2026-04-21] 圖片不顯示
- **症狀**：APK 和網頁版都看不到圖片
- **錯誤方向 1**：以為是 APK 的 Capacitor WebView 無法載入相對 URL（`/word_images/...`），加了 `serverOrigin` 前綴 → 無效
- **錯誤方向 2**：以為是 SSL 或 CSP 問題 → 無關
- **真正原因**：NAS 的 `backend/routers/quiz.py` 用的是舊路徑 `/word_images/{filename}`，但本地版本早就改為 Cloudflare R2 URL（`https://pub-xxx.r2.dev/{filename}`）。NAS 的 quiz.py 沒有同步，導致圖片指向 NAS nginx 路徑，而 APK 不認識相對路徑。
- **修法**：scp 本地 quiz.py 到 NAS，rebuild backend container
- **教訓**：本地和 NAS 的 backend code 長期不同步是風險。重要修改要記得雙向同步。

### [2026-04-21] 🚩 建議移除按鈕遺失
- **症狀**：0421.4 版本，答題後看不到「🚩 建議移除此題」也看不到「✏️ 建議定義」
- **原因**：在 0421.2～0421.4 的多次修改中，QuizView.vue 被 NAS→local 覆寫再 local→NAS 覆寫，其中一次覆寫把 🚩 的 template block 弄掉了。JS logic（submitFlag, flagLoading 等）還在，但 template 裡的按鈕不見了。
- **修法**：重新在 template 的 feedback 區段加回 🚩 按鈕
- **教訓**：多次來回同步檔案時要 diff 確認，不要盲目覆寫。每次重要 feature 加完後應該 git commit。

### [2026-04-16] 建議移除 → 送出失敗 (405)
- **症狀**：按「建議移除」出現「送出失敗」
- **原因 1**：NAS backend code 是舊版，沒有 `suggest-remove` 路由
- **原因 2**：NAS `requirements.txt` 沒有 `psycopg2-binary`，`storage_postgres.py` 無法 import
- **原因 3**：Supabase 缺少 `word_removal_votes`、`word_image_bad_votes` 兩張 table，及 `words` 缺少 `removal_vote_count`、`image_bad_count` 欄位
- **修法**：
  1. 同步 backend code 到 NAS（scp routers/words.py、main.py、storage_postgres.py 等）
  2. 同步 requirements.txt（加上 `psycopg2-binary==2.9.11`）
  3. 重新 build Docker image（`docker-compose build --no-cache backend`）
  4. 在 Supabase 補建缺少的 table 和欄位

---

## DB（Supabase）現況

- **Project URL**：`https://wzxqbvrtrjgndfhxxyjw.supabase.co`
- **Region**：ap-south-1

### Tables（共 11 張）
| Table | 說明 |
|---|---|
| `words` | 10,847 筆單字，含 `removal_vote_count`、`image_bad_count` |
| `users` | 4 位用戶（含 admin） |
| `user_progress` | 411 筆學習進度 |
| `wrong_records` | 125 筆答錯記錄 |
| `error_details` | 錯誤詳情 |
| `test_history` | 測驗歷史 |
| `word_sets` | 單字集 |
| `word_set_members` | 單字集成員 |
| `user_preferences` | 用戶偏好設定 |
| `word_removal_votes` | 移除投票（2026-04-16 補建）|
| `word_image_bad_votes` | 圖片不符投票（2026-04-16 補建）|

---

## NAS Backend 部署

- **路徑**：`/volume1/botfoler/vocabtrainer_v3/`
- **重 build 指令**：
```bash
cd /volume1/botfoler/vocabtrainer_v3
/usr/local/bin/docker-compose build --no-cache backend && /usr/local/bin/docker-compose up -d backend
```
- **注意**：每次更新 backend code 後需重新 build（不是 restart）

---

## TODO

- [ ] TTS 問題：手機 Chrome 按 🔊 沒聲音（APK 版正常，網頁版不穩定）
- [ ] 部署後端到 Fly.io（code 已備好，尚未執行 `fly deploy`）
- [ ] 建立正式版 APK build 流程（目前都是 debug build）
