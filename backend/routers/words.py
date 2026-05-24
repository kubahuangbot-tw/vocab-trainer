from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import storage_postgres as db
from auth import get_current_user
import psycopg2.extras

router = APIRouter(prefix="/api/words", tags=["words"])


class AddWordRequest(BaseModel):
    word: str

class SuggestRequest(BaseModel):
    word: str
    suggested_meaning: str

class SuggestRemoveRequest(BaseModel):
    word: str

class SuggestSentenceRequest(BaseModel):
    word: str
    suggested_sentence: str


@router.post("/add")
def add_word(body: AddWordRequest, current_user: dict = Depends(get_current_user)):
    user = db.get_user(current_user["username"])
    user_id = user["id"] if user else None
    result = db.add_word_auto(body.word.strip(), user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/recent")
def recent_words(limit: int = 10, current_user: dict = Depends(get_current_user)):
    with db.get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT word, meaning, cefr, created_at FROM words ORDER BY id DESC LIMIT %s",
            (limit,)
        )
        return [dict(row) for row in cur.fetchall()]


@router.get("/count")
def word_count(current_user: dict = Depends(get_current_user)):
    return {"count": db.get_word_count()}


@router.post("/suggest")
def suggest_meaning(body: SuggestRequest, current_user: dict = Depends(get_current_user)):
    """用戶建議更好的定義"""
    suggestion = body.suggested_meaning.strip()
    if not suggestion:
        raise HTTPException(status_code=400, detail="建議內容不能為空")
    with db.get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE words SET suggested_meaning=%s WHERE word=%s",
            (suggestion, body.word)
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="找不到該單字")
    return {"ok": True, "word": body.word, "suggested_meaning": suggestion}


@router.post("/suggest-remove")
def suggest_remove(body: SuggestRemoveRequest, current_user: dict = Depends(get_current_user)):
    """用戶建議移除某個單字題目"""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="無法識別用戶")
    with db.get_db() as conn:
        cur = conn.cursor()
        # Check word exists
        cur.execute("SELECT id FROM words WHERE word=%s", (body.word,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="找不到該單字")
        # Insert vote (ignore if already voted)
        cur.execute(
            "INSERT INTO word_removal_votes (user_id, word) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user_id, body.word)
        )
        if cur.rowcount == 0:
            return {"ok": True, "already_voted": True, "word": body.word}
        # Increment count
        cur.execute(
            "UPDATE words SET removal_vote_count = removal_vote_count + 1 WHERE word=%s RETURNING removal_vote_count",
            (body.word,)
        )
        new_count = cur.fetchone()[0]
    return {"ok": True, "word": body.word, "removal_vote_count": new_count}


@router.post("/suggest-sentence")
def suggest_sentence(body: SuggestSentenceRequest, current_user: dict = Depends(get_current_user)):
    """用戶建議更好的例句"""
    sentence = body.suggested_sentence.strip()
    if not sentence:
        raise HTTPException(status_code=400, detail="例句不能為空")
    with db.get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE words SET suggested_sentence=%s WHERE word=%s", (sentence, body.word))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="找不到該單字")
    return {"ok": True, "word": body.word}


@router.post("/vote-image-bad")
def vote_image_bad(body: SuggestRemoveRequest, current_user: dict = Depends(get_current_user)):
    """用戶投票圖片不符合"""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="無法識別用戶")
    with db.get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM words WHERE word=%s", (body.word,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="找不到該單字")
        cur.execute(
            "INSERT INTO word_image_bad_votes (user_id, word) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user_id, body.word)
        )
        if cur.rowcount == 0:
            return {"ok": True, "already_voted": True}
        cur.execute(
            "UPDATE words SET image_bad_count = image_bad_count + 1 WHERE word=%s RETURNING image_bad_count",
            (body.word,)
        )
        new_count = cur.fetchone()[0]
    return {"ok": True, "word": body.word, "image_bad_count": new_count}


@router.get("/pending-feedback")
def pending_feedback(current_user: dict = Depends(get_current_user)):
    """取得所有待 review 的 user feedback（Admin）"""
    user = db.get_user(current_user["username"])
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="需要管理員權限")
    with db.get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, word, meaning, cefr,
                   suggested_meaning, suggested_sentence,
                   removal_vote_count, image_bad_count,
                   example_sentence, image_path
            FROM words
            WHERE suggested_meaning IS NOT NULL
               OR suggested_sentence IS NOT NULL
               OR removal_vote_count > 0
               OR image_bad_count > 0
            ORDER BY (removal_vote_count + image_bad_count) DESC, id
        """)
        rows = [dict(r) for r in cur.fetchall()]
    return {
        "total": len(rows),
        "removal": [r for r in rows if r["removal_vote_count"] > 0],
        "image_bad": [r for r in rows if r["image_bad_count"] > 0],
        "suggested_meaning": [r for r in rows if r["suggested_meaning"]],
        "suggested_sentence": [r for r in rows if r["suggested_sentence"]],
    }


@router.get("/removal-candidates")
def removal_candidates(min_votes: int = 1, current_user: dict = Depends(get_current_user)):
    """取得被投票移除的單字清單（Admin）"""
    user = db.get_user(current_user["username"])
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="需要管理員權限")
    with db.get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, word, meaning, cefr, removal_vote_count
            FROM words
            WHERE removal_vote_count >= %s
            ORDER BY removal_vote_count DESC
        """, (min_votes,))
        return [dict(row) for row in cur.fetchall()]


@router.get("/search")
def search_words(q: str = "", limit: int = 20, current_user: dict = Depends(get_current_user)):
    """搜尋單字（Admin 用）"""
    with db.get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, word, meaning, cefr, suggested_meaning FROM words WHERE word LIKE %s LIMIT %s",
            (f"%{q}%", limit)
        )
        return [dict(row) for row in cur.fetchall()]


@router.get("/export")
def export_all_words(current_user: dict = Depends(get_current_user)):
    """匯出所有單字完整資料（Admin）"""
    user = db.get_user(current_user["username"])
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="需要管理員權限")
    with db.get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, word, meaning, cefr, example_sentence, suggested_meaning
            FROM words ORDER BY id
        """)
        return [dict(row) for row in cur.fetchall()]


@router.post("/batch-update")
def batch_update_words(body: List[Dict[str, Any]] = Body(...), current_user: dict = Depends(get_current_user)):
    """批次更新單字（Admin），接受 [{id, meaning, example_sentence}] 格式"""
    user = db.get_user(current_user["username"])
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="需要管理員權限")
    updated = 0
    with db.get_db() as conn:
        cur = conn.cursor()
        for item in body:
            word_id = item.get("id")
            if not word_id:
                continue
            fields, values = [], []
            if "meaning" in item:
                fields.append("meaning=%s")
                values.append(item["meaning"])
            if "example_sentence" in item:
                fields.append("example_sentence=%s")
                values.append(item["example_sentence"])
            if "suggested_meaning" in item:
                fields.append("suggested_meaning=%s")
                values.append(item["suggested_meaning"])
            if not fields:
                continue
            fields.append("updated_at=CURRENT_TIMESTAMP")
            values.append(word_id)
            cur.execute(f"UPDATE words SET {', '.join(fields)} WHERE id=%s", values)
            updated += cur.rowcount
    return {"ok": True, "updated": updated}


@router.get("/pending-suggestions")
def pending_suggestions(current_user: dict = Depends(get_current_user)):
    """取得有 suggested_meaning 的單字（Admin）"""
    user = db.get_user(current_user["username"])
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="需要管理員權限")
    with db.get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, word, meaning, suggested_meaning
            FROM words
            WHERE suggested_meaning IS NOT NULL AND suggested_meaning != ''
        """)
        return [dict(row) for row in cur.fetchall()]


@router.get("/pending-sentences")
def pending_sentences(batch_size: int = 30, offset: int = 0, current_user: dict = Depends(get_current_user)):
    """取得有例句的單字，供 review（Admin）"""
    user = db.get_user(current_user["username"])
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="需要管理員權限")
    with db.get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, word, meaning, example_sentence
            FROM words
            WHERE example_sentence IS NOT NULL AND example_sentence != ''
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (batch_size, offset))
        return [dict(row) for row in cur.fetchall()]


class ReviewSuggestionRequest(BaseModel):
    accept: bool
    new_meaning: Optional[str] = None


class ReviewSentenceRequest(BaseModel):
    new_sentence: str


@router.post("/{word_id}/review-suggestion")
def review_suggestion(word_id: int, body: ReviewSuggestionRequest, current_user: dict = Depends(get_current_user)):
    """接受或拒絕 suggested_meaning（Admin）"""
    user = db.get_user(current_user["username"])
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="需要管理員權限")
    with db.get_db() as conn:
        cur = conn.cursor()
        if body.accept and body.new_meaning:
            cur.execute(
                "UPDATE words SET meaning=%s, suggested_meaning=NULL, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                (body.new_meaning, word_id)
            )
        else:
            cur.execute("UPDATE words SET suggested_meaning=NULL WHERE id=%s", (word_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="找不到該單字")
    return {"ok": True, "word_id": word_id, "accepted": body.accept}


@router.post("/{word_id}/review-sentence")
def review_sentence(word_id: int, body: ReviewSentenceRequest, current_user: dict = Depends(get_current_user)):
    """更新例句（Admin）"""
    user = db.get_user(current_user["username"])
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="需要管理員權限")
    with db.get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE words SET example_sentence=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
            (body.new_sentence, word_id)
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="找不到該單字")
    return {"ok": True, "word_id": word_id, "new_sentence": body.new_sentence}


@router.delete("/{word_id}")
def delete_word(word_id: int, current_user: dict = Depends(get_current_user)):
    """Admin 刪除不適合的單字"""
    user = db.get_user(current_user["username"])
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="需要管理員權限")
    with db.get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT word FROM words WHERE id=%s", (word_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="找不到該單字")
        word = row["word"]
        cur.execute("DELETE FROM words WHERE id=%s", (word_id,))
    return {"ok": True, "deleted": word}
