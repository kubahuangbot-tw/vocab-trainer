#!/usr/bin/env python3
"""
VocabTrainer Web - Streamlit 網頁版
"""

import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os
import json
import io
from gtts import gTTS

FILE_DIR = os.path.dirname(os.path.abspath(__file__))

import sys
sys.path.insert(0, FILE_DIR)

from trainer import VocabTrainer
from storage import Storage
from word_list import WORD_LIST
from example_sentences import get_example_sentence

# 頁面設定
st.set_page_config(
    page_title="📚 VocabTrainer",
    page_icon="📚",
    layout="wide"
)

# ========== 設定檔 ==========
CONFIG_FILE = os.path.join(FILE_DIR, "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'question_count': 10,
        'review_ratio': 0.7,  # 測試比例
        'difficulty_min': 'A1',
        'difficulty_max': 'B3',
        'mode': 'mixed'
    }

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

DEFAULT_CONFIG = load_config()

# 初始化
if 'trainer' not in st.session_state:
    st.session_state.trainer = VocabTrainer()
    st.session_state.session_words = []
    st.session_state.current_index = 0
    st.session_state.session_results = []
    st.session_state.config = DEFAULT_CONFIG.copy()
    st.session_state.auto_played = False

if st.session_state.session_words and hasattr(st.session_state.trainer, 'current_index'):
    st.session_state.trainer.current_index = st.session_state.current_index

# ========== 側邊欄 ==========
with st.sidebar:
    st.header("⚙️ 設定")
    
    diff_options = ["A1", "A2", "B1", "B2", "B3", "C1", "C2"]
    
    st.write("### 📊 難度範圍")
    col1, col2 = st.columns(2)
    min_idx = diff_options.index(st.session_state.config.get('difficulty_min', 'A1'))
    
    with col1:
        difficulty_min = st.selectbox("最低", diff_options, index=min_idx, key="dm")
    with col2:
        max_idx = diff_options.index(st.session_state.config.get('difficulty_max', 'B3'))
        difficulty_max = st.selectbox("最高", diff_options, index=max(min_idx + 2, max_idx), key="dx")
    
    difficulty_range = f"{difficulty_min}-{difficulty_max}"
    
    st.write("### 🎯 訓練設定")
    mode = st.selectbox(
        "模式",
        ["mixed", "random", "weak"],
        index=["mixed", "random", "weak"].index(st.session_state.config.get('mode', 'mixed')),
        format_func=lambda x: {"mixed": "🔄 混合", "random": "🎲 隨機", "weak": "⚠️ 弱點"}[x]
    )
    
    if mode == "mixed":
        test_ratio = int(st.session_state.config.get('review_ratio', 0.7) * 100)
        review_ratio = 100 - test_ratio
        review = st.slider("複習比例", 0, 100, review_ratio)
        st.caption(f"🆕 測試: {100-review}% | 📖 複習: {review}%")
        st.session_state.review_ratio = (100 - review) / 100
    else:
        st.session_state.review_ratio = None
    
    question_count = st.slider("題目數量", 5, 30, st.session_state.config.get('question_count', 10))
    
    debug_mode = st.toggle("🔧 Debug", value=False)
    
    if st.button("💾 儲存設定"):
        new_config = {
            'question_count': question_count,
            'review_ratio': st.session_state.get('review_ratio', 0.7),
            'difficulty_min': difficulty_min,
            'difficulty_max': difficulty_max,
            'mode': mode
        }
        save_config(new_config)
        st.session_state.config = new_config
        st.success("✅ 已儲存!")

# ========== 主頁面 ==========
st.title("📚 VocabTrainer")

# 顯示單字庫統計
import json
try:
    with open('words.json', 'r', encoding='utf-8') as f:
        words = json.load(f)
    chinese_count = sum(1 for w, info in words.items() if any('\u4e00' <= c <= '\u9fff' for c in info.get('meaning', '')))
    total = len(words)
    st.caption(f"📚 單字庫: {total} 個 (🟢 中文: {chinese_count}, 🔴 英文: {total - chinese_count})")
except:
    pass

if not st.session_state.session_words:
    # ===== 歡迎畫面 =====
    cfg = st.session_state.config
    
    st.info(f"""
    📋 **當前設定**
    - 難度範圍: {cfg['difficulty_min']}-{cfg['difficulty_max']}
    - 題目數量: {cfg['question_count']} 題
    - 模式: {cfg['mode']}
    """)
    
    st.write("")
    
    if st.button("🚀 開始測試", type="primary", use_container_width=True):
        st.session_state.trainer = VocabTrainer()
        
        if debug_mode:
            fixed = ["hello", "world", "good", "love", "like"]
            st.session_state.trainer.current_words = fixed[:question_count]
            st.session_state.trainer.current_index = 0
        else:
            review_ratio = cfg.get('review_ratio', 0.7)
            words = st.session_state.trainer.select_words(
                cfg['question_count'], cfg['mode'], difficulty_range, review_ratio
            )
            st.session_state.session_words = words
        
        st.session_state.current_index = 0
        st.session_state.session_results = []
        st.session_state.auto_played = False
        st.rerun()
    
    # ========== 手動新增單字 ==========
    st.divider()
    st.subheader("➕ 新增單字")
    
    with st.expander("新增單字到資料庫", expanded=False):
        new_word = st.text_input("輸入英文單字", placeholder="例如: algorithm")
        
        if st.button("查詢並新增"):
            if not new_word:
                st.error("請輸入單字")
            else:
                # 查詢定義
                try:
                    import requests as req
                    resp = req.get(
                        f"https://api.dictionaryapi.dev/api/v2/entries/en/{new_word.strip()}",
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        if data and 'meanings' in data[0]:
                            meaning = data[0]['meanings'][0]['definitions'][0]['definition']
                            part = data[0]['meanings'][0].get('partOfSpeech', 'unknown')
                            
                            # 顯示預覽
                            st.success(f"✅ 找到定義!")
                            st.write(f"**{new_word}** [{part}]")
                            st.write(f"*{meaning}*")
                            
                            # 新增到資料庫
                            from word_list import add_word
                            add_word(new_word.lower(), meaning, 3)  # 預設 level 3
                            
                            # 標記為待複習
                            storage = Storage()
                            storage.update_progress(new_word.lower(), meaning, False)
                            storage.mark_tested(new_word.lower())
                            
                            st.success(f"✅ 已加入單字庫並標記為待複習!")
                        else:
                            st.error("❌ 無法取得定義")
                    else:
                        st.error(f"❌ 查不到 '{new_word}' 的定義")
                except Exception as e:
                    st.error(f"❌ 查詢失敗: {str(e)}")
    
    # 統計
    storage = Storage()
    stats = storage.get_stats()
    tested_count = storage.get_tested_count()
    
    st.divider()
    st.subheader("📊 學習統計")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("總單字", stats['total_words'])
    c2.metric("已測試", tested_count)
    c3.metric("正確率", f"{stats['accuracy']:.1f}%")
    c4.metric("錯誤次數", stats['total_errors'])
    
    weak = storage.get_weak_words(5)
    if weak:
        st.warning("⚠️ 需要加強:")
        for w, d in weak:
            st.write(f"• **{w}**: {d['meaning']} (錯{d['error_count']}次)")

else:
    # ===== 測試畫面 =====
    idx = st.session_state.current_index
    
    # 如果更換題目，重置 pending_next
    if 'last_idx' not in st.session_state or st.session_state.last_idx != idx:
        st.session_state.pending_next = False
        st.session_state.last_idx = idx
    
    if idx >= len(st.session_state.session_words):
        # 結果
        results = st.session_state.session_results
        correct = sum(1 for r in results if r['correct'])
        
        st.success("🎉 訓練完成!")
        st.metric("正確", f"{correct}/{len(results)}")
        
        errors = [r for r in results if not r['correct']]
        if errors:
            st.error("❌ 需要加強:")
            for r in errors:
                with st.expander(f"{r['word']} - {r['correct_meaning']}"):
                    st.write(f"你答: {r['your_answer']}")
                    st.write(f"例句: {r['example']}")
        
        if st.button("🔄 再來一輪"):
            st.session_state.session_words = []
            st.rerun()
    
    else:
        word = st.session_state.session_words[idx]
        word_data = st.session_state.trainer.get_current_word()
        question = st.session_state.trainer.get_next_question()
        
        st.progress((idx) / len(st.session_state.session_words))
        st.caption(f"題目 {idx+1} / {len(st.session_state.session_words)}")
        
        # CEFR 等級映射
        CEFR_LEVELS = {1: 'A1', 2: 'A2', 3: 'B1', 4: 'B2', 5: 'C1'}
        cefr = CEFR_LEVELS.get(word_data.get('level', 1), 'A1')
        
        # 題目 + 朗讀
        c1, c2 = st.columns([4, 1])
        with c1:
            st.subheader(f"🔍 {word}")
            st.caption(f"難度: {cefr}")
        with c2:
            if st.button("🔊 朗讀", key=f"sound_{idx}"):
                try:
                    tts = gTTS(text=word, lang='en')
                    audio = io.BytesIO()
                    tts.write_to_fp(audio)
                    audio.seek(0)
                    st.audio(audio.read(), format='audio/mp3')
                except:
                    st.error("發音失敗")
        
        # 自動朗讀第一題
        if idx == 0 and not st.session_state.auto_played:
            st.session_state.auto_played = True
            try:
                tts = gTTS(text=word, lang='en')
                audio = io.BytesIO()
                tts.write_to_fp(audio)
                audio.seek(0)
                st.audio(audio.read(), format='audio/mp3')
            except:
                pass
        
        # 選項
        st.write("請選擇正確的中文意思：")
        cols = st.columns(2)
        for i, option in enumerate(question['options']):
            with cols[i % 2]:
                if st.button(f"{option}", key=f"btn_{idx}_{i}", use_container_width=True):
                    result = st.session_state.trainer.check_answer(option)
                    result['your_answer'] = option
                    st.session_state.session_results.append(result)
                    
                    # 記錄本題答案，用 st.rerun() 前先不前進
                    st.session_state.pending_next = True
                    
                    # 顯示答案
                    if result['correct']:
                        st.success(f"✅ 正確！答案是: 「{question['correct_answer']}」")
                    else:
                        st.error(f"❌ 錯誤！你選了: 「{option}」")
                        st.info(f"正確答案: 「{question['correct_answer']}」")
        
        # 下一題按鈕 (只有在作答後顯示)
        if st.session_state.get('pending_next', False):
            if st.button("下一題 ➡️", key=f"next_{idx}"):
                st.session_state.pending_next = False
                st.session_state.current_index += 1
                st.rerun()