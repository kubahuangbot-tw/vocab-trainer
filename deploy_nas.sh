#!/bin/bash
# VocabTrainer NAS 部署腳本

echo "=== VocabTrainer 部署設定 ==="

# 建立必要資料夾
mkdir -p /volume1/docker/vocabtrainer/app
mkdir -p /volume1/docker/vocabtrainer/data

# 進入 app 目錄
cd /volume1/docker/vocabtrainer/app

# 建立 docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3'
services:
  vocabtrainer:
    image: python:3.11-slim
    container_name: vocabtrainer
    restart: always
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./app:/app
    working_dir: /app
    command: >
      bash -c "
      pip install streamlit gtts pandas &&
      streamlit run app_login.py --server.port 8501 --server.address 0.0.0.0
      "
EOF

echo "=== docker-compose.yml 已建立 ==="
echo ""
echo "請執行以下指令啟動："
echo "cd /volume1/docker/vocabtrainer/app"
echo "docker-compose up -d"
echo ""
echo "啟動後訪問：http://192.168.1.109:8501"
