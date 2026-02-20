import os
import re
import sys

# 齿轮波纹度软件精简优化脚本（版本2）
def optimize_software(input_file, output_file):
    print(f"开始优化文件: {input_file}")
    
    # 读取原始文件
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"原始行数: {len(lines)}")
    
    # 定义核心功能区域的行范围
    # 这些是必须保留的主要功能区域
    core_sections = [
        # 导入部分
        (1, 200),
        # ChartMarkerHelper类
        (90, 130),
        # ToleranceCalculatorDialog类
        (310, 500),
        # FileProcessingThread类
        (480, 580),
        # RippleAnalysisThread类
        (1850, 2050),
        # RippleAnalysisDialog类
        (2480, 2600),
        # AnalysisSettingsDialog类
        (2820, 2950),
        # Gear3DViewer类
        (5450, 5600),
        # GearDataViewer类（核心主类）
        (5700, 9500),
        # CustomFigureCanvas类
        (22090, 22300)
    ]
    
    # 1. 保留核心功能区域
    print("\n1. 保留核心功能区域...")
    
    optimized_lines = []
    current_line = 1
    
    for start, end in core_sections:
        # 添加区间前的空行以保持结构
        if start > current_line + 1:
            optimized_lines.append('')
        
        # 添加核心区域内容
        section_lines = lines[start-1:end]
        optimized_lines.extend(section_lines)
        current_line = end + 1
    
    # 2. 移除未使用的导入模块
    print("\n2. 优化导入模块...")
    
    optimized_content = '\n'.join(optimized_lines)
    
    # 定义需要保留的导入模块
    required_imports = [
        'import sys',
        'import os',
        'import re',
        'import logging',
        'import numpy as np',
        'import math',
        'import datetime',
        'import pandas as pd',
        'from PyQt5.QtWidgets import',
        'from PyQt5.QtCore import',
        'from PyQt5.QtGui import',
        'import matplotlib',
        'from matplotlib.backends.backend_qt5agg import',
        'from matplotlib.figure import',
        'import matplotlib.pyplot as plt',
        'from scipy.signal import',
        'from scipy.ndimage import',
        'from matplotlib.backends.backend_pdf import',
        'from mpl_toolkits.mplot3d import',
        'from scipy.interpolate import',
        'from reports.klingelnberg_single_page import KlingelnbergSinglePageReport',
        'from ui.batch_processing_page import BatchProcessingPage'
    ]
    
    # 提取实际的导入行
    import_lines = []
    for line in optimized_lines:
        stripped_line = line.strip()
        if stripped_line.startswith('import ') or stripped_line.startswith('from '):
            # 检查是否需要保留
            keep_line = False
            for required in required_imports:
                if required.split()[0] in stripped_line:
                    keep_line = True
                    break
            
            if keep_line:
                import_lines.append(line)
    
    # 3. 重构文件结构
    print("\n3. 重构文件结构...")
    
    # 创建新的文件内容
    new_content = []
    
    # 添加必要的导入
    new_content.extend(import_lines)
    new_content.append('')
    
    # 添加CHART_COLORS和ORDER_COLORS常量
    new_content.append('# Professional color scheme for charts')
    new_content.append('CHART_COLORS = {')
    new_content.append('    \'primary\': \'#2E86AB\',      # Professional blue')
    new_content.append('    \'secondary\': \'#A23B72\',    # Accent purple')
    new_content.append('    \'success\': \'#06A77D\',      # Success green')
    new_content.append('    \'warning\': \'#F18F01\',      # Warning orange')
    new_content.append('    \'danger\': \'#C73E1D\',       # Error red')
    new_content.append('    \'neutral\': \'#6C757D\',      # Neutral gray')
    new_content.append('    \'light\': \'#E9ECEF\',        # Light background')
    new_content.append('    \'dark\': \'#212529\',         # Dark text')
    new_content.append('}')
    new_content.append('')
    new_content.append('# Chart-specific colors for order analysis and reports')
    new_content.append('ORDER_COLORS = {')
    new_content.append('    \'default_bar\': \'#5DADE2\',      # Light blue for normal bars')
    new_content.append('    \'highlight_bar\': \'#E74C3C\',    # Red for important bars')
    new_content.append('    \'reference_line\': \'#27AE60\',   # Green for reference lines')
    new_content.append('    \'grid\': \'#BDC3C7\',             # Light gray for grid')
    new_content.append('}')
    new_content.append('')
    
    # 添加必要的函数
    new_content.append('def create_gear_data_structure():')
    new_content.append('    """Create empty gear measurement data structure."""')
    new_content.append('    return {\'left\': {}, \'right\': {}}')
    new_content.append('')
    
    # 添加核心类定义
    class_content = []
    in_class = False
    class_name = None
    
    for line in optimized_lines:
        stripped_line = line.strip()
        
        # 检查类定义
        if stripped_line.startswith('class '):
            class_name = stripped_line.split()[1].split('(')[0]
            in_class = True
            class_content.append(line)
        elif in_class and stripped_line and not stripped_line.startswith('    '):
            # 类结束，保存内容
            if class_name in ['ChartMarkerHelper', 'ToleranceCalculatorDialog', 'FileProcessingThread', 
                              'RippleAnalysisThread', 'RippleAnalysisDialog', 'AnalysisSettingsDialog',
                              'Gear3DViewer', 'GearDataViewer', 'CustomFigureCanvas']:
                new_content.append('')
                new_content.extend(class_content)
                print(f"  保留类: {class_name}")
            class_content = []
            in_class = False
        elif in_class:
            class_content.append(line)
    
    # 处理最后一个类
    if class_content and class_name:
        if class_name in ['ChartMarkerHelper', 'ToleranceCalculatorDialog', 'FileProcessingThread', 
                          'RippleAnalysisThread', 'RippleAnalysisDialog', 'AnalysisSettingsDialog',
                          'Gear3DViewer', 'GearDataViewer', 'CustomFigureCanvas']:
            new_content.append('')
            new_content.extend(class_content)
            print(f"  保留类: {class_name}")
    
    # 4. 清理和优化代码
    print("\n4. 清理和优化代码...")
    
    final_content = '\n'.join(new_content)
    
    # 移除重复的初始化数据
    final_content = re.sub(r'# 初始化数据\s*# 初始化数据', '# 初始化数据', final_content)
    
    # 移除未使用的变量
    final_content = re.sub(r'self\._nav_auto_hide_\w+\s*=\s*[^\n]*', '', final_content)
    final_content = re.sub(r'self\.reconstruction_thread\s*=\s*[^\n]*', '', final_content)
    final_content = re.sub(r'self\.undulation_results\s*=\s*[^\n]*', '', final_content)
    final_content = re.sub(r'self\.deviation_results\s*=\s*[^\n]*', '', final_content)
    final_content = re.sub(r'self\.pitch_results\s*=\s*[^\n]*', '', final_content)
    
    # 移除调试日志
    final_content = re.sub(r'logger\.(debug|info)\([^)]*\)', '', final_content)
    
    # 移除冗余的代码
    final_content = re.sub(r'\s*self\.protection_manager\s*=\s*None\s*', '', final_content)
    
    # 清理空行
    final_content = re.sub(r'\n\s*\n\s*\n', '\n\n', final_content)
    
    # 5. 统计优化结果
    final_lines = final_content.split('\n')
    print(f"\n优化后行数: {len(final_lines)}")
    print(f"减少行数: {len(lines) - len(final_lines)}")
    print(f"优化比例: {(1 - len(final_lines)/len(lines)):.2%}")
    
    # 6. 保存优化后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"\n优化完成！保存到: {output_file}")

# 执行优化
if __name__ == "__main__":
    input_file = "齿轮波纹度软件2_修改版_simplified.py"
    output_file = "齿轮波纹度软件2_优化版_v2.py"
    
    if os.path.exists(input_file):
        optimize_software(input_file, output_file)
    else:
        print(f"文件不存在: {input_file}")
