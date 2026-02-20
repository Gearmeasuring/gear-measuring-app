import os
import re

# 基于行范围的精确优化脚本
def range_optimize(input_file, output_file):
    print(f"开始基于行范围的精确优化: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"原始行数: {len(lines)}")
    
    # 定义需要保留的行范围（根据文件结构分析）
    keep_ranges = [
        (1, 200),    # 导入部分
        (200, 300),  # 核心数据结构和常量
        (300, 500),  # ToleranceCalculatorDialog类
        (500, 1200), # FileProcessingThread类
        (1200, 1850),# RippleAnalysisThread类
        (1850, 2500),# RippleAnalysisDialog类
        (2500, 2950),# AnalysisSettingsDialog类
        (5450, 5600),# Gear3DViewer类
        (5700, 9500),# GearDataViewer类（核心功能）
        (22090, 22300)# CustomFigureCanvas类
    ]
    
    # 提取保留的行
    optimized_lines = []
    
    for start, end in keep_ranges:
        # 确保范围在有效行内
        start_idx = max(0, start - 1)
        end_idx = min(len(lines), end)
        
        # 添加范围内容
        optimized_lines.extend(lines[start_idx:end_idx])
        # 添加空行分隔
        optimized_lines.append('')
    
    # 清理重复的空行
    final_lines = []
    prev_empty = False
    
    for line in optimized_lines:
        if line.strip() == '':
            if not prev_empty:
                final_lines.append(line)
                prev_empty = True
        else:
            final_lines.append(line)
            prev_empty = False
    
    # 修复导入语法
    final_content = '\n'.join(final_lines)
    
    # 确保PyQt5导入完整
    final_content = re.sub(r'from PyQt5\.QtWidgets import \(', 
                     'from PyQt5.QtWidgets import (\n    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QStackedWidget,\n    QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QMessageBox,\n    QLabel, QHeaderView, QAbstractItemView, QStatusBar, QAction, QTreeWidget, QTreeWidgetItem,\n    QTextEdit, QProgressBar, QDialog, QGroupBox, QFormLayout, QScrollArea,\n    QFrame, QGridLayout, QSizePolicy, QComboBox, QLineEdit, QDialogButtonBox, QSpinBox, QCheckBox,\n    QSplitter, QMenu', final_content)
    
    # 移除未使用的变量
    unused_vars = [
        r'self\.undulation_results\s*=\s*None',
        r'self\.deviation_results\s*=\s*None',
        r'self\.pitch_results\s*=\s*None',
        r'self\.current_detail\s*=\s*None',
        r'self\.base_diameter\s*=\s*0\.0',
        r'self\.reconstruction_thread\s*=\s*None',
        r'self\._nav_auto_hide_\w+\s*=\s*[^\n]*'
    ]
    
    for var in unused_vars:
        final_content = re.sub(var, '', final_content)
    
    # 移除调试日志
    final_content = re.sub(r'logger\.(debug|info)\([^)]*\)', '', final_content)
    
    # 移除重复的初始化注释
    final_content = re.sub(r'# 初始化数据\s*# 初始化数据', '# 初始化数据', final_content)
    
    # 统计结果
    final_lines_list = final_content.split('\n')
    print(f"\n优化后行数: {len(final_lines_list)}")
    print(f"减少行数: {len(lines) - len(final_lines_list)}")
    print(f"优化比例: {(1 - len(final_lines_list)/len(lines)):.2%}")
    
    # 保存优化后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"\n优化完成！保存到: {output_file}")

# 执行优化
if __name__ == "__main__":
    input_file = "齿轮波纹度软件2_修改版_simplified.py"
    output_file = "齿轮波纹度软件2_优化版_final.py"
    
    if os.path.exists(input_file):
        range_optimize(input_file, output_file)
    else:
        print(f"文件不存在: {input_file}")
