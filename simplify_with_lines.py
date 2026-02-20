# 使用行级解析的方法删除左侧树形菜单相关代码

# 读取原始文件
with open('齿轮波纹度软件2_修改版.py.before_915_points20251127.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_nav_method = False
method_depth = 0

# 导航相关的方法列表
nav_methods = [
    'def create_floating_navigation(self):',
    'def toggle_nav_pin(self):',
    'def on_nav_visibility_changed(self, visible):',
    'def show_nav_context_menu(self, position):',
    'def on_tree_selection_changed(self):',
    'def _handle_page_switch(self, current, previous):',
    'def restore_nav_state(self):',
    'def save_nav_state(self):',
    'def enable_nav_autohide(self):',
    'def _hide_nav_dock(self):',
    'def enable_auto_dock(self)'
]

# 导航相关的代码行
nav_code_lines = [
    'self.create_floating_navigation()',
    'self.nav_tree_widget.itemSelectionChanged.connect(self.on_tree_selection_changed)',
    'self.nav_dock.visibilityChanged.connect(self.on_nav_visibility_changed)',
    'self.nav_tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)',
    'self.nav_tree_widget.customContextMenuRequested.connect(self.show_nav_context_menu)',
    'self.nav_tree_widget.currentItemChanged.connect(self._handle_page_switch)',
    'self.nav_is_pinned = False'
]

for line in lines:
    # 检查是否进入导航方法
    if not in_nav_method:
        # 检查是否匹配导航方法定义
        if any(line.strip().startswith(method) for method in nav_methods):
            in_nav_method = True
            # 计算方法的缩进深度
            method_depth = len(line) - len(line.lstrip())
            continue  # 跳过方法定义行
    else:
        # 检查是否退出导航方法
        current_depth = len(line) - len(line.lstrip())
        # 如果当前行是另一个方法定义且缩进等于或小于原方法
        if line.strip().startswith('def ') and current_depth <= method_depth:
            in_nav_method = False
            # 不要添加这行，因为它是下一个方法的定义，会在后面处理
            continue
        # 否则跳过导航方法内的所有行
        continue
    
    # 检查是否是导航相关的代码行
    if any(nav_code in line for nav_code in nav_code_lines):
        continue
    
    # 特殊处理_nav_auto_hide_timer的初始化
    if '_nav_auto_hide_timer = QTimer(self)' in line:
        continue
    
    # 特殊处理_nav_auto_hide_timer的timeout.connect
    if '_nav_auto_hide_timer.timeout.connect(self._hide_nav_dock)' in line:
        continue
    
    # 特殊处理恢复导航栏状态的代码块
    if '# 恢复导航栏状态' in line:
        continue
    
    if 'self.restore_nav_state()' in line:
        continue
    
    if '# 启用自动隐藏功能' in line:
        continue
    
    if 'self.enable_nav_autohide()' in line:
        continue
    
    # 特殊处理默认选中项设置的代码块
    if 'for i in range(self.nav_tree_widget.topLevelItemCount()):' in line:
        continue
    
    if 'root_item = self.nav_tree_widget.topLevelItem(i)' in line:
        continue
    
    if 'if root_item.text(0) == "基础信息":' in line:
        continue
    
    if 'for j in range(root_item.childCount()):' in line:
        continue
    
    if 'child_item = root_item.child(j)' in line:
        continue
    
    if 'if child_item.text(0) == "齿轮基本参数":' in line:
        continue
    
    if 'self.nav_tree_widget.setCurrentItem(child_item)' in line:
        continue
    
    if 'break' in line and 'root_item.text(0) == "基础信息"' in ''.join(new_lines[-5:]):
        continue
    
    if 'break' in line and 'child_item.text(0) == "齿轮基本参数"' in ''.join(new_lines[-5:]):
        continue
    
    # 如果不是导航相关的代码，添加到新行列表
    new_lines.append(line)

# 保存简化后的文件
with open('齿轮波纹度软件2_修改版_simplified.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("已创建简化版本文件: 齿轮波纹度软件2_修改版_simplified.py")
