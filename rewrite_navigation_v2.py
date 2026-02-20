# 重写create_floating_navigation方法，只保留特定节点

# 读取原始文件
with open('齿轮波纹度软件2_修改版.py.before_915_points20251127.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 定义要替换的旧代码和新代码
old_code = '''        # 添加树形节点
        root = QTreeWidgetItem(self.nav_tree_widget, ["功能导航"])
        
        # 第一级节点 - 按分析类型重新分类
        file_item = QTreeWidgetItem(root, ["📁 文件操作"])
        basic_item = QTreeWidgetItem(root, ["📊 基础信息"])
        curve_item = QTreeWidgetItem(root, ["📈 曲线分析"])
        spectrum_item = QTreeWidgetItem(root, ["🔬 频谱分析"])
        deviation_item = QTreeWidgetItem(root, ["📋 偏差分析"])
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
        
        # 第二级节点 (曲线分析)
        QTreeWidgetItem(curve_item, ["📈 齿形曲线分析"])
        QTreeWidgetItem(curve_item, ["📉 齿向曲线分析"])
        QTreeWidgetItem(curve_item, ["📊 分组折线图"])
        
        # 第二级节点 (频谱分析)
        QTreeWidgetItem(spectrum_item, ["📊 原始阶次分析"])
        QTreeWidgetItem(spectrum_item, ["📊 归一化阶次分析"])
        QTreeWidgetItem(spectrum_item, ["📊 周节阶次分析"])
        QTreeWidgetItem(spectrum_item, ["📊 专业阶次分析"])
        
        # 第二级节点 (偏差分析)
        QTreeWidgetItem(deviation_item, ["📋 ISO1328偏差"])
        QTreeWidgetItem(deviation_item, ["📊 Ripple分析"])
        QTreeWidgetItem(deviation_item, ["📊 周节偏差分析"])
        QTreeWidgetItem(deviation_item, ["🌊 旋转角波纹度"])
        
        # 第二级节点 (报表工具)
        QTreeWidgetItem(report_item, ["📊 生成PDF偏差报表"])
        QTreeWidgetItem(report_item, ["📄 生成Klingelnberg报告"])
        QTreeWidgetItem(report_item, ["🧮 公差计算器"])'''

new_code = '''        # 添加树形节点
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
        QTreeWidgetItem(report_item, ["🧮 公差计算器"])'''

# 替换代码
content = content.replace(old_code, new_code)

# 保存修改后的文件
with open('齿轮波纹度软件2_修改版_simplified.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("已创建简化版本文件: 齿轮波纹度软件2_修改版_simplified.py")
print("已删除左侧树形菜单中曲线分析、频谱分析和偏差分析节点")
