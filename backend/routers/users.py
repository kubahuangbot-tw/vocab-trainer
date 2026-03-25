import math
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import storage_sqlite as db
from auth import get_current_user, hash_password
from word_list import WORD_LIST

router = APIRouter(prefix="/api/users", tags=["users"])

CEFR_MAP = {1: "A1", 2: "A2", 3: "B1", 4: "B2", 5: "C1"}


class UserInfo(BaseModel):
    username: str
    is_admin: bool


class StatsResponse(BaseModel):
    total_correct: int
    total_errors: int
    accuracy: float
    recent_errors_7d: int
    tested_count: int
    estimated_level: Optional[str]
    estimated_score: Optional[float]


class CreateUserRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None


class UserListItem(BaseModel):
    id: int
    username: str
    display_name: Optional[str]


@router.get("/me", response_model=UserInfo)
def get_me(current_user: dict = Depends(get_current_user)):
    return UserInfo(username=current_user["username"], is_admin=current_user["is_admin"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(current_user: dict = Depends(get_current_user)):
    user = db.get_user(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")

    user_id = user["id"]
    stats = db.get_stats(user_id)
    progress = db.get_user_progress(user_id)

    # AI level estimation (Laplace Smoothing)
    K = 5
    TARGET_ACC = 0.7
    level_stats = {i: {"correct": 0, "total": 0} for i in range(1, 6)}

    for word, p in progress.items():
        if word in WORD_LIST:
            level = WORD_LIST[word].get("level", 3)
            c = p.get("correct_count", 0)
            e = p.get("error_count", 0)
            t = c + e
            if t > 0:
                level_stats[level]["correct"] += c
                level_stats[level]["total"] += t

    total_ws = total_w = 0.0
    for level, ls in level_stats.items():
        n = ls["total"]
        if n == 0:
            continue
        adj_p = (ls["correct"] + K * TARGET_ACC) / (n + K)
        w = math.sqrt(n)
        total_ws += adj_p * w * level
        total_w += adj_p * w

    estimated_level = None
    estimated_score = None
    if total_w > 0:
        score = total_ws / total_w
        estimated_score = round(score, 2)
        base = CEFR_MAP.get(math.floor(score), "A1")
        suffix = "+" if (score - math.floor(score)) >= 0.5 else ""
        estimated_level = f"{base}{suffix}"

    return StatsResponse(
        total_correct=stats["total_correct"],
        total_errors=stats["total_errors"],
        accuracy=round(stats["accuracy"], 1),
        recent_errors_7d=stats["recent_errors_7d"],
        tested_count=len(progress),
        estimated_level=estimated_level,
        estimated_score=estimated_score,
    )


@router.get("/preferences")
def get_preferences(current_user: dict = Depends(get_current_user)):
    user = db.get_user(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    db.create_preferences_table()
    prefs = db.get_user_preferences(user["id"])
    return prefs or {"difficulty_min": "A1", "difficulty_max": "C1", "question_count": 10, "mode": "random"}


@router.put("/preferences")
def save_preferences(prefs: dict, current_user: dict = Depends(get_current_user)):
    user = db.get_user(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    db.create_preferences_table()
    db.save_user_preferences(user["id"], prefs)
    return {"ok": True}


@router.get("/list", response_model=List[UserListItem])
def list_users(current_user: dict = Depends(get_current_user)):
    if not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="需要管理員權限")
    users = db.list_users() if hasattr(db, "list_users") else []
    return users


@router.post("/create", response_model=UserListItem)
def create_user(body: CreateUserRequest, current_user: dict = Depends(get_current_user)):
    if not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="需要管理員權限")
    existing = db.get_user(body.username)
    if existing:
        raise HTTPException(status_code=400, detail="用戶名已存在")
    hashed = hash_password(body.password)
    user_id = db.create_user(body.username, hashed, body.display_name)
    return UserListItem(id=user_id, username=body.username, display_name=body.display_name)
