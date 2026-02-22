"""
用户认证模块
支持用户注册、登录、密码管理
"""

import streamlit as st
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# 用户数据文件路径
USERS_FILE = "users.json"


def load_users() -> Dict[str, Any]:
    """加载用户数据"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_users(users: Dict[str, Any]):
    """保存用户数据"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def hash_password(password: str, salt: Optional[str] = None) -> tuple:
    """
    使用 PBKDF2 哈希密码
    返回 (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)

    # 使用 PBKDF2 进行密码哈希
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # 迭代次数
    ).hex()

    return hashed, salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """验证密码"""
    new_hash, _ = hash_password(password, salt)
    return new_hash == hashed


def register_user(username: str, password: str, email: str = "", company: str = "") -> tuple:
    """
    注册新用户
    返回 (success: bool, message: str)
    """
    users = load_users()

    # 检查用户名是否已存在
    if username in users:
        return False, "Username already exists"

    # 验证输入
    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(password) < 6:
        return False, "Password must be at least 6 characters"

    # 创建用户
    hashed_password, salt = hash_password(password)

    users[username] = {
        "username": username,
        "password_hash": hashed_password,
        "salt": salt,
        "email": email,
        "company": company,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "is_active": True,
        "role": "user"  # 可以是 user, admin 等
    }

    save_users(users)
    return True, "Registration successful"


def login_user(username: str, password: str) -> tuple:
    """
    用户登录
    返回 (success: bool, message: str, user_data: dict)
    """
    users = load_users()

    if username not in users:
        return False, "Username or password is incorrect", None

    user = users[username]

    if not user.get("is_active", True):
        return False, "Account is disabled", None

    if not verify_password(password, user["password_hash"], user["salt"]):
        return False, "Username or password is incorrect", None

    # 更新最后登录时间
    user["last_login"] = datetime.now().isoformat()
    save_users(users)

    # 返回用户数据（不包含密码）
    user_data = {
        "username": user["username"],
        "email": user.get("email", ""),
        "company": user.get("company", ""),
        "role": user.get("role", "user"),
        "created_at": user.get("created_at", ""),
        "last_login": user["last_login"]
    }

    return True, "Login successful", user_data


def change_password(username: str, old_password: str, new_password: str) -> tuple:
    """
    修改密码
    返回 (success: bool, message: str)
    """
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters"

    users = load_users()

    if username not in users:
        return False, "User not found"

    user = users[username]

    if not verify_password(old_password, user["password_hash"], user["salt"]):
        return False, "Current password is incorrect"

    # 更新密码
    hashed_password, salt = hash_password(new_password)
    user["password_hash"] = hashed_password
    user["salt"] = salt

    save_users(users)
    return True, "Password changed successfully"


def init_session_state():
    """初始化 session state"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "show_register" not in st.session_state:
        st.session_state.show_register = False


def login_page():
    """显示登录页面"""
    st.title("🔐 Gear Measurement System")
    st.markdown("---")

    # 创建两列布局
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.session_state.show_register:
            # 注册界面
            st.subheader("📝 User Registration")

            with st.form("register_form"):
                new_username = st.text_input("Username", placeholder="Enter username (min 3 chars)")
                new_password = st.text_input("Password", type="password", placeholder="Enter password (min 6 chars)")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
                email = st.text_input("Email (optional)", placeholder="your@email.com")
                company = st.text_input("Company (optional)", placeholder="Your company name")

                submitted = st.form_submit_button("Register", use_container_width=True)

                if submitted:
                    if not new_username or not new_password:
                        st.error("Please fill in all required fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success, message = register_user(new_username, new_password, email, company)
                        if success:
                            st.success(message)
                            st.info("Please login with your new account")
                            st.session_state.show_register = False
                            st.rerun()
                        else:
                            st.error(message)

            if st.button("← Back to Login", use_container_width=True):
                st.session_state.show_register = False
                st.rerun()

        else:
            # 登录界面
            st.subheader("🔑 User Login")

            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")

                col_login, col_register = st.columns(2)
                with col_login:
                    login_submitted = st.form_submit_button("Login", use_container_width=True)

                if login_submitted:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        success, message, user_data = login_user(username, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user = user_data
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

            # 注册按钮在表单外
            if st.button("📝 Create New Account", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()

            # 显示系统信息
            st.markdown("---")
            st.markdown("""
            **System Features:**
            - 📊 Gear profile and lead analysis
            - 📈 Pitch deviation measurement
            - 📉 Merged curve analysis
            - 📄 PDF report generation
            - 🔒 Secure data storage
            """)


def logout():
    """用户登出"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()


def get_current_user() -> Optional[Dict[str, Any]]:
    """获取当前登录用户信息"""
    if st.session_state.authenticated:
        return st.session_state.user
    return None


def require_auth(func):
    """
    装饰器：要求用户登录才能访问
    用法：
        @require_auth
        def protected_page():
            st.write("This is a protected page")
    """
    def wrapper(*args, **kwargs):
        init_session_state()
        if not st.session_state.authenticated:
            login_page()
            return
        return func(*args, **kwargs)
    return wrapper
