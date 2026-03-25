"""
用戶管理模組 (只用 SQLite)
"""
import hashlib
import sys
from pathlib import Path

# 確保可以 import storage_sqlite
sys.path.insert(0, str(Path(__file__).parent))
from storage_sqlite import get_db, create_user as sqlite_create_user, get_user as sqlite_get_user


def hash_password(password):
    """密碼雜湊"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_user(username, password):
    """驗證用戶登入 (只用 SQLite)"""
    user = sqlite_get_user(username)
    if not user:
        return False
    
    # Guest 用戶不需要密碼
    if username == "guest" and password == "":
        return True
    
    # 密碼比對 (支援明文或 hash)
    if user['password'] == password:
        return True
    if user['password'] == hash_password(password):
        return True
    
    return False


def create_user(username, password, email=None, is_admin=False):
    """建立新用戶"""
    existing = sqlite_get_user(username)
    if existing:
        return False, "用戶名已存在"
    
    user_id = sqlite_create_user(username, password, email)
    return True, f"用戶 {username} 已建立 (ID: {user_id})"


def get_user_data_dir(username):
    """取得用戶資料目錄"""
    from storage_sqlite import get_db
    return Path(__file__).parent / "data"


def list_users():
    """列出所有用戶"""
    from storage_sqlite import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, display_name, created_at FROM users ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]


def delete_user(username):
    """刪除用戶"""
    from storage_sqlite import get_db
    user = sqlite_get_user(username)
    if not user:
        return False, "用戶不存在"
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
    
    return True, f"用戶 {username} 已刪除"
