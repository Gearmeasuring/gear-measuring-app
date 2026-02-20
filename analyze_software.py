import os
import re
import ast

# 分析齿轮波纹度软件文件
def analyze_software_file(file_path):
    print(f"分析文件: {file_path}")
    print("=" * 60)
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 基本统计
    lines = content.split('\n')
    total_lines = len(lines)
    code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
    comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
    
    print(f"总行数: {total_lines}")
    print(f"代码行数: {code_lines}")
    print(f"注释行数: {comment_lines}")
    print(f"代码比例: {code_lines/total_lines:.2%}")
    print()
    
    # 分析导入模块
    print("导入模块分析:")
    import_pattern = r'^(import|from)\s+([\w\.]+)'
    imports = set()
    for line in lines:
        match = re.match(import_pattern, line.strip())
        if match:
            imports.add(match.group(2))
    
    print("直接导入:", sorted(imports))
    print(f"总导入模块数: {len(imports)}")
    print()
    
    # 分析类定义
    print("类定义分析:")
    class_pattern = r'^\s*class\s+([\w]+)'
    classes = []
    for i, line in enumerate(lines):
        match = re.match(class_pattern, line.strip())
        if match:
            classes.append((match.group(1), i+1))
    
    for class_name, line_num in classes:
        print(f"  {class_name} (第{line_num}行)")
    print(f"总类数: {len(classes)}")
    print()
    
    # 分析主要功能函数
    print("主要功能函数分析:")
    func_pattern = r'^\s*def\s+(\w+)\('
    funcs = []
    for i, line in enumerate(lines):
        match = re.match(func_pattern, line.strip())
        if match:
            funcs.append((match.group(1), i+1))
    
    # 只显示部分关键函数
    key_funcs = [f for f in funcs if any(keyword in f[0] for keyword in 
                                         ['open', 'analyze', 'report', 'view', 'run', 'generate'])]
    
    print("关键功能函数:")
    for func_name, line_num in key_funcs[:20]:  # 只显示前20个
        print(f"  {func_name} (第{line_num}行)")
    if len(key_funcs) > 20:
        print(f"  ... 还有 {len(key_funcs) - 20} 个函数")
    
    print(f"总函数数: {len(funcs)}")
    print()
    
    # 分析工具栏和菜单创建
    print("UI组件分析:")
    toolbar_pattern = r'addAction\(self\.(\w+_action)\)'
    actions = set()
    for match in re.finditer(toolbar_pattern, content):
        actions.add(match.group(1))
    
    print("工具栏和菜单动作:", sorted(actions))
    print(f"总动作数: {len(actions)}")
    
    return {
        'total_lines': total_lines,
        'code_lines': code_lines,
        'comment_lines': comment_lines,
        'imports': imports,
        'classes': classes,
        'functions': funcs,
        'actions': actions
    }

# 执行分析
if __name__ == "__main__":
    file_path = "齿轮波纹度软件2_修改版_simplified.py"
    if os.path.exists(file_path):
        analyze_software_file(file_path)
    else:
        print(f"文件不存在: {file_path}")
