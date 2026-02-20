#!/usr/bin/env python3
"""
检查模块路径和导入机制，确保正确加载波纹度频谱分析模块
"""
import os
import sys

# 打印当前工作目录
print(f"当前工作目录: {os.getcwd()}")

# 打印 Python 路径
print("\nPython 路径:")
for i, path in enumerate(sys.path):
    print(f"{i}: {path}")

# 尝试导入模块
try:
    # 直接导入模块文件，绕过 __init__.py
    print("\n尝试直接导入模块文件:")
    module_path = 'gear_analysis_refactored.reports.klingelnberg_ripple_spectrum'
    
    # 动态导入模块
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        module_path,
        os.path.join('gear_analysis_refactored', 'reports', 'klingelnberg_ripple_spectrum.py')
    )
    klingelnberg_ripple_spectrum = importlib.util.module_from_spec(spec)
    sys.modules[module_path] = klingelnberg_ripple_spectrum
    spec.loader.exec_module(klingelnberg_ripple_spectrum)
    
    print(f"✓ 成功导入 {module_path}")
    print(f"模块文件路径: {os.path.abspath('gear_analysis_refactored/reports/klingelnberg_ripple_spectrum.py')}")
    
    # 检查模块中的类
    if hasattr(klingelnberg_ripple_spectrum, 'KlingelnbergRippleSpectrumReport'):
        print("✓ 模块包含 KlingelnbergRippleSpectrumReport 类")
    else:
        print("✗ 模块不包含 KlingelnbergRippleSpectrumReport 类")
        
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()

# 检查是否存在重复模块
duplicate_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file == 'klingelnberg_ripple_spectrum.py':
            full_path = os.path.join(root, file)
            duplicate_files.append(full_path)

print("\n找到的 klingelnberg_ripple_spectrum.py 文件:")
for i, file_path in enumerate(duplicate_files):
    print(f"{i+1}: {file_path}")

# 检查 klingelnberg_single_page.py 文件
single_page_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file == 'klingelnberg_single_page.py':
            full_path = os.path.join(root, file)
            single_page_files.append(full_path)

print("\n找到的 klingelnberg_single_page.py 文件:")
for i, file_path in enumerate(single_page_files):
    print(f"{i+1}: {file_path}")
