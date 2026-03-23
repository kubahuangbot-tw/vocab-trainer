# VocabTrainer - 英文單字訓練系統

智慧型 Spaced Repetition 單字學習工具，自動根據你的錯誤調整學習重點。

## 功能特點

✅ **智慧選題** - 根據錯誤頻率自動調整權重  
✅ **多種模式** - 隨機/弱點複習/混合訓練  
✅ **錯誤記錄** - 詳細記錄錯誤並提供例句  
✅ **進度追蹤** - CSV 長期保存學習數據  
✅ **即時回饋** - 顯示正確答案與用法說明

## 安裝

```bash
cd /home/deck/study/vocab_trainer
```

## 使用方法

| 命令 | 說明 |
|------|------|
| `python main.py train` | 混合模式訓練 (預設) |
| `python main.py train random` | 完全隨機抽考 |
| `python main.py train weak` | 優先測驗弱點單字 |
| `python main.py quiz 5` | 快速測驗 5 題 |
| `python main.py review` | 複習錯誤單字 |
| `python main.py stats` | 查看學習統計 |
| `python main.py list` | 列出單字庫 |

## 資料檔案

```
data/
├── progress.csv     # 學習進度 (單字權重)
└── wrong_words.csv  # 錯誤記錄 (長期dataset)
```

## 演算法設計

### Spaced Repetition 權重計算
```python
# 正確時: weight = weight * 0.8 (降低)
# 錯誤時: weight = weight * 2 + 1 (提高)
```

### 選題策略
- **Random**: 完全隨機
- **Weak**: 錯誤次數最多的優先
- **Mixed**: 70% 弱點 + 30% 新單字

## 擴充單字

在 `word_list.py` 中添加新單字：
```python
"單字": {"meaning": "中文", "level": 1-5}
```

在 `example_sentences.py` 中添加例句：
```python
"單字": "Example sentence here."
```

## 未來規劃

- [ ] Web 介面 (Streamlit/Flask)
- [ ] 匯入更多單字 (5000字庫)
- [ ] 每日複習提醒
- [ ] 統計圖表
- [ ] API 串接 (Google Sheets 同步)