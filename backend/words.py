from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import storage_postgres as db
from auth import get_current_user

router = APIRouter(prefix="/api/words", tags=["words"])


class AddWordRequest(BaseModel):
    word: str

class SuggestRequest(BaseModel):
    word: str
    suggested_meaning: str


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
        cursor = conn.cursor()
        cursor.execute(
            "SELECT word, meaning, cefr, created_at FROM words ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]


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
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE words SET suggested_meaning=? WHERE word=?",
            (suggestion, body.word)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="找不到該單字")
    return {"ok": True, "word": body.word, "suggested_meaning": suggestion}


@router.get("/search")
def search_words(q: str = "", limit: int = 20, current_user: dict = Depends(get_current_user)):
    """搜尋單字（Admin 用）"""
    with db.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, word, meaning, cefr, suggested_meaning FROM words WHERE word LIKE ? LIMIT ?",
            (f"%{q}%", limit)
        )
        return [dict(row) for row in cursor.fetchall()]


@router.delete("/{word_id}")
def delete_word(word_id: int, current_user: dict = Depends(get_current_user)):
    """Admin 刪除不適合的單字"""
    user = db.get_user(current_user["username"])
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="需要管理員權限")
    with db.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT word FROM words WHERE id=?", (word_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="找不到該單字")
        word = row["word"]
        cursor.execute("DELETE FROM words WHERE id=?", (word_id,))
    return {"ok": True, "deleted": word}
