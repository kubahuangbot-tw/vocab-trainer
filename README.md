# VocabTrainer - 多人單字測驗系統

## 專案簡介

VocabTrainer 是一個基於 Streamlit 的多人英文單字測驗系統，支援：
- SQLite 資料庫
- 多用戶學習進度追蹤
- AI 驅動的程度估算演算法
- 兒童友善內容過濾

## 功能列表

### 核心功能
- 用戶登入系統 (含管理員/訪客)
- 單字測驗 (選擇題模式)
- 學習進度追蹤
- 程度分析報告
- 新增單字 (自動翻譯)

### 程度演算法 (AI)
```python
# Laplace Smoothing + 平方根加權
final_score = Σ(adj_p × √n_i × level) / Σ(adj_p × √n_i)
adj_p = (c_i + K×0.7) / (n_i + K)
K = 5
```

### 資料庫結構 (SQLite)

```
vocab.db
├── words          # 單字庫 (10,618 個)
├── users          # 用戶
├── user_progress  # 學習進度
├── error_details  # 錯誤日誌
├── user_preferences  # 用戶偏好
└── word_sets     # 單字集
```

## 開發環境

### 本地開發

```bash
# 1. 複製專案
cd ~/study
git clone https://github.com/kubahuangbot-tw/vocab-trainer.git
cd vocab-trainer

# 2. 建立虛擬環境 (可選)
python3 -m venv venv
source venv/bin/activate

# 3. 安裝依賴
pip install streamlit pandas gtts

# 4. 執行
streamlit run app_login.py --server.port 8501
```

### 測試
```bash
python3 -m unittest test_vocab -v
```

## 部署到 Synology NAS

### 1. 準備 Docker

在 NAS 上安裝 **Container Manager** (Docker)

### 2. 建立資料夾
```
/volume1/botfoler/vocabtrainer/
├── app/          # 程式碼
│   ├── app_login.py
│   ├── trainer.py
│   ├── storage_sqlite.py
│   ├── users.py
│   └── ...
└── data/         # 資料庫
    └── vocab.db
```

### 3. 上傳檔案

```bash
# SSH 連線
ssh -i ~/.ssh/nas_key kubabot@192.168.1.109

# 建立資料夾
mkdir -p /volume1/botfoler/vocabtrainer/app
mkdir -p /volume1/botfoler/vocabtrainer/data

# 上傳檔案 (從本電腦)
scp -i ~/.ssh/nas_key -r ./* kubabot@192.168.1.109:/volume1/botfoler/vocabtrainer/app/
```

### 4. 建立 docker-compose.yml

```yaml
version: '3'
services:
  vocabtrainer:
    image: python:3.11-slim
    container_name: vocabtrainer
    restart: always
    ports:
      - "8501:8501"
    volumes:
      - ../data:/app/data
      - .:/app
    working_dir: /app
    command: >
      bash -c "pip install streamlit pandas gtts && streamlit run app_login.py --server.port 8501 --server.address 0.0.0.0"
```

### 5. 啟動容器

DSM → Container Manager → 建立專案
- 名稱: vocabtrainer
- 路徑: /volume1/botfoler/vocabtrainer/app

### 6. 存取

- 內網: http://192.168.1.109:8501
- 外網: https://your-domain.synology.me (需設定反向代理)

## 主要檔案說明

| 檔案 | 功能 |
|------|------|
| app_login.py | Streamlit 主程式 |
| trainer.py | 單字訓練邏輯 |
| storage_sqlite.py | SQLite 儲存模組 |
| users.py | 用戶驗證 |
| test_vocab.py | 單元測試 |
| words.json | 原始單字庫 |

## 常用指令

### 更新單字庫
```python
from storage_sqlite import import_words_from_json
import_words_from_json('words.json')
```

### 新增用戶
```python
from storage_sqlite import create_user
create_user('username', 'password', '顯示名稱')
```

### 查詢用戶進度
```python
from storage_sqlite import get_user, get_user_progress
user = get_user('kuba')
progress = get_user_progress(user['id'])
```

## 外部依賴

- Streamlit
- Pandas
- gTTS (發音)
- SQLite (內建)

## GitHub

https://github.com/kubahuangbot-tw/vocab-trainer

## 已知問題與排除

### passlib 與 bcrypt 5.x 不相容 → 登入 500 錯誤

**症狀：** 使用者無法登入，backend 日誌出現：
```
ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
INFO: "POST /api/auth/login HTTP/1.1" 500 Internal Server Error
```

**原因：** `passlib 1.7.4` 在執行 bcrypt wrap-bug 偵測時，會傳入一個超過 72 bytes 的測試字串，而 `bcrypt 4.x+` 開始拒絕這種操作並拋出例外，導致整個驗證流程崩潰。

**修復方式：** 在 `backend/auth.py` 中移除 passlib，改直接呼叫 `bcrypt` 套件：

```python
# 修復前（會炸）
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd_context.verify(plain, hashed)

# 修復後
import bcrypt as _bcrypt
_bcrypt.checkpw(plain.encode(), hashed.encode())
```

### docker restart 不會套用程式碼變更

**症狀：** 修改了原始碼並 `docker restart`，但 container 內的程式碼還是舊的。

**原因：** `docker restart` 只是重啟現有 container，不會重新 build image。Container 內的程式碼是在 `docker build` 時打包進去的。

**修復方式：**
- 快速修補（不 rebuild image）：用 `docker cp` 把檔案直接複製進 container：
  ```bash
  docker cp backend/auth.py vocabtrainer-backend:/app/auth.py
  docker restart vocabtrainer-backend
  ```
- 完整更新：重新 build image：
  ```bash
  cd /volume1/botfoler/vocabtrainer_v3
  docker-compose up -d --build
  ```

## 授權

MIT
