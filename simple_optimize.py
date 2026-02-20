import os
import re

# 简单优化脚本 - 直接修复原始文件中的冗余代码
def simple_optimize(input_file, output_file):
    print(f"开始简单优化: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"原始行数: {len(lines)}")
    
    # 1. 修复导入语法错误
    print("\n1. 修复导入语法错误...")
    
    # 找到并修复不完整的PyQt5导入
    content = re.sub(r'from PyQt5\.QtWidgets import \(', 
                     'from PyQt5.QtWidgets import (\n    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QStackedWidget,\n    QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QMessageBox,\n    QLabel, QHeaderView, QAbstractItemView, QStatusBar, QAction, QTreeWidget, QTreeWidgetItem,\n    QTextEdit, QProgressBar, QDialog, QGroupBox, QFormLayout, QScrollArea,\n    QFrame, QGridLayout, QSizePolicy, QComboBox, QLineEdit, QDialogButtonBox, QSpinBox, QCheckBox,\n    QSplitter, QMenu', content)
    
    # 2. 移除重复的导入
    print("\n2. 移除重复的导入...")
    
    # 移除重复的导入块
    content = re.sub(r'import re\s*import os\s*import logging\s*import numpy as np\s*import math\s*import datetime', 
                     '', content)
    
    # 3. 移除重复的字体配置和日志配置
    print("\n3. 移除重复的配置代码...")
    
    # 移除重复的字体配置
    font_config_pattern = r'try:\s*\s*import matplotlib.font_manager as fm\s*import logging\s*\s*# 根据系统类型设置字体\s*if platform.system\(\) == \'Windows\':\s*[\s\S]*?except Exception as e:\s*print\(f"字体配置警告: {e}\"\)\s*mpl\.rcParams\[\'font\.sans-serif\'\] = \[\'SimHei\', \'DejaVu Sans\'\]\s*mpl\.rcParams\[\'axes\.unicode_minus\'\] = False'
    
    # 找到第一个字体配置块并保留，移除其他
    matches = list(re.finditer(font_config_pattern, content))
    if matches:
        # 保留第一个配置块
        first_config = matches[0].group(0)
        
        # 移除所有配置块
        content = re.sub(font_config_pattern, '', content)
        
        # 重新添加第一个配置块到合适位置
        import_end_pos = content.find('from ui.batch_processing_page import BatchProcessingPage')
        if import_end_pos != -1:
            content = content[:import_end_pos + 50] + '\n\n' + first_config + '\n' + content[import_end_pos + 50:]
    
    # 移除重复的日志配置
    log_config_pattern = r'logger = logging\.getLogger\(\'GearDataViewer\'\)\s*logger\.setLevel\(logging\.DEBUG\)\s*\s*# 创建文件处理器，并设置编码为utf-8\s*try:\s*file_handler = logging\.FileHandler\(\'gear_viewer\.log\', encoding=\'utf-8\'\)\s*except TypeError:\s*file_handler = logging\.FileHandler\(\'gear_viewer\.log\'\)\s*file_handler\.encoding = \'utf-8\'\s*\s*file_handler\.setLevel\(logging\.DEBUG\)\s*console_handler = logging\.StreamHandler\(\)\s*console_handler\.setLevel\(logging\.INFO\)\s*formatter = logging\.Formatter\(\'%(asctime)s - %(name)s - %(levelname)s - %(message)s\'\)\s*file_handler\.setFormatter\(formatter\)\s*console_handler\.setFormatter\(formatter\)\s*logger\.addHandler\(file_handler\)\s*logger\.addHandler\(console_handler\)'
    
    matches = list(re.finditer(log_config_pattern, content))
    if matches:
        # 保留第一个日志配置块
        first_log_config = matches[0].group(0)
        
        # 移除所有日志配置块
        content = re.sub(log_config_pattern, '', content)
        
        # 重新添加第一个日志配置块到合适位置
        if 'font_config_pattern' in locals() and import_end_pos != -1:
            content = content[:import_end_pos + 50 + len(first_config) + 2] + '\n' + first_log_config + '\n' + content[import_end_pos + 50 + len(first_config) + 2:]
    
    # 4. 移除未使用的变量初始化
    print("\n4. 移除未使用的变量初始化...")
    
    # 移除未使用的数据变量
    unused_vars = [
        r'self\.undulation_results\s*=\s*None',
        r'self\.deviation_results\s*=\s*None',
        r'self\.pitch_results\s*=\s*None',
        r'self\.current_detail\s*=\s*None',
        r'self\.base_diameter\s*=\s*0\.0',
        r'self\.reconstruction_thread\s*=\s*None',
        r'self\._nav_auto_hide_timer\s*=\s*None',
        r'self\._nav_auto_hide_enabled\s*=\s*True',
        r'self\._nav_expanded_width\s*=\s*300',
        r'self\._nav_collapsed_width\s*=\s*30'
    ]
    
    for var_pattern in unused_vars:
        content = re.sub(var_pattern, '', content)
    
    # 5. 移除重复的"初始化数据"注释
    print("\n5. 移除重复的注释...")
    content = re.sub(r'# 初始化数据\s*# 初始化数据', '# 初始化数据', content)
    
    # 6. 移除调试日志
    print("\n6. 移除调试日志...")
    content = re.sub(r'logger\.debug\([^)]*\)', '', content)
    
    # 7. 移除未使用的方法
    print("\n7. 移除未使用的方法...")
    
    # 移除show_processing_steps方法
    content = re.sub(r'def show_processing_steps\(self\):\s*\s*self\.processing_steps_dialog = ProcessingStepsDialog\(self\)\s*self\.processing_steps_dialog\.exec_\(\)', 
                     '', content)
    
    # 移除未使用的工具栏动作启用代码
    content = re.sub(r'self\.(settings_action|run_all_action|html_report_action)\.setEnabled\(False\)', '', content)
    
    # 8. 清理空行
    print("\n8. 清理空行...")
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    # 统计最终结果
    final_lines = content.split('\n')
    print(f"\n优化后行数: {len(final_lines)}")
    print(f"减少行数: {len(lines) - len(final_lines)}")
    print(f"优化比例: {(1 - len(final_lines)/len(lines)):.2%}")
    
    # 保存优化后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n优化完成！保存到: {output_file}")

# 执行优化
if __name__ == "__main__":
    input_file = "齿轮波纹度软件2_修改版_simplified.py"
    output_file = "齿轮波纹度软件2_优化版_final.py"
    
    if os.path.exists(input_file):
        simple_optimize(input_file, output_file)
    else:
        print(f"文件不存在: {input_file}")
