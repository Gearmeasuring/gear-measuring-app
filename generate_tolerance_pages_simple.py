import re

# 读取现有文件内容
file_path = 'gear_analysis_refactored/ui/tolerance_dialog.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 定义需要添加的标准
standards = [
    ("DIN 3962", "din3962"),
    ("AGMA", "agma"),
    ("ISO 1328 : 1997", "iso1328_1997"),
    ("ISO 1328 : 2013", "iso1328_2013"),  # 已存在，可能需要更新
    ("ANSI B92.1", "ansi_b921"),
    ("DIN 5480", "din5480")
]

# 1. 修改init_ui方法，添加所有标准的页面创建
def update_init_ui(content):
    # 找到init_ui方法中的页面创建部分
    init_ui_pattern = r'(def init_ui\(self\):\n[\s\S]*?# Create Pages\n[\s\S]*?)# Set default page'
    match = re.search(init_ui_pattern, content)
    if not match:
        return content
    
    # 生成新的页面创建代码
    new_pages_code = "        # Create Pages\n"
    
    for std_name, std_code in standards:
        new_pages_code += f"        self.create_{std_code}_profile_page()\n"
        new_pages_code += f"        self.create_{std_code}_lead_page()\n"
        new_pages_code += f"        self.create_{std_code}_spacing_page()\n"
    
    new_pages_code += "        self.create_empty_page() # Placeholder for others\n"
    
    # 替换原有代码
    return re.sub(init_ui_pattern, match.group(1) + new_pages_code, content)

# 2. 更新on_tree_item_clicked方法
def update_tree_item_clicked(content):
    # 找到on_tree_item_clicked方法
    tree_clicked_pattern = r'(def on_tree_item_clicked\(self, item, column\):\n[\s\S]*?)    def'
    match = re.search(tree_clicked_pattern, content)
    if not match:
        return content
    
    # 生成新的页面映射
    new_mapping = "        # Map IDs to stack indices\n"
    new_mapping += "        page_mapping = {\n"
    
    for i, (std_name, std_code) in enumerate(standards):
        profile_idx = i * 3
        lead_idx = i * 3 + 1
        spacing_idx = i * 3 + 2
        
        new_mapping += f"            \"{std_name}_Profile\": {profile_idx},\n"
        new_mapping += f"            \"{std_name}_Lead / Line of action\": {lead_idx},\n"
        new_mapping += f"            \"{std_name}_Spacing\": {spacing_idx},\n"
    
    # 添加默认页面
    new_mapping += f"            \"default\": {len(standards) * 3}\n"
    new_mapping += "        }\n"
    
    # 更新页面切换逻辑
    new_logic = ""
    new_logic += "        # Get page index from mapping\n"
    new_logic += "        if page_id in page_mapping:\n"
    new_logic += "            index = page_mapping[page_id]\n"
    new_logic += "            self.content_stack.setCurrentIndex(index)\n"
    new_logic += "            \n"
    new_logic += "            # Set window title based on page_id\n"
    new_logic += "            if \"Profile\" in page_id:\n"
    new_logic += "                standard = page_id.split(\"_\", 1)[0]\n"
    new_logic += "                self.setWindowTitle(f\"Tolerances acc.to {{{{standard}}}} Profile\")\n"
    new_logic += "            elif \"Lead\" in page_id:\n"
    new_logic += "                standard = page_id.split(\"_\", 1)[0]\n"
    new_logic += "                self.setWindowTitle(f\"Tolerances acc.to {{{{standard}}}} Lead\")\n"
    new_logic += "            elif \"Spacing\" in page_id:\n"
    new_logic += "                standard = page_id.split(\"_\", 1)[0]\n"
    new_logic += "                self.setWindowTitle(f\"Tolerances acc.to {{{{standard}}}} Spacing\")\n"
    new_logic += "            else:\n"
    new_logic += "                self.setWindowTitle(\"Tolerance Settings\")\n"
    new_logic += "        else:\n"
    new_logic += f"            self.content_stack.setCurrentIndex({len(standards) * 3})  # Empty page\n"
    new_logic += "            self.setWindowTitle(\"Tolerance Settings\")\n"
    
    # 构建新的方法内容
    old_method = match.group(1)
    # 移除旧的映射和逻辑
    old_method = re.sub(r'        # Map IDs to stack indices[\s\S]*?        self.setWindowTitle\(\"Tolerance Settings\"\)', 
                       new_mapping + new_logic, old_method)
    
    # 替换原有方法
    return re.sub(tree_clicked_pattern, old_method + '    def', content)

# 3. 复制ISO 1328:2013的页面方法作为模板，为每个标准创建页面
def add_new_pages(content):
    # 获取ISO 1328:2013的Profile页面作为模板
    profile_template_pattern = r'(def create_iso1328_2013_profile_page\(self\):[\s\S]*?)(?=def create_iso1328_2013_lead_page)'
    profile_match = re.search(profile_template_pattern, content)
    if not profile_match:
        return content
    profile_template = profile_match.group(1)
    
    # 获取ISO 1328:2013的Lead页面作为模板
    lead_template_pattern = r'(def create_iso1328_2013_lead_page\(self\):[\s\S]*?)(?=def create_iso1328_2013_spacing_page)'
    lead_match = re.search(lead_template_pattern, content)
    if not lead_match:
        return content
    lead_template = lead_match.group(1)
    
    # 获取ISO 1328:2013的Spacing页面作为模板
    spacing_template_pattern = r'(def create_iso1328_2013_spacing_page\(self\):[\s\S]*?)(?=def create_empty_page)'
    spacing_match = re.search(spacing_template_pattern, content)
    if not spacing_match:
        return content
    spacing_template = spacing_match.group(1)
    
    # 在create_empty_page方法前插入新的页面方法
    insert_point_pattern = r'(def create_empty_page\(self\):)'
    insert_point_match = re.search(insert_point_pattern, content)
    if not insert_point_match:
        return content
    insert_point = insert_point_match.start(1)
    
    # 为每个标准生成页面方法
    new_methods = ""
    for std_name, std_code in standards:
        if std_code == "iso1328_2013":
            continue  # 已存在
        
        # 创建Profile页面方法
        profile_method = profile_template.replace("iso1328_2013", std_code)
        profile_method = profile_method.replace("Tolerances acc.to DIN Profile", f"Tolerances acc.to {std_name} Profile")
        new_methods += profile_method
        
        # 创建Lead页面方法
        lead_method = lead_template.replace("iso1328_2013", std_code)
        lead_method = lead_method.replace("Tolerances acc.to DIN Lead", f"Tolerances acc.to {std_name} Lead")
        new_methods += lead_method
        
        # 创建Spacing页面方法
        spacing_method = spacing_template.replace("iso1328_2013", std_code)
        spacing_method = spacing_method.replace("Tolerances acc.to DIN Spacing", f"Tolerances acc.to {std_name} Spacing")
        new_methods += spacing_method
    
    # 插入新方法
    return content[:insert_point] + new_methods + content[insert_point:]

# 执行所有更新
content = update_init_ui(content)
content = update_tree_item_clicked(content)
content = add_new_pages(content)

# 保存更新后的内容
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated tolerance_dialog.py with pages for all standards")
