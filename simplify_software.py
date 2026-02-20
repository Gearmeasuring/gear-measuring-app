import re

# 读取原始文件
with open('齿轮波纹度软件2_修改版.py.before_915_points20251127.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 删除左侧树形菜单的调用
content = re.sub(r'\s*self\.create_floating_navigation\(\)\s*', '', content)

# 2. 删除整个create_floating_navigation方法
success = False
while not success:
    try:
        # 匹配方法定义和整个方法体
        method_pattern = r'def create_floating_navigation\(self\):[\s\S]*?\n\s*def '  
        match = re.search(method_pattern, content)
        if match:
            # 获取匹配的内容
            matched_content = match.group(0)
            # 只保留最后一个'def '
            new_content = matched_content[-4:]  # 'def '
            # 替换原内容
            content = content.replace(matched_content, new_content)
        else:
            success = True
    except Exception as e:
        print(f"Error: {e}")
        success = True

# 3. 删除与导航栏相关的事件处理
content = re.sub(r'\s*self\.nav_tree_widget\.itemSelectionChanged\.connect\(self\.on_tree_selection_changed\)\s*', '', content)
content = re.sub(r'\s*self\.nav_dock\.visibilityChanged\.connect\(self\.on_nav_visibility_changed\)\s*', '', content)
content = re.sub(r'\s*self\.nav_tree_widget\.setContextMenuPolicy\(Qt\.CustomContextMenu\)\s*', '', content)
content = re.sub(r'\s*self\.nav_tree_widget\.customContextMenuRequested\.connect\(self\.show_nav_context_menu\)\s*', '', content)
content = re.sub(r'\s*self\.nav_tree_widget\.currentItemChanged\.connect\(self\._handle_page_switch\)\s*', '', content)

# 4. 删除与导航栏相关的变量初始化
content = re.sub(r'\s*self\._nav_auto_hide_timer\s*=\s*QTimer\(self\).*?self\._nav_auto_hide_timer\.timeout\.connect\(self\._hide_nav_dock\)\s*', '', content, flags=re.DOTALL)
content = re.sub(r'\s*self\.nav_is_pinned\s*=\s*False\s*', '', content)

# 5. 删除导航相关的方法
navigation_methods = [
    'toggle_nav_pin',
    'on_nav_visibility_changed',
    'show_nav_context_menu',
    'on_tree_selection_changed',
    '_handle_page_switch',
    'restore_nav_state',
    'save_nav_state',
    'enable_nav_autohide',
    '_hide_nav_dock',
    'enable_auto_dock'
]

for method in navigation_methods:
    method_pattern = rf'def {method}\(self.*?\):[\s\S]*?\n\s*def '
    match = re.search(method_pattern, content)
    if match:
        # 获取匹配的内容
        matched_content = match.group(0)
        # 只保留最后一个'def '
        new_content = matched_content[-4:]  # 'def '
        # 替换原内容
        content = content.replace(matched_content, new_content)

# 6. 修复_delayed_create_pages方法中的错误引用
content = re.sub(r'\s*# 设置默认选中项\(基本信息\)\s*for i in range\(self\.nav_tree_widget\.topLevelItemCount\(\)\):.*?break\s*', '', content, flags=re.DOTALL)
content = re.sub(r'\s*# 恢复导航栏状态\s*self\.restore_nav_state\(\)\s*# 启用自动隐藏功能\s*self\.enable_nav_autohide\(\)\s*', '', content)

# 7. 保存简化后的文件
with open('齿轮波纹度软件2_修改版_simplified.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("已创建简化版本文件: 齿轮波纹度软件2_修改版_simplified.py")
