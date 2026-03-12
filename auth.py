"""
用户认证模块
支持用户注册、登录、密码管理、访问记录、会话持久化
支持多用户并发访问
"""

import streamlit as st
import hashlib
import secrets
import json
import os
import time
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List

# 用户数据文件路径
USERS_FILE = "users.json"
ACCESS_LOG_FILE = "access_log.json"
SESSION_FILE = ".session_cache.json"

# 默认管理员账号
DEFAULT_ADMIN = "tonyztzhou"

# 会话有效期（秒）- 7天
SESSION_EXPIRY = 7 * 24 * 60 * 60

# 文件锁，用于多线程安全
_file_lock = threading.Lock()


def _safe_read_json(filepath: str) -> Any:
    """线程安全地读取JSON文件"""
    with _file_lock:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return None


def _safe_write_json(filepath: str, data: Any):
    """线程安全地写入JSON文件"""
    with _file_lock:
        # 先写入临时文件，然后重命名，避免写入中断导致数据损坏
        temp_file = filepath + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # 原子性重命名
        os.replace(temp_file, filepath)


def load_users() -> Dict[str, Any]:
    """加载用户数据"""
    users = _safe_read_json(USERS_FILE)
    if users is None:
        users = {}
    # 如果用户数据为空，创建默认管理员账号
    if not users:
        # 创建默认管理员账号，密码: admin123
        hashed_password, salt = hash_password("admin123")
        users[DEFAULT_ADMIN] = {
            "username": DEFAULT_ADMIN,
            "password_hash": hashed_password,
            "salt": salt,
            "email": "",
            "company": "Jinxing",
            "role": "admin",
            "created_at": datetime.now().isoformat()
        }
        save_users(users)
        print(f"已创建默认管理员账号: {DEFAULT_ADMIN}, 密码: admin123")
    # 确保默认管理员存在且角色正确
    if DEFAULT_ADMIN in users:
        users[DEFAULT_ADMIN]["role"] = "admin"
    return users


def save_users(users: Dict[str, Any]):
    """保存用户数据"""
    # 确保默认管理员角色正确
    if DEFAULT_ADMIN in users:
        users[DEFAULT_ADMIN]["role"] = "admin"
    _safe_write_json(USERS_FILE, users)


def load_access_log() -> List[Dict[str, Any]]:
    """加载访问记录"""
    logs = _safe_read_json(ACCESS_LOG_FILE)
    if logs is None:
        return []
    return logs


def save_access_log(logs: List[Dict[str, Any]]):
    """保存访问记录"""
    _safe_write_json(ACCESS_LOG_FILE, logs)


def get_beijing_time() -> datetime:
    """获取北京时间"""
    return datetime.now(ZoneInfo("Asia/Shanghai"))


def format_beijing_time(dt: datetime = None) -> str:
    """格式化北京时间为字符串"""
    if dt is None:
        dt = get_beijing_time()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def log_access(username: str, action: str, details: str = ""):
    """记录用户访问（使用北京时间）"""
    logs = load_access_log()
    logs.append({
        "username": username,
        "action": action,
        "details": details,
        "timestamp": format_beijing_time(),
        "ip": "",  # 在Streamlit中无法直接获取IP
    })
    # 只保留最近1000条记录
    if len(logs) > 1000:
        logs = logs[-1000:]
    save_access_log(logs)


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
        return False, "用户名已存在"

    # 验证输入
    if len(username) < 3:
        return False, "用户名至少需要3个字符"

    if len(password) < 6:
        return False, "密码至少需要6个字符"

    # 创建用户
    hashed_password, salt = hash_password(password)

    # 如果是默认管理员账号，设置为admin角色
    role = "admin" if username == DEFAULT_ADMIN else "user"

    users[username] = {
        "username": username,
        "password_hash": hashed_password,
        "salt": salt,
        "email": email,
        "company": company,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "is_active": True,
        "role": role
    }

    save_users(users)
    log_access(username, "注册", "新用户注册")
    return True, "注册成功"


def login_user(username: str, password: str) -> tuple:
    """
    用户登录
    返回 (success: bool, message: str, user_data: dict)
    """
    users = load_users()

    if username not in users:
        return False, "用户名或密码错误", None

    user = users[username]

    if not user.get("is_active", True):
        return False, "账户已被禁用", None

    if not verify_password(password, user["password_hash"], user["salt"]):
        log_access(username, "登录失败", "密码错误")
        return False, "用户名或密码错误", None

    # 更新最后登录时间
    user["last_login"] = datetime.now().isoformat()
    save_users(users)

    # 记录登录
    log_access(username, "登录", "用户登录成功")

    # 返回用户数据（不包含密码）
    user_data = {
        "username": user["username"],
        "email": user.get("email", ""),
        "company": user.get("company", ""),
        "role": user.get("role", "user"),
        "created_at": user.get("created_at", ""),
        "last_login": user["last_login"]
    }

    # 注意：不再保存全局会话文件，每个浏览器会话独立
    # 这修复了多用户同时访问时看到其他用户登录状态的问题

    return True, "登录成功", user_data


def change_password(username: str, old_password: str, new_password: str) -> tuple:
    """
    修改密码
    返回 (success: bool, message: str)
    """
    if len(new_password) < 6:
        return False, "新密码至少需要6个字符"

    users = load_users()

    if username not in users:
        return False, "用户不存在"

    user = users[username]

    if not verify_password(old_password, user["password_hash"], user["salt"]):
        return False, "当前密码错误"

    # 更新密码
    hashed_password, salt = hash_password(new_password)
    user["password_hash"] = hashed_password
    user["salt"] = salt

    save_users(users)
    log_access(username, "修改密码", "用户修改密码")
    return True, "密码修改成功"


def is_admin(username: str) -> bool:
    """检查用户是否为管理员"""
    users = load_users()
    if username in users:
        return users[username].get("role", "user") == "admin"
    return False


def get_all_users() -> List[Dict[str, Any]]:
    """获取所有用户信息（用于管理员）"""
    users = load_users()
    user_list = []
    for username, user_data in users.items():
        user_list.append({
            "username": username,
            "email": user_data.get("email", ""),
            "company": user_data.get("company", ""),
            "role": user_data.get("role", "user"),
            "created_at": user_data.get("created_at", ""),
            "last_login": user_data.get("last_login", ""),
            "is_active": user_data.get("is_active", True)
        })
    return user_list


def toggle_user_status(username: str, active: bool) -> bool:
    """启用/禁用用户账户"""
    users = load_users()
    if username in users:
        users[username]["is_active"] = active
        save_users(users)
        action = "启用" if active else "禁用"
        log_access(username, f"账户{action}", f"管理员操作")
        return True
    return False


def delete_user(username: str) -> bool:
    """删除用户"""
    if username == DEFAULT_ADMIN:
        return False  # 不能删除默认管理员

    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        log_access(username, "删除用户", "管理员删除用户")
        return True
    return False


def save_session(username: str, user_data: Dict[str, Any]):
    """保存会话到文件"""
    session_data = {
        "username": username,
        "user_data": user_data,
        "timestamp": time.time(),
        "expiry": time.time() + SESSION_EXPIRY
    }
    try:
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False)
    except Exception as e:
        print(f"保存会话失败: {e}")


def load_session() -> Optional[Dict[str, Any]]:
    """从文件加载会话"""
    if not os.path.exists(SESSION_FILE):
        return None

    try:
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        # 检查会话是否过期
        if time.time() > session_data.get("expiry", 0):
            # 会话过期，删除文件
            try:
                os.remove(SESSION_FILE)
            except:
                pass
            return None

        return session_data
    except Exception as e:
        print(f"加载会话失败: {e}")
        return None


def clear_session():
    """清除会话文件"""
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
        except:
            pass


def init_session_state():
    """初始化 session state"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "show_register" not in st.session_state:
        st.session_state.show_register = False
    if "show_admin" not in st.session_state:
        st.session_state.show_admin = False
    
    # 注意：移除了全局会话文件恢复功能
    # 每个浏览器会话现在独立，不会共享登录状态
    # 这修复了多用户同时访问时看到其他用户登录状态的问题


def login_page():
    """显示登录页面"""
    st.title("🔐 齿轮傅里叶级数分析软件")
    st.caption("控制和改善你的齿轮噪声")
    st.markdown("---")

    # 创建两列布局
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.session_state.show_register:
            # 注册界面
            st.subheader("📝 用户注册")

            with st.form("register_form"):
                new_username = st.text_input("用户名", placeholder="请输入用户名（至少3个字符）")
                new_password = st.text_input("密码", type="password", placeholder="请输入密码（至少6个字符）")
                confirm_password = st.text_input("确认密码", type="password", placeholder="请再次输入密码")
                email = st.text_input("邮箱（可选）", placeholder="your@email.com")
                company = st.text_input("公司（可选）", placeholder="您的公司名称")

                submitted = st.form_submit_button("注册", use_container_width=True)

                if submitted:
                    if not new_username or not new_password:
                        st.error("请填写所有必填项")
                    elif new_password != confirm_password:
                        st.error("两次输入的密码不一致")
                    else:
                        success, message = register_user(new_username, new_password, email, company)
                        if success:
                            st.success(message)
                            st.info("请使用新账户登录")
                            st.session_state.show_register = False
                            st.rerun()
                        else:
                            st.error(message)

            if st.button("← 返回登录", use_container_width=True):
                st.session_state.show_register = False
                st.rerun()

        else:
            # 登录界面
            st.subheader("🔑 用户登录")

            with st.form("login_form"):
                username = st.text_input("用户名", placeholder="请输入用户名")
                password = st.text_input("密码", type="password", placeholder="请输入密码")

                col_login, col_register = st.columns(2)
                with col_login:
                    login_submitted = st.form_submit_button("登录", use_container_width=True)

                if login_submitted:
                    if not username or not password:
                        st.error("请输入用户名和密码")
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
            if st.button("📝 创建新账户", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()

            # 显示使用说明
            st.markdown("---")
            st.markdown("""
            **📖 使用说明：**
            1. **已有账号**：直接输入用户名和密码登录
            2. **新用户**：点击"创建新账户"注册，注册后即可登录
            3. **各自账号**：每个用户拥有独立的账号和密码
            4. **数据安全**：个人数据隔离存储，保护隐私
            
            **🔧 系统功能：**
            - 📊 齿形/齿向波纹度分析
            - 📈 周节偏差测量报告
            - 📉 0-360°合并曲线分析
            - 📄 专业PDF报告生成
            - 🔒 安全数据存储与访问记录
            """)


def admin_panel():
    """管理员面板"""
    st.title("🔧 管理员面板")
    st.markdown("---")

    # 检查是否为管理员
    user = get_current_user()
    if not user or not is_admin(user["username"]):
        st.error("您没有管理员权限")
        return

    # 标签页
    tab1, tab2, tab3 = st.tabs(["📊 访问记录", "👥 用户管理", "📈 统计信息"])

    with tab1:
        st.subheader("访问记录")
        logs = load_access_log()

        if not logs:
            st.info("暂无访问记录")
        else:
            # 筛选选项
            col1, col2 = st.columns(2)
            with col1:
                filter_user = st.selectbox(
                    "筛选用户",
                    ["全部"] + list(set(log["username"] for log in logs)),
                    key="filter_user"
                )
            with col2:
                filter_action = st.selectbox(
                    "筛选操作",
                    ["全部"] + list(set(log["action"] for log in logs)),
                    key="filter_action"
                )

            # 过滤记录
            filtered_logs = logs
            if filter_user != "全部":
                filtered_logs = [log for log in filtered_logs if log["username"] == filter_user]
            if filter_action != "全部":
                filtered_logs = [log for log in filtered_logs if log["action"] == filter_action]

            # 显示记录
            st.write(f"显示 {len(filtered_logs)} 条记录（共 {len(logs)} 条）")

            for log in reversed(filtered_logs[-100:]):  # 只显示最近100条
                with st.expander(f"{log['timestamp']} - {log['username']} - {log['action']}"):
                    st.write(f"**用户:** {log['username']}")
                    st.write(f"**操作:** {log['action']}")
                    st.write(f"**详情:** {log.get('details', '')}")
                    st.write(f"**时间:** {log['timestamp']}")

    with tab2:
        st.subheader("用户管理")
        users = get_all_users()

        if not users:
            st.info("暂无用户")
        else:
            # 显示用户列表
            for user_info in users:
                with st.expander(f"{user_info['username']} ({user_info['role']}) {'✅' if user_info['is_active'] else '❌'}"):
                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        st.write(f"**邮箱:** {user_info['email'] or '未设置'}")
                        st.write(f"**公司:** {user_info['company'] or '未设置'}")
                        st.write(f"**角色:** {user_info['role']}")

                    with col2:
                        st.write(f"**创建时间:** {user_info['created_at'][:19] if user_info['created_at'] else '未知'}")
                        st.write(f"**最后登录:** {user_info['last_login'][:19] if user_info['last_login'] else '从未登录'}")
                        st.write(f"**状态:** {'正常' if user_info['is_active'] else '已禁用'}")

                    with col3:
                        if user_info['username'] != DEFAULT_ADMIN:
                            if user_info['is_active']:
                                if st.button(f"禁用", key=f"disable_{user_info['username']}"):
                                    if toggle_user_status(user_info['username'], False):
                                        st.success("已禁用")
                                        st.rerun()
                            else:
                                if st.button(f"启用", key=f"enable_{user_info['username']}"):
                                    if toggle_user_status(user_info['username'], True):
                                        st.success("已启用")
                                        st.rerun()

                            if st.button(f"删除", key=f"delete_{user_info['username']}"):
                                if delete_user(user_info['username']):
                                    st.success("已删除")
                                    st.rerun()

    with tab3:
        st.subheader("统计信息")
        users = get_all_users()
        logs = load_access_log()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总用户数", len(users))
        with col2:
            active_users = len([u for u in users if u['is_active']])
            st.metric("活跃用户", active_users)
        with col3:
            admin_count = len([u for u in users if u['role'] == 'admin'])
            st.metric("管理员", admin_count)
        with col4:
            st.metric("访问记录", len(logs))

        # 今日访问统计（使用北京时间）
        today = get_beijing_time().strftime("%Y-%m-%d")
        today_logs = [log for log in logs if log['timestamp'].startswith(today)]
        st.write(f"**今日访问次数:** {len(today_logs)}")

        # 登录失败统计
        failed_logins = len([log for log in logs if log['action'] == '登录失败'])
        st.write(f"**登录失败次数:** {failed_logins}")


def logout():
    """用户登出"""
    user = get_current_user()
    if user:
        log_access(user["username"], "登出", "用户退出登录")
    # 只清除当前会话状态，不清除全局会话文件
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
