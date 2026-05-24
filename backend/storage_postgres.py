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


# ── SRS interval table (streak → days until next review) ─────────────────────
_SRS_INTERVALS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14}
_SRS_MASTERED_STREAK = 5      # streak >= 5 → mastered (30-day interval)
_SRS_MASTERED_INTERVAL = 30
_WEIGHT_CORRECT_DECAY = 0.75  # answer correct → weight * 0.75
_WEIGHT_WRONG_BOOST   = 2.0   # answer wrong   → weight * 2.0
_WEIGHT_MIN = 1.0
_WEIGHT_MAX = 10.0


def _srs_next_review(streak: int) -> datetime:
    days = _SRS_INTERVALS.get(streak, _SRS_MASTERED_INTERVAL if streak >= _SRS_MASTERED_STREAK else 14)
    return datetime.now() + timedelta(days=days)


def update_progress(user_id, word, meaning, correct=True):
    """
    SRS-based progress update.

    Correct answer:
      streak++, weight decays by 25% (min 1.0),
      next_review pushed out by SRS interval.

    Wrong answer:
      streak resets to 0, weight doubles (max 10.0),
      next_review = now (show again in this session / next day).
    """
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id FROM words WHERE word = %s", (word,))
        row = _fetchone_dict(cur)
        if not row:
            return
        word_id = row['id']
        now = datetime.now()
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')

        cur.execute(
            "SELECT id, correct_count, error_count, weight, streak, last_error FROM user_progress WHERE user_id = %s AND word_id = %s",
            (user_id, word_id)
        )
        existing = _fetchone_dict(cur)

        if existing:
            correct_count = existing['correct_count'] + (1 if correct else 0)
            error_count   = existing['error_count']   + (0 if correct else 1)
            old_streak    = existing.get('streak') or 0
            old_weight    = float(existing.get('weight') or 1.0)

            if correct:
                new_streak = old_streak + 1
                new_weight = max(_WEIGHT_MIN, old_weight * _WEIGHT_CORRECT_DECAY)
            else:
                new_streak = 0
                new_weight = min(_WEIGHT_MAX, old_weight * _WEIGHT_WRONG_BOOST)

            next_review = _srs_next_review(new_streak)

            cur.execute("""
                UPDATE user_progress
                SET correct_count=%s, error_count=%s, weight=%s, streak=%s,
                    last_reviewed=%s, last_error=%s, next_review=%s
                WHERE user_id=%s AND word_id=%s
            """, (
                correct_count, error_count, round(new_weight, 4), new_streak,
                now_str,
                now_str if not correct else existing['last_error'],
                next_review,
                user_id, word_id
            ))
        else:
            # First time seeing this word
            new_streak  = 1 if correct else 0
            new_weight  = _WEIGHT_MIN if correct else _WEIGHT_WRONG_BOOST
            next_review = _srs_next_review(new_streak)
            cur.execute("""
                INSERT INTO user_progress
                  (user_id, word_id, correct_count, error_count, weight, streak,
                   last_reviewed, last_error, next_review)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                user_id, word_id,
                1 if correct else 0, 0 if correct else 1,
                round(new_weight, 4), new_streak,
                now_str, now_str if not correct else None,
                next_review
            ))

        if not correct:
            cur.execute(
                "INSERT INTO error_details (user_id, word_id, your_answer, created_at) VALUES (%s,%s,%s,%s)",
                (user_id, word_id, 'incorrect', now_str)
            )


def get_weak_words(user_id, top_n=20):
    """
    Return words due for review (next_review <= NOW), excluding mastered words.
    Ordered by weight DESC (most problematic first).
    """
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT w.word, w.meaning, w.cefr, up.error_count, up.weight, up.streak
            FROM user_progress up
            JOIN words w ON up.word_id = w.id
            WHERE up.user_id = %s
              AND up.error_count > 0
              AND (up.next_review IS NULL OR up.next_review <= NOW())
              AND up.streak < %s
            ORDER BY up.weight DESC
            LIMIT %s
        """, (user_id, _SRS_MASTERED_STREAK, top_n))
        return [(row['word'], {'meaning': row['meaning'], 'correct_count': row['error_count']}) for row in cur.fetchall()]


def get_quiz_words(user_id, count=10, min_level=1, max_level=6, mode="mixed"):
    """
    Select words for a quiz session using SRS logic.

    Modes:
      "weak"  – only due-for-review words (next_review <= NOW, streak < mastered)
      "new"   – only unseen words (not in user_progress)
      "mixed" – 70% due-for-review + 30% new (falls back if either pool is small)

    Returns list of word dicts: {word, meaning, cefr, difficulty, example_sentence, image_path}
    """
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        base_filter = "w.difficulty BETWEEN %s AND %s AND w.meaning IS NOT NULL AND w.meaning != ''"

        def fetch_due(limit):
            cur.execute(f"""
                SELECT w.word, w.meaning, w.cefr, w.difficulty, w.example_sentence, w.image_path,
                       up.weight, up.streak
                FROM user_progress up
                JOIN words w ON up.word_id = w.id
                WHERE up.user_id = %s
                  AND {base_filter}
                  AND (up.next_review IS NULL OR up.next_review <= NOW())
                  AND up.streak < %s
                ORDER BY up.weight DESC
                LIMIT %s
            """, (user_id, min_level, max_level, _SRS_MASTERED_STREAK, limit))
            return [dict(r) for r in cur.fetchall()]

        def fetch_new(limit):
            cur.execute(f"""
                SELECT w.word, w.meaning, w.cefr, w.difficulty, w.example_sentence, w.image_path
                FROM words w
                WHERE {base_filter}
                  AND NOT EXISTS (
                      SELECT 1 FROM user_progress up
                      WHERE up.user_id = %s AND up.word_id = w.id
                  )
                ORDER BY RANDOM()
                LIMIT %s
            """, (min_level, max_level, user_id, limit))
            return [dict(r) for r in cur.fetchall()]

        if mode == "weak":
            words = fetch_due(count)
            if len(words) < count:
                words += fetch_new(count - len(words))

        elif mode == "new":
            words = fetch_new(count)
            if len(words) < count:
                words += fetch_due(count - len(words))

        else:  # mixed: 70% due + 30% new
            due_count = max(1, int(count * 0.7))
            new_count = count - due_count
            due_words = fetch_due(due_count)
            new_words = fetch_new(new_count)
            # If one pool is small, fill from the other
            if len(due_words) < due_count:
                new_words += fetch_new(due_count - len(due_words) + new_count)
                new_words = new_words[:count - len(due_words)]
            elif len(new_words) < new_count:
                due_words += fetch_due(new_count - len(new_words) + due_count)
                due_words = due_words[:count - len(new_words)]
            words = due_words + new_words

        import random
        random.shuffle(words)
        return words[:count]


def get_mastery_stats(user_id):
    """Return counts: new / learning / review_due / mastered per CEFR level."""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                w.cefr,
                COUNT(*) FILTER (WHERE up.id IS NULL)                                AS new_words,
                COUNT(*) FILTER (WHERE up.streak < %s AND up.next_review > NOW())    AS learning,
                COUNT(*) FILTER (WHERE up.streak < %s AND (up.next_review IS NULL OR up.next_review <= NOW())) AS due,
                COUNT(*) FILTER (WHERE up.streak >= %s)                              AS mastered
            FROM words w
            LEFT JOIN user_progress up ON up.word_id = w.id AND up.user_id = %s
            GROUP BY w.cefr ORDER BY w.cefr
        """, (_SRS_MASTERED_STREAK, _SRS_MASTERED_STREAK, _SRS_MASTERED_STREAK, user_id))
        return [dict(r) for r in cur.fetchall()]


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
