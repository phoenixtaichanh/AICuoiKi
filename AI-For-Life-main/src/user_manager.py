"""
User Manager - Quản lý users và sessions
Lưu vào file nguoidung.txt (JSON format)
"""

import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

USER_FILE = "nguoidung.txt"
SESSION_LIFETIME = 86400  # 24 hours

def ensure_user_file():
    """Đảm bảo file nguoidung.txt tồn tại"""
    if not os.path.exists(USER_FILE):
        # Tạo file với user mặc định
        default_users = {
            "users": [
                {
                    "id": 1,
                    "username": "admin",
                    "password_hash": hash_password("password"),
                    "email": "admin@example.com",
                    "full_name": "Administrator",
                    "created_at": datetime.now().isoformat(),
                    "is_active": True
                },
                {
                    "id": 2,
                    "username": "nguoidung1",
                    "password_hash": hash_password("1234"),
                    "email": "user1@example.com",
                    "full_name": "Người Dùng 1",
                    "created_at": datetime.now().isoformat(),
                    "is_active": True
                }
            ],
            "sessions": []
        }
        write_users_file(default_users)
    return read_users_file()

def hash_password(password: str) -> str:
    """Hash password đơn giản (SHA256)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password"""
    return hash_password(password) == password_hash

def generate_session_token() -> str:
    """Tạo session token"""
    return secrets.token_urlsafe(32)

def read_users_file() -> Dict[str, Any]:
    """Đọc file nguoidung.txt"""
    try:
        if not os.path.exists(USER_FILE):
            ensure_user_file()
        
        with open(USER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # Nếu file lỗi, tạo lại
        ensure_user_file()
        return read_users_file()

def write_users_file(data: Dict[str, Any]):
    """Ghi file nguoidung.txt"""
    with open(USER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Tìm user theo username"""
    data = read_users_file()
    for user in data.get("users", []):
        if user.get("username") == username:
            return user
    return None

def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Tìm user theo email"""
    data = read_users_file()
    for user in data.get("users", []):
        if user.get("email") == email:
            return user
    return None

def find_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Tìm user theo ID"""
    data = read_users_file()
    for user in data.get("users", []):
        if user.get("id") == user_id:
            return user
    return None

def add_user(username: str, password: str, email: str = None, full_name: str = None) -> Dict[str, Any]:
    """Thêm user mới"""
    data = read_users_file()
    
    # Tìm ID lớn nhất
    max_id = 0
    for user in data.get("users", []):
        if user.get("id", 0) > max_id:
            max_id = user.get("id", 0)
    
    new_user = {
        "id": max_id + 1,
        "username": username,
        "password_hash": hash_password(password),
        "email": email,
        "full_name": full_name,
        "created_at": datetime.now().isoformat(),
        "is_active": True
    }
    
    data.setdefault("users", []).append(new_user)
    write_users_file(data)
    
    return new_user

def create_session(user_id: int) -> str:
    """Tạo session mới"""
    data = read_users_file()
    
    # Xóa sessions hết hạn
    cleanup_expired_sessions()
    
    # Xóa sessions cũ của user này
    data["sessions"] = [s for s in data.get("sessions", []) if s.get("user_id") != user_id]
    
    # Tạo session mới
    session_token = generate_session_token()
    expires_at = (datetime.now() + timedelta(seconds=SESSION_LIFETIME)).isoformat()
    
    new_session = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now().isoformat()
    }
    
    data.setdefault("sessions", []).append(new_session)
    write_users_file(data)
    
    return session_token

def find_session_by_token(token: str) -> Optional[Dict[str, Any]]:
    """Tìm session theo token"""
    data = read_users_file()
    now = datetime.now()
    
    for session in data.get("sessions", []):
        if session.get("session_token") == token:
            expires_at = datetime.fromisoformat(session.get("expires_at", ""))
            if expires_at > now:
                return session
    return None

def delete_session(token: str):
    """Xóa session"""
    data = read_users_file()
    data["sessions"] = [s for s in data.get("sessions", []) if s.get("session_token") != token]
    write_users_file(data)

def cleanup_expired_sessions():
    """Xóa sessions hết hạn"""
    data = read_users_file()
    now = datetime.now()
    
    data["sessions"] = [
        s for s in data.get("sessions", [])
        if datetime.fromisoformat(s.get("expires_at", "")) > now
    ]
    write_users_file(data)

def update_user_last_login(user_id: int):
    """Cập nhật last_login"""
    data = read_users_file()
    for user in data.get("users", []):
        if user.get("id") == user_id:
            user["last_login"] = datetime.now().isoformat()
            break
    write_users_file(data)

