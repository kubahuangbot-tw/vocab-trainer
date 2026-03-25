from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/api/health")
def health():
    return {"status": "ok", "words": db.get_word_count()}
