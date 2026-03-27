import random
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import io, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import storage_sqlite as db
from auth import get_current_user
from word_list import WORD_LIST
from trainer import VocabTrainer, DIFFICULTY_LEVELS

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


class Question(BaseModel):
    word: str
    options: List[str]
    correct_answer: str
    level: int
    cefr: str
    example_sentence: Optional[str] = None
    image_url: Optional[str] = None


class QuestionsResponse(BaseModel):
    questions: List[Question]
    total: int


class AnswerRequest(BaseModel):
    word: str
    selected: str
    correct_answer: str


class AnswerResponse(BaseModel):
    correct: bool
    word: str
    correct_answer: str
    your_answer: str


CEFR_MAP = {1: "A1", 2: "A2", 3: "B1", 4: "B2", 5: "C1", 6: "C2"}


def _has_chinese(meaning: str) -> bool:
    return bool(meaning) and any('\u4e00' <= c <= '\u9fff' for c in meaning)


@router.get("/questions", response_model=QuestionsResponse)
def get_questions(
    count: int = 10,
    difficulty_min: str = "A1",
    difficulty_max: str = "C1",
    mode: str = "random",
    current_user: dict = Depends(get_current_user),
):
    user = db.get_user(current_user["username"])
    user_id = user["id"] if user else None

    difficulty = f"{difficulty_min}-{difficulty_max}"
    trainer = VocabTrainer(user_id=user_id)

    words = trainer.select_words(count=count, mode=mode, difficulty=difficulty, review_ratio=0.3)

    # Build all Chinese meanings for wrong options
    all_meanings = [
        d["meaning"] for d in WORD_LIST.values()
        if _has_chinese(d.get("meaning", ""))
    ]

    # Fetch example sentences and image paths from DB in bulk
    with db.get_db() as conn:
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(words))
        cursor.execute(
            f"SELECT word, example_sentence, image_path FROM words WHERE word IN ({placeholders})",
            words
        )
        rows = cursor.fetchall()
        example_map = {row['word']: row['example_sentence'] for row in rows}
        image_map   = {row['word']: row['image_path'] for row in rows}

    questions = []
    for word in words:
        if word not in WORD_LIST:
            continue
        data = WORD_LIST[word]
        meaning = data.get("meaning", "")
        if not _has_chinese(meaning):
            continue

        level = data.get("level", 1)
        wrong = random.sample([m for m in all_meanings if m != meaning], min(3, len(all_meanings) - 1))
        options = wrong + [meaning]
        random.shuffle(options)

        img_path = image_map.get(word)
        image_url = f"/word_images/{img_path.split('/')[-1]}" if img_path else None

        questions.append(Question(
            word=word,
            options=options,
            correct_answer=meaning,
            level=level,
            cefr=CEFR_MAP.get(level, "A1"),
            example_sentence=example_map.get(word) or None,
            image_url=image_url,
        ))

    return QuestionsResponse(questions=questions, total=len(questions))


@router.post("/answer", response_model=AnswerResponse)
def submit_answer(
    body: AnswerRequest,
    current_user: dict = Depends(get_current_user),
):
    user = db.get_user(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")

    user_id = user["id"]
    is_correct = body.selected == body.correct_answer

    db.update_progress(user_id, body.word, body.correct_answer, is_correct)
    if not is_correct:
        db.add_wrong_record(user_id, body.word, body.correct_answer, body.selected)

    return AnswerResponse(
        correct=is_correct,
        word=body.word,
        correct_answer=body.correct_answer,
        your_answer=body.selected,
    )


@router.get("/tts/{word}")
def tts(word: str, current_user: dict = Depends(get_current_user)):
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text=word, lang="en").write_to_fp(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 失敗: {e}")
