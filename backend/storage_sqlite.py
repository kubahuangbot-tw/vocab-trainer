"""
SQLite 資料庫儲存模組 - 支援多用戶 + 時間權重
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager

# 資料目錄 — 指向專案根目錄的 data/ (與舊版共用 DB)
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "vocab.db"


@contextmanager
def get_db():
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """初始化資料庫結構"""
    with get_db() as conn:
        cursor = conn.cursor()

        # ========== 單字庫 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                meaning TEXT,
                cefr TEXT,
                example_sentence TEXT,
                phonetic TEXT,
                word_type TEXT,
                difficulty INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ========== 用戶 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT,
                display_name TEXT,
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        # 若舊版 DB 沒有 is_admin 欄位，補上
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        except Exception:
            pass

        # ========== 用戶學習進度 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                word_id INTEGER NOT NULL,
                correct_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                weight REAL DEFAULT 1.0,
                last_reviewed TIMESTAMP,
                last_error TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (word_id) REFERENCES words(id),
                UNIQUE(user_id, word_id)
            )
        """)

        # ========== 錯誤記錄 (摘要) ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wrong_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                word_id INTEGER NOT NULL,
                your_answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (word_id) REFERENCES words(id)
            )
        """)

        # ========== 錯誤詳細日誌 (每次錯誤都記錄) ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                word_id INTEGER NOT NULL,
                your_answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (word_id) REFERENCES words(id)
            )
        """)

        # ========== 測試歷史 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                test_type TEXT,
                total_questions INTEGER,
                correct_count INTEGER,
                score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # ========== 單字集 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_by INTEGER,
                is_public INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # ========== 單字集成員 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_set_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_set_id INTEGER NOT NULL,
                word_id INTEGER NOT NULL,
                FOREIGN KEY (word_set_id) REFERENCES word_sets(id),
                FOREIGN KEY (word_id) REFERENCES words(id),
                UNIQUE(word_set_id, word_id)
            )
        """)

        # ========== 索引 ==========
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_words_word ON words(word)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_words_cefr ON words(cefr)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_progress_user ON user_progress(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_details_user ON error_details(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_details_time ON error_details(created_at)")

        conn.commit()


def import_words_from_json(json_path):
    """從 JSON 匯入單字庫"""
    with open(json_path, 'r', encoding='utf-8') as f:
        words_data = json.load(f)

    with get_db() as conn:
        cursor = conn.cursor()
        for word, info in words_data.items():
            # 處理 level -> cefr 映射
            cefr = ""
            level = info.get('level', 0)
            if level == 1:
                cefr = "a1"
            elif level == 2:
                cefr = "a2"
            elif level == 3:
                cefr = "b1"
            elif level == 4:
                cefr = "b2"
            elif level == 5:
                cefr = "c1"
            elif level >= 6:
                cefr = "c2"

            cursor.execute("""
                INSERT OR REPLACE INTO words
                (word, meaning, cefr, example_sentence, phonetic, word_type, difficulty, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                word,
                info.get('meaning', ''),
                cefr,
                info.get('example_sentence', ''),
                info.get('phonetic', ''),
                info.get('type', ''),
                level
            ))
        conn.commit()
    return len(words_data)


def create_user(username, password, display_name=None):
    """建立用戶"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, display_name)
            VALUES (?, ?, ?)
        """, (username, password, display_name or username))
        conn.commit()
        return cursor.lastrowid


def get_user(username):
    """取得用戶"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_users():
    """列出所有用戶"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, display_name, is_admin, created_at FROM users ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]


def get_user_by_id(user_id):
    """依 ID 取得用戶"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_progress(user_id):
    """取得用戶學習進度"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT w.word, w.meaning, w.cefr, up.correct_count, up.error_count,
                   up.weight, up.last_reviewed, up.last_error
            FROM user_progress up
            JOIN words w ON up.word_id = w.id
            WHERE up.user_id = ?
        """, (user_id,))
        return {row['word']: dict(row) for row in cursor.fetchall()}


def calculate_time_weight(last_error_time):
    """根據錯誤時間計算權重

    邏輯:
    - 7天內錯誤: 權重 2.0 (高)
    - 7-14天: 權重 1.5 (中)
    - 14-30天: 權重 1.0 (低)
    - 30天以上: 權重 0.5 (極低)
    """
    if not last_error_time:
        return 1.0

    try:
        error_date = datetime.strptime(last_error_time, '%Y-%m-%d %H:%M:%S')
    except:
        return 1.0

    days_old = (datetime.now() - error_date).days

    if days_old <= 7:
        return 2.0
    elif days_old <= 14:
        return 1.5
    elif days_old <= 30:
        return 1.0
    else:
        return 0.5


def update_progress(user_id, word, meaning, correct=True):
    """更新單字學習進度 (含時間權重)"""
    with get_db() as conn:
        cursor = conn.cursor()

        # 取得 word_id
        cursor.execute("SELECT id FROM words WHERE word = ?", (word,))
        row = cursor.fetchone()
        if not row:
            return
        word_id = row['id']

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 檢查是否存在
        cursor.execute("""
            SELECT id, correct_count, error_count, weight, last_error
            FROM user_progress WHERE user_id = ? AND word_id = ?
        """, (user_id, word_id))
        row = cursor.fetchone()

        if row:
            correct_count = row['correct_count'] + (1 if correct else 0)
            error_count = row['error_count'] + (0 if correct else 1)

            # 如果錯誤,更新 last_error 並計算新權重
            new_weight = row['weight']
            if not correct:
                # 計算時間權重
                time_weight = calculate_time_weight(row['last_error'])
                # 新權重 = 基礎權重 * 時間權重
                new_weight = max(1, row['weight'] * time_weight)

            cursor.execute("""
                UPDATE user_progress
                SET correct_count = ?, error_count = ?, weight = ?,
                    last_reviewed = ?, last_error = ?
                WHERE user_id = ? AND word_id = ?
            """, (
                correct_count, error_count, new_weight, now,
                now if not correct else row['last_error'],
                user_id, word_id
            ))

            # 記錄錯誤詳細日誌
            if not correct:
                cursor.execute("""
                    INSERT INTO error_details (user_id, word_id, your_answer, created_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, word_id, 'incorrect', now))
        else:
            weight = 1.0 if correct else 3.0
            cursor.execute("""
                INSERT INTO user_progress
                (user_id, word_id, correct_count, error_count, weight, last_reviewed, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, word_id,
                1 if correct else 0,
                0 if correct else 1,
                weight,
                now,
                now if not correct else None
            ))

            # 記錄錯誤詳細日誌
            if not correct:
                cursor.execute("""
                    INSERT INTO error_details (user_id, word_id, your_answer, created_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, word_id, 'incorrect', now))

        conn.commit()


def get_all_words(cefr=None, limit=None):
    """取得所有單字"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM words"
        params = []
        if cefr:
            query += " WHERE cefr = ?"
            params.append(cefr)
        query += " ORDER BY RANDOM()"
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_words_by_ids(word_ids):
    """依 ID 取得單字"""
    if not word_ids:
        return []
    with get_db() as conn:
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(word_ids))
        cursor.execute(f"SELECT * FROM words WHERE id IN ({placeholders})", word_ids)
        return [dict(row) for row in cursor.fetchall()]


def get_weak_words(user_id, top_n=20):
    """取得最弱的單字 (考慮時間權重)
    
    回傳格式: [(word, {data}), ...] - 為了相容 trainer.py
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 取得每個單字最近的錯誤時間
        cursor.execute("""
            SELECT w.word, w.meaning, w.cefr, up.error_count, up.weight, up.last_error
            FROM user_progress up
            JOIN words w ON up.word_id = w.id
            WHERE up.user_id = ? AND up.error_count > 0
            ORDER BY up.weight DESC, up.last_error DESC
            LIMIT ?
        """, (user_id, top_n))
        
        # 回傳舊格式 (tuple list) 相容 trainer.py: (word, {meaning: ...})
        results = []
        for row in cursor.fetchall():
            results.append((row['word'], {'meaning': row['meaning'], 'correct_count': row['error_count']}))
        
        return results


def add_wrong_record(user_id, word, meaning, your_answer):
    """記錄錯誤 (摘要)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM words WHERE word = ?", (word,))
        row = cursor.fetchone()
        if row:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO wrong_records (user_id, word_id, your_answer, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, row['id'], your_answer, now))
            conn.commit()


def get_error_history(user_id, word_id=None, days=30):
    """取得錯誤歷史 (可限定天數)"""
    with get_db() as conn:
        cursor = conn.cursor()

        if word_id:
            cursor.execute("""
                SELECT ed.*, w.word, w.meaning
                FROM error_details ed
                JOIN words w ON ed.word_id = w.id
                WHERE ed.user_id = ? AND ed.word_id = ?
                ORDER BY ed.created_at DESC
            """, (user_id, word_id))
        else:
            # ,取得最近 N 天的錯誤
            cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                SELECT ed.*, w.word, w.meaning
                FROM error_details ed
                JOIN words w ON ed.word_id = w.id
                WHERE ed.user_id = ? AND ed.created_at > ?
                ORDER BY ed.created_at DESC
            """, (user_id, cutoff))

        return [dict(row) for row in cursor.fetchall()]


def get_stats(user_id):
    """取得學習統計"""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT SUM(correct_count) as total_correct, SUM(error_count) as total_errors
            FROM user_progress WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()

        total_correct = row['total_correct'] or 0
        total_errors = row['total_errors'] or 0

        # 計算近期錯誤趨勢
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM error_details
            WHERE user_id = ? AND created_at > datetime('now', '-7 days')
        """, (user_id,))
        recent_errors = cursor.fetchone()['count']

        return {
            'total_correct': total_correct,
            'total_errors': total_errors,
            'recent_errors_7d': recent_errors,
            'accuracy': total_correct / (total_correct + total_errors) * 100 if (total_correct + total_errors) > 0 else 0
        }


def get_word_count():
    """取得單字數量"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM words")
        return cursor.fetchone()['count']


def export_words_to_json(output_path):
    """匯出單字庫為 JSON"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM words")

        words_dict = {}
        for row in cursor.fetchall():
            words_dict[row['word']] = {
                'meaning': row['meaning'],
                'level': row['difficulty'],
                'type': row['word_type'],
                'cefr': row['cefr'],
                'example_sentence': row['example_sentence'],
                'phonetic': row['phonetic']
            }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(words_dict, f, ensure_ascii=False, indent=2)

        return len(words_dict)


# ========== 單字集管理 ==========
def create_word_set(name, description, user_id, is_public=False):
    """建立單字集"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO word_sets (name, description, created_by, is_public)
            VALUES (?, ?, ?, ?)
        """, (name, description, user_id, 1 if is_public else 0))
        conn.commit()
        return cursor.lastrowid


def add_word_to_set(word_set_id, word_id):
    """新增單字到單字集"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO word_set_members (word_set_id, word_id)
            VALUES (?, ?)
        """, (word_set_id, word_id))
        conn.commit()


def get_word_set_words(word_set_id):
    """取得單字集內的單字"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT w.* FROM words w
            JOIN word_set_members wsm ON w.id = wsm.word_id
            WHERE wsm.word_set_id = ?
        """, (word_set_id,))
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    # 初始化
    init_db()
    print(f"資料庫建立完成: {DB_PATH}")
    print(f"單字數量: {get_word_count()}")

# ========== 新增單字 + 自動翻譯 ==========
def translate_word(text):
    """使用 Google Translate API 翻譯"""
    import urllib.request
    import urllib.parse
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-TW&dt=t&q={urllib.parse.quote(text[:100])}"
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        if data[0] and data[0][0]:
            return data[0][0][0][:100]
    except Exception as e:
        print(f"翻譯錯誤: {e}")
    return ''


def add_word_auto(word, user_id=None):
    """自動新增單字 (含翻譯)
    
    邏輯:
    1. 檢查 DB 是否有這個單字
    2. 有 → 加入用戶的複習清單
    3. 沒有 → 用 Google 翻譯查詢，加入 DB

    Args:
        word: 英文單字
        user_id: 新增者 ID (可選)

    Returns:
        dict: {'success': bool, 'word': str, 'meaning': str, 'message': str, 'action': str}
    """
    word = word.strip().lower()

    if not word:
        return {'success': False, 'message': '單字不能為空', 'action': 'error'}

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 檢查是否已存在
        cursor.execute("SELECT id, meaning FROM words WHERE word = ?", (word,))
        existing = cursor.fetchone()

        if existing:
            # 單字已存在，加入用戶複習清單
            word_id = existing['id']
            existing_meaning = existing['meaning']
            
            if user_id:
                # 檢查用戶是否已有這個單字的學習紀錄
                cursor.execute("""
                    SELECT id FROM user_progress 
                    WHERE user_id = ? AND word_id = ?
                """, (user_id, word_id))
                
                if not cursor.fetchone():
                    # 沒有紀錄，加入複習清單
                    cursor.execute("""
                        INSERT INTO user_progress 
                        (user_id, word_id, correct_count, error_count, weight, last_reviewed, last_error)
                        VALUES (?, ?, 0, 1, 2.0, ?, ?)
                    """, (user_id, word_id, now, now))
                    
                    conn.commit()
                    return {
                        'success': True,
                        'word': word,
                        'meaning': existing_meaning,
                        'message': f'單字已存在，已加入你的複習清單！',
                        'action': 'added_to_review'
                    }
                else:
                    return {
                        'success': True,
                        'word': word,
                        'meaning': existing_meaning,
                        'message': '單字已存在，已在你的複習清單中',
                        'action': 'already_in_review'
                    }
            
            return {
                'success': True,
                'word': word,
                'meaning': existing_meaning,
                'message': '單字已存在',
                'action': 'exists'
            }

        # 單字不存在，翻譯並新增
        meaning = translate_word(word)

        if not meaning:
            return {'success': False, 'message': '翻譯失敗，請稍後再試', 'action': 'error'}

        # 估算難度 (根據單字長度)
        difficulty = 1 if len(word) <= 4 else (2 if len(word) <= 6 else (3 if len(word) <= 8 else 4))
        
        # 儲存到資料庫
        cursor.execute("""
            INSERT INTO words (word, meaning, difficulty, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (word, meaning, difficulty))
        
        word_id = cursor.lastrowid
        
        # 如果有用戶 ID，加入複習清單
        if user_id:
            cursor.execute("""
                INSERT INTO user_progress 
                (user_id, word_id, correct_count, error_count, weight, last_reviewed, last_error)
                VALUES (?, ?, 0, 1, 2.0, ?, ?)
            """, (user_id, word_id, now, now))
        
        conn.commit()
        
        return {
            'success': True,
            'word': word,
            'meaning': meaning,
            'message': f'✅ 新增成功！難度: {["A1","A2","B1","B2","C1"][difficulty-1]}',
            'action': 'created'
        }


# ========== 用戶偏好設定 ==========
def save_user_preferences(user_id, preferences):
    """儲存用戶偏好設定"""
    import json
    create_preferences_table()
    with get_db() as conn:
        cursor = conn.cursor()
        prefs_json = json.dumps(preferences, ensure_ascii=False)
        cursor.execute("""
            INSERT OR REPLACE INTO user_preferences (user_id, preferences, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (user_id, prefs_json))
        conn.commit()


def get_user_preferences(user_id):
    """取得用戶偏好設定"""
    import json
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT preferences FROM user_preferences 
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row and row['preferences']:
            return json.loads(row['preferences'])
    return None


def create_preferences_table():
    """建立偏好設定表"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                preferences TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
