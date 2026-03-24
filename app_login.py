#!/usr/bin/env python3
"""
VocabTrainer - 多人版本 (含登入)
"""

import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os
import json
import io
from gtts import gTTS
from pathlib import Path

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = Path(FILE_DIR) / "data"

import sys
sys.path.insert(0, FILE_DIR)

from trainer import VocabTrainer
from word_list import WORD_LIST
import users

# 頁面設定
st.set_page_config(
    page_title="📚 VocabTrainer",
    page_icon="📚",
    layout="wide"
)

# 初始化管理員
users.init_admin()

# === Session State ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# ========== 用戶儲存 ==========
def get_user_storage(username):
    """取得用戶資料目錄"""
    user_dir = users.get_user_data_dir(username)
    return UserStorage(username, user_dir)

class UserStorage:
    """用戶專屬儲存 (模擬 Storage 介面)"""
    
    def __init__(self, username, data_dir):
        self.username = username
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        
        self.progress_file = data_dir / "progress.csv"
        self.wrong_file = data_dir / "wrong_words.csv"
        self.tested_file = data_dir / "tested_words.json"
        
        self._init_files()
    
    def _init_files(self):
        if not self.progress_file.exists():
            self.progress_file.write_text("word,correct_count,error_count,last_reviewed,weight,meaning")
        if not self.wrong_file.exists():
            self.wrong_file.write_text("word,meaning,count")
        if not self.tested_file.exists():
            self.tested_file.write_text("{}")
    
    def get_progress(self):
        try:
            df = pd.read_csv(self.progress_file)
            return df.to_dict('records')
        except:
            return []
    
    def update_progress(self, word, meaning, correct):
        progress = self.get_progress()
        found = next((p for p in progress if p['word'] == word), None)
        now = datetime.now().isoformat()
        
        if found:
            found['correct_count'] = found.get('correct_count', 0) + (1 if correct else 0)
            found['error_count'] = found.get('error_count', 0) + (0 if correct else 1)
            found['last_reviewed'] = now
            found['weight'] = max(0.1, found.get('weight', 1) - 0.1 if correct else +0.2)
        else:
            progress.append({
                'word': word,
                'correct_count': 1 if correct else 0,
                'error_count': 0 if correct else 1,
                'last_reviewed': now,
                'weight': 0.5 if correct else 1.5,
                'meaning': meaning
            })
        
        pd.DataFrame(progress).to_csv(self.progress_file, index=False)
    
    def mark_tested(self, word):
        tested = self.get_tested_words()
        tested[word] = datetime.now().isoformat()
        self.tested_file.write_text(json.dumps(tested, ensure_ascii=False))
    
    def get_tested_words(self):
        try:
            return json.loads(self.tested_file.read_text())
        except:
            return {}
    
    def get_weak_words(self, count=10):
        try:
            df = pd.read_csv(self.wrong_file)
            return df.sort_values('count', ascending=False).head(count).to_dict('records')
        except:
            return []
    
    def add_wrong_record(self, word, correct_meaning, user_answer, example=None):
        wrong = self.get_weak_words(100)  # load all
        found = next((w for w in wrong if w['word'] == word), None)
        if found:
            found['count'] = found.get('count', 0) + 1
        else:
            wrong.append({'word': word, 'meaning': correct_meaning, 'count': 1})
        pd.DataFrame(wrong).to_csv(self.wrong_file, index=False)
    
    def get_wrong_records(self):
        return self.get_weak_words(50)

# ========== 登入函式 ==========
def login_form():
    st.markdown("""
    <style>
    .login-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.title("📚 VocabTrainer")
    st.markdown("### 多人單字測驗系統")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login"):
            username = st.text_input("用戶名", placeholder="輸入用戶名")
            password = st.text_input("密碼", type="password", placeholder="輸入密碼")
            
            col_a, col_b = st.columns(2)
            with col_a:
                login_btn = st.form_submit_button("🔐 登入", use_container_width=True)
            with col_b:
                st.markdown("###")
                st.caption("👷 帳號由管理員建立")
            
            if login_btn:
                if users.verify_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("❌ 用戶名或密碼錯誤")
    
    st.markdown("---")
    st.write("**現有用戶:**")
    for u in users.list_users():
        icon = "👑" if u["is_admin"] else "👤"
        email = f" ({u['email']})" if u.get("email") else ""
        st.write(f"{icon} `{u['username']}`{email}")

# ========== 主程式 ==========
def main():
    # 側邊欄
    with st.sidebar:
        st.title("📚 VocabTrainer")
        
        if st.session_state.logged_in:
            st.write(f"👤 **{st.session_state.username}**")
            
            # 管理員
            user_list = users.list_users()
            current = next((u for u in user_list if u["username"] == st.session_state.username), None)
            is_admin = current and current.get("is_admin")
            
            # 新增單字功能 (所有登入用戶都可使用)
            st.markdown("---")
            st.markdown("### 📝 新增單字")
            
            with st.expander("加入想學的單字"):
                st.caption("自動翻譯並加入單字庫")
                with st.form("add_word"):
                    new_word = st.text_input("輸入英文單字", key="new_word")
                    submit = st.form_submit_button("➕ 新增", use_container_width=True)
                    
                    if submit and new_word:
                        from storage_sqlite import add_word_auto, get_user
                        user = get_user(st.session_state.username)
                        user_id = user['id'] if user else None
                        result = add_word_auto(new_word.strip(), user_id)
                        if result['success']:
                            st.success(f"{result['message']}")
                            st.caption(f"{result['word']}: {result['meaning']}")
                        else:
                            st.error(f"❌ {result['message']}")
                
                # 顯示最近新增的單字
                st.write("---")
                st.caption("最近新增")
                from storage_sqlite import get_db
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT word, meaning, created_at 
                        FROM words 
                        ORDER BY id DESC LIMIT 5
                    """)
                    for row in cursor.fetchall():
                        st.write(f"• {row[0]}: {row[1]}")
            
            # 管理員功能
            if is_admin:
                st.markdown("---")
                st.markdown("### 👷 管理員")
                
                with st.expander("👥 用戶管理"):
                    st.caption("自動翻譯並加入單字庫")
                    with st.form("add_word"):
                        new_word = st.text_input("輸入英文單字", key="new_word_admin")
                        submit = st.form_submit_button("➕ 新增", use_container_width=True)
                        
                        if submit and new_word:
                            from storage_sqlite import add_word_auto, get_user
                            user = get_user(st.session_state.username)
                            user_id = user['id'] if user else None
                            result = add_word_auto(new_word.strip(), user_id)
                            if result['success']:
                                st.success(f"{result['message']}")
                                st.caption(f"{result['word']}: {result['meaning']}")
                            else:
                                st.error(f"❌ {result['message']}")
                    
                    # 顯示最近新增的單字
                    st.write("---")
                    st.caption("最近新增")
                    from storage_sqlite import get_db
                    with get_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT word, meaning, created_at 
                            FROM words 
                            ORDER BY id DESC LIMIT 5
                        """)
                        for row in cursor.fetchall():
                            st.write(f"• {row[0]}: {row[1]}")
                
                with st.expander("👥 用戶管理"):
                    for u in user_list:
                        icon = "👑" if u["is_admin"] else "👤"
                        st.write(f"{icon} {u['username']}")
                    
                    st.write("---")
                    with st.form("add"):
                        st.write("**新增用戶**")
                        nu = st.text_input("用戶名", key="nu")
                        np = st.text_input("密碼", type="password", key="np")
                        ne = st.text_input("Email (可選)", key="ne")
                        if st.form_submit_button("➕ 建立"):
                            ok, msg = users.create_user(nu, np, ne)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
            
            if st.button("🚪 登出"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.rerun()
        else:
            st.info("請先登入")
    
    # 登入檢查
    if not st.session_state.logged_in:
        login_form()
        return
    
    # 用戶資料
    user_storage = get_user_storage(st.session_state.username)
    
    # 測驗
    st.title("🎯 單字測驗")
    
    # 用戶設定檔 - 從 SQLite 讀取
    from storage_sqlite import get_user as sqlite_get_user
    from storage_sqlite import get_user_preferences, save_user_preferences, create_preferences_table
    
    # 確保偏好表存在
    create_preferences_table()
    
    # 取得用戶 ID
    sqlite_user = sqlite_get_user(st.session_state.username)
    user_id = sqlite_user['id'] if sqlite_user else None
    
    # 嘗試從 SQLite 讀取偏好
    saved_config = {}
    if user_id:
        prefs = get_user_preferences(user_id)
        if prefs:
            saved_config = prefs
    
    # 預設值
    default_config = {
        'difficulty_min': 'A1',
        'difficulty_max': 'C1',
        'question_count': 10,
        'mode': 'random'
    }
    
    # 設定
    if 'config' not in st.session_state:
        st.session_state.config = saved_config if saved_config else default_config
    
    cfg = st.session_state.config
    
    with st.sidebar.expander("⚙️ 設定"):
        diff_options = ['A1', 'A2', 'B1', 'B2', 'C1']
        min_idx = diff_options.index(cfg.get('difficulty_min', 'A1'))
        max_idx = diff_options.index(cfg.get('difficulty_max', 'C1'))
        
        cfg['difficulty_min'] = st.selectbox("最低", diff_options, index=min_idx, key="dm")
        cfg['difficulty_max'] = st.selectbox("最高", diff_options, index=max(min_idx+2, max_idx), key="dx")
        
        cfg['question_count'] = st.slider("題目數", 5, 50, cfg['question_count'])
        cfg['mode'] = st.selectbox("模式", ["random", "weak", "mixed"], index=0)
        
        # 儲存按鈕
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 儲存設定", use_container_width=True):
                if user_id:
                    save_user_preferences(user_id, cfg)
                    st.success("✅ 已儲存！")
                else:
                    st.error("❌ 無法儲存")
        with col2:
            if st.button("🔄 重新開始", use_container_width=True):
                st.session_state.session_words = []
                st.session_state.session_results = []
                st.session_state.current_index = 0
    
    # 程度分析 (隱藏版)
    from storage_sqlite import get_user as sqlite_get_user, get_user_progress, get_weak_words, update_progress, add_wrong_record
    with st.sidebar.expander("📊 程度分析", expanded=False):
        # 從 SQLite 取得學習資料
        sqlite_user = sqlite_get_user(st.session_state.username)
        user_id = sqlite_user["id"] if sqlite_user else None
        if user_id:
            progress = get_user_progress(user_id)
            weak_words = get_weak_words(user_id, 20)
        else:
            progress = {}
            weak_words = []
        tested_count = len(progress)
        if tested_count > 0:
            # 計算各等級正確率
            level_stats = {1: {'correct': 0, 'total': 0}, 2: {'correct': 0, 'total': 0}, 
                          3: {'correct': 0, 'total': 0}, 4: {'correct': 0, 'total': 0}, 5: {'correct': 0, 'total': 0}}
            
            for word, p in progress.items():
                # word already obtained
                if word in WORD_LIST:
                    level = WORD_LIST[word].get('level', 3)
                    correct = p.get('correct_count', 0)
                    errors = p.get('error_count', 0)
                    total = correct + errors
                    
                    if total > 0:
                        level_stats[level]['correct'] += correct
                        level_stats[level]['total'] += total
            
            # 顯示各等級正確率
            CEFR = {1: 'A1', 2: 'A2', 3: 'B1', 4: 'B2', 5: 'C1'}
            
            cols = st.columns(5)
            for i, (level, stats) in enumerate(level_stats.items()):
                if stats['total'] > 0:
                    rate = stats['correct'] / stats['total'] * 100
                    with cols[i]:
                        st.metric(f"{CEFR[level]}", f"{rate:.0f}%", f"{stats['total']}題")
            
            # AI 演算法估算整體程度
            import math
            K = 5
            TARGET_ACC = 0.7
            level_map = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5}
            reverse_map = {v: k for k, v in level_map.items()}
            
            total_weighted_score = 0
            total_weight = 0
            
            for level in [1, 2, 3, 4, 5]:
                stats = level_stats.get(level, {})
                n_i = stats.get('total', 0)
                c_i = stats.get('correct', 0)
                
                if n_i == 0:
                    continue
                
                # Laplace Smoothing
                adj_p = (c_i + K * TARGET_ACC) / (n_i + K)
                # Weight by Square Root
                weight = math.sqrt(n_i)
                # Level Score
                level_score = adj_p * weight
                
                total_weighted_score += level_score * level
                total_weight += level_score
            
            if total_weight > 0:
                final_score = total_weighted_score / total_weight
                
                # 判斷等級
                base_level = reverse_map.get(math.floor(final_score), "A1")
                is_plus = (final_score - math.floor(final_score)) >= 0.5
                level_suffix = "+" if is_plus else ""
                
                level_names = {1: '基礎', 2: '初級', 3: '中級', 4: '中高級', 5: '高級'}
                est_level = f"{base_level}{level_suffix} ({level_names.get(level_map.get(base_level, 3), '')})"
                
                st.success(f"📈 估算程度: **{est_level}** ({final_score:.2f})")
                st.caption(f"(根據 {tested_count} 題測試)")
        else:
            st.info("尚未有測試紀錄")
    
    # 單字庫
    chinese = sum(1 for w in WORD_LIST.values() if w.get('meaning', '') and any('\u4e00' <= c <= '\u9fff' for c in w['meaning']))
    st.caption(f"📊 單字庫: {len(WORD_LIST)} | ✅ 中文: {chinese}")
    
    # 初始化
    if 'session_words' not in st.session_state or not st.session_state.session_words:
        from trainer import VocabTrainer
        from storage_sqlite import get_user
        
        # 取得用戶 ID
        sqlite_user = get_user(st.session_state.username)
        user_id = sqlite_user['id'] if sqlite_user else None
        
        trainer = VocabTrainer(user_id=user_id)
        trainer.storage = user_storage
        trainer.current_words = WORD_LIST  # Use global WORD_LIST
        
        difficulty = f"{cfg['difficulty_min']}-{cfg['difficulty_max']}"
        
        # 使用 select_words 方法
        words = trainer.select_words(
            count=cfg['question_count'],
            mode=cfg['mode'],
            difficulty=difficulty,
            review_ratio=0.3
        )
        
        # 轉換為題目格式
        session_words = []
        for word in words:
            if word not in WORD_LIST:
                continue
            
            word_data = WORD_LIST[word]
            meaning = word_data.get('meaning', '')
            level = word_data.get('level', 3)
            
            # 取得選項
            all_meanings = [x['meaning'] for x in WORD_LIST.values() 
                          if x.get('meaning', '') and any('\u4e00' <= c <= '\u9fff' for c in x['meaning'])]
            wrong_options = random.sample([m for m in all_meanings if m != meaning], 3)
            options = wrong_options + [meaning]
            random.shuffle(options)
            
            session_words.append({
                'word': word,
                'meaning': meaning,
                'correct_answer': meaning,
                'level': level,
                'options': options
            })
        
        st.session_state.session_words = session_words
        st.session_state.session_results = []
        st.session_state.current_index = 0
    
    # 顯示題目
    idx = st.session_state.current_index
    words = st.session_state.session_words
    
    if idx >= len(words):
        results = st.session_state.session_results
        correct = sum(1 for r in results if r['correct'])
        st.success(f"🏁 完成！正確率: {correct}/{len(results)} ({correct/len(results)*100:.0f}%)")
        
        for r in results:
            icon = "✅" if r['correct'] else "❌"
            st.write(f"{icon} **{r['word']}**: 你答 `{r['your_answer']}`")
            if not r['correct']:
                st.caption(f"   → 正確: {r['correct_meaning']}")
        
        if st.button("🔁 再測一次"):
            st.session_state.session_words = []
            st.rerun()
        return
    
    # 當前題目
    q = words[idx]
    word = q['word']
    
    st.write(f"### 題目 {idx+1} / {len(words)}")
    
    CEFR = {1:'A1',2:'A2',3:'B1',4:'B2',5:'C1'}
    cefr = CEFR.get(q.get('level',1),'A1')
    
    c1, c2, c3 = st.columns([4,1,2])
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
    
    with c3:
        if st.button("❓ 不會", key=f"review_{idx}", type="secondary"):
            # 加入複習清單 (記錄為錯誤)
            result = {
                'correct': False,
                'word': word,
                'correct_meaning': q['correct_answer'],
                'your_answer': '不知道'
            }
            st.session_state.session_results.append(result)
            
            # 記錄到複習清單 (視為錯誤)
            is_correct = False
            if user_id:
                update_progress(user_id, word, q["correct_answer"], is_correct)
            if user_id:
                add_wrong_record(user_id, word, q["correct_answer"], is_correct)
            user_storage.mark_tested(word)
            user_storage.add_wrong_record(word, q['correct_answer'], '不知道')
            
            st.session_state.pending_next = True
            st.warning(f"📚 已加入複習清單")
            st.session_state.current_index += 1
            st.rerun()
    
    # 選項
    st.write("請選擇正確的中文意思：")
    cols = st.columns(2)
    
    for i, option in enumerate(q['options']):
        with cols[i % 2]:
            if st.button(f"{option}", key=f"btn_{idx}_{i}", use_container_width=True):
                is_correct = option == q['correct_answer']
                
                result = {
                    'correct': is_correct,
                    'word': word,
                    'correct_meaning': q['correct_answer'],
                    'your_answer': option
                }
                st.session_state.session_results.append(result)
                
                # 儲存到用戶資料
                if user_id:
                    update_progress(user_id, word, q["correct_answer"], is_correct)
                if user_id:
                    add_wrong_record(user_id, word, q["correct_answer"], is_correct)
                user_storage.mark_tested(word)
                if not is_correct:
                    user_storage.add_wrong_record(word, q['correct_answer'], option)
                
                st.session_state.pending_next = True
                
                if is_correct:
                    st.success(f"✅ 正確！答案是: 「{q['correct_answer']}」")
                else:
                    st.error(f"❌ 錯誤！你選了: 「{option}」")
                    st.info(f"正確答案: 「{q['correct_answer']}」")
    
    # 下一題
    if st.session_state.get('pending_next', False):
        if st.button("下一題 ➡️", key=f"next_{idx}"):
            st.session_state.pending_next = False
            st.session_state.current_index += 1
            st.rerun()

if __name__ == "__main__":
    main()
