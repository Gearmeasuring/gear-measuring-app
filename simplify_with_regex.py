# 使用多行正则表达式删除左侧树形菜单相关代码
import re

# 读取原始文件
with open('齿轮波纹度软件2_修改版.py.before_915_points20251127.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 删除create_floating_navigation方法调用
content = re.sub(r'self\.create_floating_navigation\(\)', '', content)

# 删除导航相关的信号连接
content = re.sub(r'self\.nav_tree_widget\.itemSelectionChanged\.connect\(self\.on_tree_selection_changed\)', '', content)
content = re.sub(r'self\.nav_dock\.visibilityChanged\.connect\(self\.on_nav_visibility_changed\)', '', content)
content = re.sub(r'self\.nav_tree_widget\.setContextMenuPolicy\(Qt\.CustomContextMenu\)', '', content)
content = re.sub(r'self\.nav_tree_widget\.customContextMenuRequested\.connect\(self\.show_nav_context_menu\)', '', content)
content = re.sub(r'self\.nav_tree_widget\.currentItemChanged\.connect\(self\._handle_page_switch\)', '', content)

# 删除_nav_auto_hide_timer相关代码
content = re.sub(r'self\._nav_auto_hide_timer\s*=\s*QTimer\(self\)', '', content)
content = re.sub(r'self\._nav_auto_hide_timer\.timeout\.connect\(self\._hide_nav_dock\)', '', content)

# 删除导航相关变量初始化
content = re.sub(r'self\.nav_is_pinned\s*=\s*False', '', content)

# 删除恢复导航栏状态和启用自动隐藏的代码
content = re.sub(r'#\s*恢复导航栏状态\s*\n\s*self\.restore_nav_state\(\)', '', content)
content = re.sub(r'#\s*启用自动隐藏功能\s*\n\s*self\.enable_nav_autohide\(\)', '', content)

# 删除导航相关方法（使用多行匹配）
nav_methods_patterns = [
    r'def create_floating_navigation\(self\):.*?(?=^\s*def\s+|$)',
    r'def toggle_nav_pin\(self\):.*?(?=^\s*def\s+|$)',
    r'def on_nav_visibility_changed\(self, visible\):.*?(?=^\s*def\s+|$)',
    r'def show_nav_context_menu\(self, position\):.*?(?=^\s*def\s+|$)',
    r'def on_tree_selection_changed\(self\):.*?(?=^\s*def\s+|$)',
    r'def _handle_page_switch\(self, current, previous\):.*?(?=^\s*def\s+|$)',
    r'def restore_nav_state\(self\):.*?(?=^\s*def\s+|$)',
    r'def save_nav_state\(self\):.*?(?=^\s*def\s+|$)',
    r'def enable_nav_autohide\(self\):.*?(?=^\s*def\s+|$)',
    r'def _hide_nav_dock\(self\):.*?(?=^\s*def\s+|$)',
    r'def enable_auto_dock\(self\):.*?(?=^\s*def\s+|$)'
]

for pattern in nav_methods_patterns:
    content = re.sub(pattern, '', content, flags=re.DOTALL | re.MULTILINE)

# 删除默认选中项设置的代码块
content = re.sub(r'for i in range\(self\.nav_tree_widget\.topLevelItemCount\(\)\):.*?break.*?break', '', content, flags=re.DOTALL)

# 删除_nav_is_pinned相关的引用
content = re.sub(r'self\.nav_is_pinned', '', content)

# 删除_nav_dock相关的引用
content = re.sub(r'self\.nav_dock', '', content)

# 删除_nav_tree_widget相关的引用
content = re.sub(r'self\.nav_tree_widget', '', content)

# 清理空白行
content = re.sub(r'\n\s*\n', '\n', content)

# 保存简化后的文件
with open('齿轮波纹度软件2_修改版_simplified.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("已创建简化版本文件: 齿轮波纹度软件2_修改版_simplified.py")
