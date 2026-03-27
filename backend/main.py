from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import storage_sqlite as db
from routers import auth, quiz, users, words

db.init_db()
db.create_preferences_table()

app = FastAPI(title="VocabTrainer API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(quiz.router)
app.include_router(users.router)
app.include_router(words.router)

# Serve word images as static files
_data_dir = Path(os.environ.get("DATA_DIR", Path(__file__).parent.parent / "data"))
_images_dir = _data_dir / "word_images"
_images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/word_images", StaticFiles(directory=str(_images_dir)), name="word_images")


@app.get("/api/health")
def health():
    return {"status": "ok", "words": db.get_word_count()}
