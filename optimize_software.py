import os
import re
import sys

# 齿轮波纹度软件精简优化脚本
def optimize_software(input_file, output_file):
    print(f"开始优化文件: {input_file}")
    
    # 读取原始文件
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"原始行数: {len(lines)}")
    
    # 1. 移除未使用的导入模块
    print("\n1. 优化导入模块...")
    
    # 需要保留的导入模块
    keep_imports = {
        'sys', 'os', 're', 'math', 'datetime', 'logging',
        'numpy', 'pandas', 'matplotlib', 'scipy',
        'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui',
        'reports.klingelnberg_single_page', 'ui.batch_processing_page'
    }
    
    # 移除未使用的导入
    optimized_lines = []
    in_import_section = True
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            optimized_lines.append(line)
            continue
            
        # 检查是否为导入行
        if in_import_section and (stripped_line.startswith('import ') or stripped_line.startswith('from ')):
            # 检查是否需要保留
            keep_line = False
            for keep_import in keep_imports:
                if keep_import in stripped_line:
                    keep_line = True
                    break
            
            if keep_line:
                optimized_lines.append(line)
            # 特殊处理需要保留的PyQt5模块
            elif 'PyQt5' in stripped_line:
                optimized_lines.append(line)
            else:
                print(f"  移除导入: {stripped_line}")
        else:
            if in_import_section and stripped_line and not stripped_line.startswith('#'):
                in_import_section = False
            optimized_lines.append(line)
    
    # 2. 移除未使用的类
    print("\n2. 移除未使用的类...")
    
    # 需要保留的类
    keep_classes = {
        'ChartMarkerHelper', 'ToleranceCalculatorDialog',
        'FileProcessingThread', 'RippleAnalysisThread',
        'RippleAnalysisDialog', 'Gear3DViewer', 'GearDataViewer'
    }
    
    # 找到所有类的定义和范围
    class_ranges = []
    current_class = None
    current_start = None
    
    for i, line in enumerate(optimized_lines):
        stripped_line = line.strip()
        if stripped_line.startswith('class '):
            if current_class:
                class_ranges.append((current_class, current_start, i))
            
            class_name = stripped_line.split()[1].split('(')[0]
            current_class = class_name
            current_start = i
    
    if current_class:
        class_ranges.append((current_class, current_start, len(optimized_lines)))
    
    # 创建新的行列表，移除不需要的类
    new_lines = []
    last_end = 0
    
    for class_name, start, end in class_ranges:
        if class_name in keep_classes:
            # 保留这个类
            new_lines.extend(optimized_lines[last_end:end])
        else:
            print(f"  移除类: {class_name} (第{start+1}行 - 第{end}行)")
        last_end = end
    
    # 添加剩余的行
    if last_end < len(optimized_lines):
        new_lines.extend(optimized_lines[last_end:])
    
    optimized_lines = new_lines
    
    # 3. 移除未使用的函数
    print("\n3. 移除未使用的函数...")
    
    # 需要保留的关键函数
    keep_functions = {
        'run', 'analyze_profile_ripple', 'analyze_flank_ripple', 
        'generate_order_analysis', 'generate', 'init_report_tab',
        'generate_topography_report', 'show_3d_gear_view', 'open_tolerance_calculator',
        'open_file', 'generate_html_report'
    }
    
    # 找到所有函数的定义和范围
    func_ranges = []
    current_func = None
    current_start = None
    indent_level = -1
    
    for i, line in enumerate(optimized_lines):
        stripped_line = line.strip()
        if stripped_line.startswith('def '):
            if current_func:
                func_ranges.append((current_func, current_start, i))
            
            func_name = stripped_line.split()[1].split('(')[0]
            current_func = func_name
            current_start = i
            indent_level = len(line) - len(stripped_line)
        elif current_func and stripped_line and not stripped_line.startswith('#'):
            # 检查缩进级别，判断是否为函数结束
            current_indent = len(line) - len(stripped_line)
            if current_indent <= indent_level:
                func_ranges.append((current_func, current_start, i))
                current_func = None
                indent_level = -1
    
    if current_func:
        func_ranges.append((current_func, current_start, len(optimized_lines)))
    
    # 创建新的行列表，移除不需要的函数
    new_lines = []
    last_end = 0
    
    for func_name, start, end in func_ranges:
        if func_name in keep_functions:
            # 保留这个函数
            new_lines.extend(optimized_lines[last_end:end])
        else:
            # 检查是否为类方法
            in_class = False
            for j in range(last_end, start):
                if optimized_lines[j].strip().startswith('class '):
                    in_class = True
                    break
            
            if in_class:
                # 如果是类方法，需要保留
                new_lines.extend(optimized_lines[last_end:end])
            else:
                print(f"  移除函数: {func_name} (第{start+1}行 - 第{end}行)")
        last_end = end
    
    # 添加剩余的行
    if last_end < len(optimized_lines):
        new_lines.extend(optimized_lines[last_end:])
    
    optimized_lines = new_lines
    
    # 4. 优化代码结构，移除重复初始化
    print("\n4. 优化代码结构...")
    
    # 移除重复的"初始化数据"注释
    optimized_content = '\n'.join(optimized_lines)
    optimized_content = re.sub(r'# 初始化数据\s*# 初始化数据', '# 初始化数据', optimized_content)
    
    # 5. 移除调试相关代码
    print("\n5. 移除调试代码...")
    
    # 移除调试日志
    optimized_content = re.sub(r'logger\.(debug|info)\([^)]*\)', '', optimized_content)
    
    # 6. 移除未使用的变量和代码块
    print("\n6. 移除未使用的变量和代码块...")
    
    # 移除未使用的数据变量
    unused_data_vars = [
        'self.undulation_results', 'self.deviation_results', 'self.pitch_results',
        'self.current_detail', 'self.base_diameter', 'self.reconstruction_thread'
    ]
    
    for var in unused_data_vars:
        pattern = rf'self\.{var.split("self.")[-1]}\s*=\s*[^\n]*'
        optimized_content = re.sub(pattern, '', optimized_content)
    
    # 7. 简化状态栏和自动隐藏功能
    print("\n7. 简化UI功能...")
    
    # 移除自动隐藏相关代码
    auto_hide_patterns = [
        r'self\._nav_auto_hide_\w+\s*=\s*[^\n]*',
        r'self\._nav_auto_hide_timer\s*=\s*[^\n]*'
    ]
    
    for pattern in auto_hide_patterns:
        optimized_content = re.sub(pattern, '', optimized_content)
    
    # 8. 移除处理步骤对话框相关代码
    print("\n8. 移除处理步骤对话框...")
    
    # 移除ProcessingStepsDialog类
    optimized_content = re.sub(
        r'class ProcessingStepsDialog\(QDialog\):[\s\S]*?def __init__\([^)]*\):[\s\S]*?def setupUi\([^)]*\):[\s\S]*?(?=class|def|$)',
        '', optimized_content
    )
    
    # 9. 优化性能，移除冗余的日志记录
    print("\n9. 优化性能...")
    
    # 移除冗余的日志记录
    redundant_logs = [
        r'logger\.warning\([^)]*软件保护系统[^)]*\)',
        r'logger\.info\([^)]*创建主窗口[^)]*\)'
    ]
    
    for pattern in redundant_logs:
        optimized_content = re.sub(pattern, '', optimized_content)
    
    # 10. 最终清理，移除空行
    print("\n10. 清理空行...")
    
    # 移除连续的空行
    optimized_content = re.sub(r'\n\s*\n\s*\n', '\n\n', optimized_content)
    
    # 统计最终行数
    final_lines = optimized_content.split('\n')
    print(f"\n优化后行数: {len(final_lines)}")
    print(f"减少行数: {len(lines) - len(final_lines)}")
    print(f"优化比例: {(1 - len(final_lines)/len(lines)):.2%}")
    
    # 保存优化后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(optimized_content)
    
    print(f"\n优化完成！保存到: {output_file}")

# 执行优化
if __name__ == "__main__":
    input_file = "齿轮波纹度软件2_修改版_simplified.py"
    output_file = "齿轮波纹度软件2_优化版.py"
    
    if os.path.exists(input_file):
        optimize_software(input_file, output_file)
    else:
        print(f"文件不存在: {input_file}")
