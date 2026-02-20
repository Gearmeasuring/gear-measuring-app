# 完整解决方案：注释掉所有与左侧树形菜单相关的代码调用

# 读取原始文件
with open('齿轮波纹度软件2_修改版.py.before_915_points20251127.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 要注释掉的导航相关代码行列表
nav_related_lines = [
    'self.create_floating_navigation()',
    'self.nav_tree_widget.itemSelectionChanged.connect(self.on_tree_selection_changed)',
    'self.nav_dock.visibilityChanged.connect(self.on_nav_visibility_changed)',
    'self.nav_tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)',
    'self.nav_tree_widget.customContextMenuRequested.connect(self.show_nav_context_menu)',
    'self.nav_tree_widget.currentItemChanged.connect(self._handle_page_switch)',
    'self._nav_auto_hide_timer = QTimer(self)',
    'self._nav_auto_hide_timer.timeout.connect(self._hide_nav_dock)',
    'self.nav_is_pinned = False',
    'self.restore_nav_state()',
    'self.enable_nav_autohide()'
]

# 注释掉所有导航相关代码行
for line in nav_related_lines:
    content = content.replace(line, '# ' + line + '  # 根据用户要求注释掉左侧树形菜单相关代码')

# 保存修改后的文件
with open('齿轮波纹度软件2_修改版_simplified.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("已创建简化版本文件: 齿轮波纹度软件2_修改版_simplified.py")
print("所有与左侧树形菜单相关的代码调用已被注释掉")
