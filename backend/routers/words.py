from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import storage_sqlite as db
from auth import get_current_user

router = APIRouter(prefix="/api/words", tags=["words"])


class AddWordRequest(BaseModel):
    word: str


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
