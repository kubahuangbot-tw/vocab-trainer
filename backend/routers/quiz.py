import random
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import io, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import storage_postgres as db
from auth import get_current_user
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


def _load_all_meanings():
    """Load all Chinese meanings from DB for distractor pool."""
    try:
        with db.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT meaning FROM words WHERE meaning IS NOT NULL AND meaning != ''")
            return [row[0] for row in cursor.fetchall() if _has_chinese(row[0])]
    except Exception:
        return []

# Cache at startup from DB — refreshed on backend restart
_ALL_MEANINGS = _load_all_meanings()


@router.get("/questions", response_model=QuestionsResponse)
def get_questions(
    count: int = 10,
    difficulty_min: str = "A1",
    difficulty_max: str = "C1",
    mode: str = "random",
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("user_id")

    difficulty = f"{difficulty_min}-{difficulty_max}"
    trainer = VocabTrainer(user_id=user_id)

    words = trainer.select_words(count=count, mode=mode, difficulty=difficulty, review_ratio=0.3)

    # Fetch all word data from DB in bulk (meaning, difficulty, example, image)
    with db.get_db() as conn:
        import psycopg2.extras
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            "SELECT word, meaning, difficulty, example_sentence, image_path FROM words WHERE word = ANY(%s)",
            (list(words),)
        )
        rows = cursor.fetchall()
        meaning_map  = {row['word']: row['meaning'] for row in rows}
        level_map    = {row['word']: row['difficulty'] or 1 for row in rows}
        example_map  = {row['word']: row['example_sentence'] for row in rows}
        image_map    = {row['word']: row['image_path'] for row in rows}

    questions = []
    for word in words:
        meaning = meaning_map.get(word, "")
        if not _has_chinese(meaning):
            continue

        level = level_map.get(word, 1)
        wrong = random.sample([m for m in _ALL_MEANINGS if m != meaning], min(3, len(_ALL_MEANINGS) - 1))
        options = wrong + [meaning]
        random.shuffle(options)

        img_path = image_map.get(word)
        R2_BASE = os.environ.get("R2_BASE_URL", "https://pub-b6b3766953db4ce69c3b6d781c16e708.r2.dev")
        image_url = f"{R2_BASE}/{img_path.split('/')[-1]}" if img_path else None

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
