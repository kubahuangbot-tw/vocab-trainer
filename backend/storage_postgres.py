"""
PostgreSQL 資料庫儲存模組 - 相容 storage_sqlite.py API
"""
import json
import os
from datetime import datetime, timedelta
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
import psycopg2.pool

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres.wzxqbvrtrjgndfhxxyjw:LFHGDXKg22rnSDPO@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"
)

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        _pool = psycopg2.pool.ThreadedConnectionPool(2, 10, DATABASE_URL)
    return _pool


@contextmanager
def get_db():
    pool = _get_pool()
    conn = pool.getconn()
    conn.autocommit = False
    try:
        yield conn
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        pool.putconn(conn, close=True)
        conn = None
        raise
    finally:
        if conn is not None:
            pool.putconn(conn)


def _fetchone_dict(cursor):
    row = cursor.fetchone()
    return dict(row) if row else None


def init_db():
    """No-op: schema already created in Supabase"""
    pass


# ========== 用戶 ==========

def create_user(username, password, display_name=None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "INSERT INTO users (username, password, display_name) VALUES (%s, %s, %s) RETURNING id",
            (username, password, display_name or username)
        )
        return cur.fetchone()["id"]


def get_user(username):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        return _fetchone_dict(cur)


def list_users():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, username, display_name, is_admin, created_at FROM users ORDER BY id")
        return [dict(r) for r in cur.fetchall()]


def get_user_by_id(user_id):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return _fetchone_dict(cur)


# ========== 單字 ==========

def get_word_count():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM words")
        return cur.fetchone()[0]


def get_all_words(cefr=None, limit=None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if cefr:
            cur.execute("SELECT * FROM words WHERE cefr = %s ORDER BY RANDOM()" + (f" LIMIT {int(limit)}" if limit else ""), (cefr,))
        else:
            cur.execute("SELECT * FROM words ORDER BY RANDOM()" + (f" LIMIT {int(limit)}" if limit else ""))
        return [dict(r) for r in cur.fetchall()]


def get_words_by_ids(word_ids):
    if not word_ids:
        return []
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM words WHERE id = ANY(%s)", (list(word_ids),))
        return [dict(r) for r in cur.fetchall()]


def add_word_auto(word, user_id=None):
    word = word.strip().lower()
    if not word:
        return {'success': False, 'message': '單字不能為空', 'action': 'error'}

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT id, meaning FROM words WHERE word = %s", (word,))
        existing = _fetchone_dict(cur)

        if existing:
            word_id = existing["id"]
            existing_meaning = existing["meaning"]

            if user_id:
                cur.execute(
                    "SELECT id FROM user_progress WHERE user_id = %s AND word_id = %s",
                    (user_id, word_id)
                )
                if not cur.fetchone():
                    cur.execute(
                        "INSERT INTO user_progress (user_id, word_id, correct_count, error_count, weight, last_reviewed, last_error) VALUES (%s,%s,0,1,2.0,%s,%s)",
                        (user_id, word_id, now, now)
                    )
                    return {'success': True, 'word': word, 'meaning': existing_meaning, 'message': '單字已存在，已加入你的複習清單！', 'action': 'added_to_review'}
                else:
                    return {'success': True, 'word': word, 'meaning': existing_meaning, 'message': '單字已存在，已在你的複習清單中', 'action': 'already_in_review'}
            return {'success': True, 'word': word, 'meaning': existing_meaning, 'message': '單字已存在', 'action': 'exists'}

        meaning = translate_word(word)
        if not meaning:
            return {'success': False, 'message': '翻譯失敗，請稍後再試', 'action': 'error'}

        difficulty = 1 if len(word) <= 4 else (2 if len(word) <= 6 else (3 if len(word) <= 8 else 4))

        cur.execute(
            "INSERT INTO words (word, meaning, difficulty) VALUES (%s, %s, %s) RETURNING id",
            (word, meaning, difficulty)
        )
        word_id = cur.fetchone()["id"]

        if user_id:
            cur.execute(
                "INSERT INTO user_progress (user_id, word_id, correct_count, error_count, weight, last_reviewed, last_error) VALUES (%s,%s,0,1,2.0,%s,%s)",
                (user_id, word_id, now, now)
            )

        return {
            'success': True, 'word': word, 'meaning': meaning,
            'message': f'✅ 新增成功！難度: {["A1","A2","B1","B2","C1"][difficulty-1]}',
            'action': 'created'
        }


def translate_word(text):
    import urllib.request, urllib.parse
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-TW&dt=t&q={urllib.parse.quote(text[:100])}"
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        if data[0] and data[0][0]:
            return data[0][0][0][:100]
    except Exception as e:
        print(f"翻譯錯誤: {e}")
    return ''


# ========== 學習進度 ==========

def get_user_progress(user_id):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT w.word, w.meaning, w.cefr, up.correct_count, up.error_count,
                   up.weight, up.last_reviewed, up.last_error
            FROM user_progress up
            JOIN words w ON up.word_id = w.id
            WHERE up.user_id = %s
        """, (user_id,))
        return {row['word']: dict(row) for row in cur.fetchall()}


def calculate_time_weight(last_error_time):
    if not last_error_time:
        return 1.0
    try:
        if isinstance(last_error_time, str):
            error_date = datetime.strptime(last_error_time, '%Y-%m-%d %H:%M:%S')
        else:
            error_date = last_error_time
    except Exception:
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
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id FROM words WHERE word = %s", (word,))
        row = _fetchone_dict(cur)
        if not row:
            return
        word_id = row['id']
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cur.execute(
            "SELECT id, correct_count, error_count, weight, last_error FROM user_progress WHERE user_id = %s AND word_id = %s",
            (user_id, word_id)
        )
        existing = _fetchone_dict(cur)

        if existing:
            correct_count = existing['correct_count'] + (1 if correct else 0)
            error_count = existing['error_count'] + (0 if correct else 1)
            new_weight = existing['weight']
            if not correct:
                time_weight = calculate_time_weight(existing['last_error'])
                new_weight = max(1, existing['weight'] * time_weight)
            cur.execute("""
                UPDATE user_progress
                SET correct_count=%s, error_count=%s, weight=%s, last_reviewed=%s, last_error=%s
                WHERE user_id=%s AND word_id=%s
            """, (
                correct_count, error_count, new_weight, now,
                now if not correct else existing['last_error'],
                user_id, word_id
            ))
            if not correct:
                cur.execute(
                    "INSERT INTO error_details (user_id, word_id, your_answer, created_at) VALUES (%s,%s,%s,%s)",
                    (user_id, word_id, 'incorrect', now)
                )
        else:
            weight = 1.0 if correct else 3.0
            cur.execute("""
                INSERT INTO user_progress (user_id, word_id, correct_count, error_count, weight, last_reviewed, last_error)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (user_id, word_id, 1 if correct else 0, 0 if correct else 1, weight, now, now if not correct else None))
            if not correct:
                cur.execute(
                    "INSERT INTO error_details (user_id, word_id, your_answer, created_at) VALUES (%s,%s,%s,%s)",
                    (user_id, word_id, 'incorrect', now)
                )


def get_weak_words(user_id, top_n=20):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT w.word, w.meaning, w.cefr, up.error_count, up.weight, up.last_error
            FROM user_progress up
            JOIN words w ON up.word_id = w.id
            WHERE up.user_id = %s AND up.error_count > 0
            ORDER BY up.weight DESC, up.last_error DESC
            LIMIT %s
        """, (user_id, top_n))
        return [(row['word'], {'meaning': row['meaning'], 'correct_count': row['error_count']}) for row in cur.fetchall()]


def add_wrong_record(user_id, word, meaning, your_answer):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id FROM words WHERE word = %s", (word,))
        row = _fetchone_dict(cur)
        if row:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute(
                "INSERT INTO wrong_records (user_id, word_id, your_answer, created_at) VALUES (%s,%s,%s,%s)",
                (user_id, row['id'], your_answer, now)
            )


def get_error_history(user_id, word_id=None, days=30):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if word_id:
            cur.execute("""
                SELECT ed.*, w.word, w.meaning FROM error_details ed
                JOIN words w ON ed.word_id = w.id
                WHERE ed.user_id = %s AND ed.word_id = %s
                ORDER BY ed.created_at DESC
            """, (user_id, word_id))
        else:
            cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            cur.execute("""
                SELECT ed.*, w.word, w.meaning FROM error_details ed
                JOIN words w ON ed.word_id = w.id
                WHERE ed.user_id = %s AND ed.created_at > %s
                ORDER BY ed.created_at DESC
            """, (user_id, cutoff))
        return [dict(r) for r in cur.fetchall()]


def get_stats(user_id):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT SUM(correct_count) as total_correct, SUM(error_count) as total_errors FROM user_progress WHERE user_id = %s",
            (user_id,)
        )
        row = _fetchone_dict(cur)
        total_correct = row['total_correct'] or 0
        total_errors = row['total_errors'] or 0

        cur.execute(
            "SELECT COUNT(*) as count FROM error_details WHERE user_id = %s AND created_at > NOW() - INTERVAL '7 days'",
            (user_id,)
        )
        recent_errors = cur.fetchone()['count']

        return {
            'total_correct': total_correct,
            'total_errors': total_errors,
            'recent_errors_7d': recent_errors,
            'accuracy': total_correct / (total_correct + total_errors) * 100 if (total_correct + total_errors) > 0 else 0
        }


# ========== 用戶偏好 ==========

def save_user_preferences(user_id, preferences):
    with get_db() as conn:
        cur = conn.cursor()
        prefs_json = json.dumps(preferences, ensure_ascii=False)
        cur.execute("""
            INSERT INTO user_preferences (user_id, preferences, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET preferences = EXCLUDED.preferences, updated_at = CURRENT_TIMESTAMP
        """, (user_id, prefs_json))


def get_user_preferences(user_id):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT preferences FROM user_preferences WHERE user_id = %s", (user_id,))
        row = _fetchone_dict(cur)
        if row and row['preferences']:
            return json.loads(row['preferences'])
    return None


def create_preferences_table():
    pass  # Already created in Supabase


# ========== 單字集 ==========

def create_word_set(name, description, user_id, is_public=False):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "INSERT INTO word_sets (name, description, created_by, is_public) VALUES (%s,%s,%s,%s) RETURNING id",
            (name, description, user_id, 1 if is_public else 0)
        )
        return cur.fetchone()['id']


def add_word_to_set(word_set_id, word_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO word_set_members (word_set_id, word_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
            (word_set_id, word_id)
        )


def get_word_set_words(word_set_id):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT w.* FROM words w
            JOIN word_set_members wsm ON w.id = wsm.word_id
            WHERE wsm.word_set_id = %s
        """, (word_set_id,))
        return [dict(r) for r in cur.fetchall()]


def export_words_to_json(output_path):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM words")
        words_dict = {}
        for row in cur.fetchall():
            words_dict[row['word']] = {
                'meaning': row['meaning'], 'level': row['difficulty'],
                'type': row['word_type'], 'cefr': row['cefr'],
                'example_sentence': row['example_sentence'], 'phonetic': row['phonetic']
            }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(words_dict, f, ensure_ascii=False, indent=2)
        return len(words_dict)


def import_words_from_json(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        words_data = json.load(f)
    cefr_map = {1: 'a1', 2: 'a2', 3: 'b1', 4: 'b2', 5: 'c1'}
    with get_db() as conn:
        cur = conn.cursor()
        for word, info in words_data.items():
            level = info.get('level', 0)
            cur.execute("""
                INSERT INTO words (word, meaning, cefr, example_sentence, phonetic, word_type, difficulty)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (word) DO NOTHING
            """, (word, info.get('meaning',''), cefr_map.get(level,''), info.get('example_sentence',''),
                  info.get('phonetic',''), info.get('type',''), level))
    return len(words_data)
