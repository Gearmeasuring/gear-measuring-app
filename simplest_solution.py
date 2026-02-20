# 最简单的解决方案：注释掉左侧树形菜单的创建调用

# 读取原始文件
with open('齿轮波纹度软件2_修改版.py.before_915_points20251127.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并注释掉create_floating_navigation方法的调用
content = content.replace('self.create_floating_navigation()', '# self.create_floating_navigation()  # 根据用户要求注释掉左侧树形菜单')

# 保存修改后的文件
with open('齿轮波纹度软件2_修改版_simplified.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("已创建简化版本文件: 齿轮波纹度软件2_修改版_simplified.py")
print("左侧树形菜单的创建调用已被注释掉")
