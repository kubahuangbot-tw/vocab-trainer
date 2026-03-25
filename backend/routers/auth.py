from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from pydantic import BaseModel
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import storage_sqlite as db
from auth import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    is_admin: bool


@router.post("/login", response_model=LoginResponse)
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = db.get_user(form.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用戶名或密碼錯誤")

    if not verify_password(form.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用戶名或密碼錯誤")

    is_admin = bool(user.get("is_admin", False))
    token = create_access_token({"sub": user["username"], "is_admin": is_admin})
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        username=user["username"],
        is_admin=is_admin,
    )
