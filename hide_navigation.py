# 将导航栏设置为不可见的简单修改方法
import re

# 读取原始文件
with open('齿轮波纹度软件2_修改版.py.before_915_points20251127.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修改create_floating_navigation方法，在方法末尾添加隐藏导航栏的代码
content = re.sub(r'(def create_floating_navigation\(self\):.*?)(?=^\s*def\s+|$)', r'\1\n        # 隐藏导航栏（根据用户要求）\n        self.nav_dock.hide()', content, flags=re.DOTALL | re.MULTILINE)

# 保存修改后的文件
with open('齿轮波纹度软件2_修改版_simplified.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("已创建简化版本文件: 齿轮波纹度软件2_修改版_simplified.py")
print("导航栏已设置为默认隐藏")
