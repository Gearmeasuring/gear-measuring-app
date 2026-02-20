# 重写create_floating_navigation方法，只保留特定节点
import re

# 读取原始文件
with open('齿轮波纹度软件2_修改版.py.before_915_points20251127.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找create_floating_navigation方法
match = re.search(r'def create_floating_navigation\(self\):.*?(?=^\s*def\s+|$)', content, flags=re.DOTALL | re.MULTILINE)
if match:
    method_content = match.group(0)
    
    # 创建新的方法内容，只保留文件操作、基础信息和报表工具节点
    new_method_content = re.sub(r'# 添加树形节点.*?(?=QTreeWidgetItem\(report_item, \["🧮 公差计算器"\]\))', 
                                '''# 添加树形节点
        root = QTreeWidgetItem(self.nav_tree_widget, ["功能导航"])
        
        # 第一级节点 - 只保留文件操作、基础信息和报表工具
        file_item = QTreeWidgetItem(root, ["📁 文件操作"])
        basic_item = QTreeWidgetItem(root, ["📊 基础信息"])
        report_item = QTreeWidgetItem(root, ["📄 报表工具"])
        
        # 第二级节点 (文件操作)
        QTreeWidgetItem(file_item, ["📂 打开文件"])
        QTreeWidgetItem(file_item, ["📂 批量处理"])
        
        # 第二级节点 (基础信息)
        QTreeWidgetItem(basic_item, ["ℹ️ 基本信息"])
        QTreeWidgetItem(basic_item, ["⚙️ 齿轮参数"])
        QTreeWidgetItem(basic_item, ["🔄 左右齿面"])
        QTreeWidgetItem(basic_item, ["📈 齿向数据"])
        QTreeWidgetItem(basic_item, ["📉 齿形数据"])
        
        # 第二级节点 (报表工具)
        QTreeWidgetItem(report_item, ["📊 生成PDF偏差报表"])
        QTreeWidgetItem(report_item, ["📄 生成Klingelnberg报告"])
        ''', 
                                method_content, flags=re.DOTALL)
    
    # 替换原来的方法内容
    content = content.replace(method_content, new_method_content)

# 保存修改后的文件
with open('齿轮波纹度软件2_修改版_simplified.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("已创建简化版本文件: 齿轮波纹度软件2_修改版_simplified.py")
print("已重写左侧树形菜单，只保留文件操作、基础信息和报表工具节点")
