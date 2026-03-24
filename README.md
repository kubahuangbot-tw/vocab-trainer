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

## 授權

MIT
