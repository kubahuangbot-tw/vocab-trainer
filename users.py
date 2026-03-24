"""User management for VocabTrainer"""
import json
import os
import hashlib
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
USERS_FILE = DATA_DIR / "users.json"

# 初始化目錄
DATA_DIR.mkdir(exist_ok=True)

def load_users():
    """載入用戶資料"""
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    """儲存用戶資料"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def hash_password(password):
    """密碼雜湊"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, email=None, is_admin=False):
    """建立新用戶 (管理員呼叫)"""
    users = load_users()
    
    if username in users:
        return False, "用戶名已存在"
    
    # 建立用戶目錄
    user_dir = DATA_DIR / username
    user_dir.mkdir(exist_ok=True)
    
    users[username] = {
        "password": hash_password(password),
        "email": email,
        "gmail": email,  # 如果用 Gmail 登入
        "is_admin": is_admin,
        "created_at": "2026-03-23"
    }
    
    # 建立用戶資料檔案
    (user_dir / "progress.csv").write_text("")
    (user_dir / "wrong_words.csv").write_text("")
    (user_dir / "tested_words.json").write_text("{}")
    
    save_users(users)
    return True, f"用戶 {username} 建立成功"

def verify_user(username, password):
    """驗證用戶登入 (支援 SQLite)"""
    # 先嘗試 SQLite
    try:
        import storage_sqlite
        user = storage_sqlite.get_user(username)
        if user:
            if username == "guest" and password == "":
                return True
            if user['password'] == password or user['password'] == hash_password(password):
                return True
    except:
        pass
    
    # 回退到 JSON
    users = load_users()
    if username not in users:
        return False
    
    # Guest 用戶不需要密碼
    if username == "guest" and password == "":
        return True
    
    return users[username]["password"] == hash_password(password)

def get_user_data_dir(username):
    """取得用戶資料目錄"""
    return DATA_DIR / username

def list_users():
    """列出所有用戶"""
    users = load_users()
    return [{"username": u, "email": v.get("email"), "is_admin": v.get("is_admin")} 
            for u, v in users.items()]

def delete_user(username):
    """刪除用戶 (管理員呼叫)"""
    users = load_users()
    if username not in users:
        return False, "用戶不存在"
    
    if users[username].get("is_admin"):
        return False, "不能刪除管理員"
    
    del users[username]
    save_users(users)
    return True, f"用戶 {username} 已刪除"

# 預設管理員
def init_admin():
    """初始化管理員帳號"""
    users = load_users()
    if "admin" not in users:
        create_user("admin", "admin123", is_admin=True)
        print("管理員帳號: admin / admin123")

if __name__ == "__main__":
    # 初始化
    init_admin()
    print("用戶列表:", list_users())
