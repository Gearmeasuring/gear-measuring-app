import os
import re

# 智能优化脚本 - 精确优化齿轮波纹度软件
def smart_optimize(input_file, output_file):
    print(f"开始智能优化: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"原始行数: {len(lines)}")
    
    # 1. 清理导入模块
    print("\n1. 清理导入模块...")
    
    # 定义需要保留的导入
    keep_imports = [
        'sys', 'os', 're', 'logging', 'numpy as np', 'math', 'datetime',
        'pandas as pd', 'collections.defaultdict',
        'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui',
        'matplotlib', 'matplotlib.pyplot as plt',
        'scipy.signal', 'scipy.ndimage', 'scipy.interpolate',
        'matplotlib.backends.backend_qt5agg', 'matplotlib.figure',
        'matplotlib.backends.backend_pdf', 'mpl_toolkits.mplot3d',
        'reports.klingelnberg_single_page.KlingelnbergSinglePageReport',
        'ui.batch_processing_page.BatchProcessingPage'
    ]
    
    # 提取导入行
    import_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            keep = False
            for keep_import in keep_imports:
                if keep_import in stripped:
                    keep = True
                    break
            
            if keep:
                import_lines.append(line)
    
    # 2. 保留核心数据结构和常量
    print("\n2. 保留核心数据结构和常量...")
    
    core_data = [
        'def create_gear_data_structure():',
        '    """Create empty gear measurement data structure."""',
        '    return {\'left\': {}, \'right\': {}}',
        '',
        '# Professional color scheme for charts',
        'CHART_COLORS = {',
        '    \'primary\': \'#2E86AB\',      # Professional blue',
        '    \'secondary\': \'#A23B72\',    # Accent purple',
        '    \'success\': \'#06A77D\',      # Success green',
        '    \'warning\': \'#F18F01\',      # Warning orange',
        '    \'danger\': \'#C73E1D\',       # Error red',
        '    \'neutral\': \'#6C757D\',      # Neutral gray',
        '    \'light\': \'#E9ECEF\',        # Light background',
        '    \'dark\': \'#212529\',         # Dark text',
        '}',
        '',
        '# Chart-specific colors for order analysis and reports',
        'ORDER_COLORS = {',
        '    \'default_bar\': \'#5DADE2\',      # Light blue for normal bars',
        '    \'highlight_bar\': \'#E74C3C\',    # Red for important bars',
        '    \'reference_line\': \'#27AE60\',   # Green for reference lines',
        '    \'grid\': \'#BDC3C7\',             # Light gray for grid',
        '}'
    ]
    
    # 3. 提取核心类定义
    print("\n3. 提取核心类定义...")
    
    class_pattern = r'^\s*class\s+([\w]+)\([^)]*\):'
    class_ranges = []
    core_classes = []
    
    current_class = None
    class_start = None
    
    for i, line in enumerate(lines):
        match = re.match(class_pattern, line)
        if match:
            if current_class:
                class_ranges.append((current_class, class_start, i))
            current_class = match.group(1)
            class_start = i
    
    if current_class:
        class_ranges.append((current_class, class_start, len(lines)))
    
    # 保留核心类
    keep_classes = ['ChartMarkerHelper', 'ToleranceCalculatorDialog', 'FileProcessingThread',
                    'RippleAnalysisThread', 'RippleAnalysisDialog', 'AnalysisSettingsDialog',
                    'Gear3DViewer', 'GearDataViewer', 'CustomFigureCanvas']
    
    class_contents = {}
    
    for class_name, start, end in class_ranges:
        if class_name in keep_classes:
            class_content = lines[start:end]
            class_contents[class_name] = class_content
            core_classes.append(class_name)
            print(f"  提取类: {class_name} ({end-start}行)")
    
    # 4. 清理GearDataViewer类中的冗余代码
    print("\n4. 清理GearDataViewer类...")
    
    if 'GearDataViewer' in class_contents:
        gear_viewer_lines = class_contents['GearDataViewer']
        optimized_gear_viewer = []
        
        # 需要移除的方法和属性
        remove_methods = ['show_processing_steps', 'generate_html_report', 'generate_order_analysis',
                         'show_deviation_analysis', 'analyze_pitch_data', 'open_tolerance_calculator',
                         'init_report_tab', 'generate_topography_report']
        
        # 需要移除的属性初始化
        remove_attrs = ['self.undulation_results', 'self.deviation_results', 'self.pitch_results',
                       'self.current_detail', 'self.base_diameter', 'self.reconstruction_thread',
                       'self._nav_auto_hide_timer', 'self._nav_auto_hide_enabled',
                       'self._nav_expanded_width', 'self._nav_collapsed_width']
        
        in_remove_method = False
        method_name = None
        
        for line in gear_viewer_lines:
            stripped = line.strip()
            
            # 检查方法定义
            if stripped.startswith('def '):
                method_name = stripped.split()[1].split('(')[0]
                in_remove_method = method_name in remove_methods
                
            # 检查属性初始化
            attr_removed = False
            for attr in remove_attrs:
                if attr in stripped and '=' in stripped:
                    attr_removed = True
                    break
            
            if not in_remove_method and not attr_removed:
                # 清理重复的"初始化数据"注释
                if stripped == '# 初始化数据':
                    if optimized_gear_viewer and optimized_gear_viewer[-1].strip() == '# 初始化数据':
                        continue
                optimized_gear_viewer.append(line)
            
        class_contents['GearDataViewer'] = optimized_gear_viewer
    
    # 5. 构建优化后的文件内容
    print("\n5. 构建优化后的文件...")
    
    optimized_content = []
    
    # 添加导入
    optimized_content.extend(import_lines)
    optimized_content.append('')
    
    # 添加核心数据结构
    optimized_content.extend(core_data)
    optimized_content.append('')
    
    # 添加核心类
    for class_name in core_classes:
        if class_name in class_contents:
            optimized_content.append('')
            optimized_content.extend(class_contents[class_name])
    
    # 6. 最终清理
    print("\n6. 最终清理...")
    
    final_text = '\n'.join(optimized_content)
    
    # 移除多余的空行
    final_text = re.sub(r'\n\s*\n\s*\n', '\n\n', final_text)
    
    # 移除调试日志
    final_text = re.sub(r'logger\.(debug|info)\([^)]*\);?', '', final_text)
    
    # 修复可能的语法问题
    final_text = re.sub(r'\s*;\s*', '', final_text)  # 移除多余的分号
    
    final_lines = final_text.split('\n')
    print(f"优化后行数: {len(final_lines)}")
    print(f"减少行数: {len(lines) - len(final_lines)}")
    print(f"优化比例: {(1 - len(final_lines)/len(lines)):.2%}")
    
    # 保存优化后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_text)
    
    print(f"\n优化完成！保存到: {output_file}")

# 执行优化
if __name__ == "__main__":
    input_file = "齿轮波纹度软件2_修改版_simplified.py"
    output_file = "齿轮波纹度软件2_优化版.py"
    
    if os.path.exists(input_file):
        smart_optimize(input_file, output_file)
    else:
        print(f"文件不存在: {input_file}")
