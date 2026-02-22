#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从备份文件中恢复完整的 ToleranceSettingsDialog 类
"""

try:
    # 读取 .bak_final 备份文件内容
    print("正在读取完整备份文件...")
    with open('tolerance_dialog.py.bak_final', 'r', encoding='utf-8', errors='ignore') as f:
        backup_content = f.read()
    
    print(f"备份文件总长度: {len(backup_content)} 字符")
    
    # 找到类定义的开始位置
    class_start = backup_content.find('class ToleranceSettingsDialog')
    if class_start == -1:
        print("错误：未找到类定义")
        exit(1)
    
    print(f"类定义开始位置: {class_start}")
    
    # 找到类定义的结束位置（最后一个方法结束后）
    # 我们需要找到文件的末尾，因为类可能包含很多方法
    class_end = len(backup_content)
    
    # 提取完整的类定义
    complete_class = backup_content[class_start:class_end]
    print(f"提取的类定义长度: {len(complete_class)} 字符")
    
    # 验证提取的类是否完整
    if 'class ToleranceSettingsDialog' not in complete_class:
        print("错误：提取的类定义不完整")
        exit(1)
    
    # 找到导入语句的开始位置（文件开头到类定义前）
    imports_part = backup_content[:class_start]
    
    # 组合完整的文件内容：导入语句 + 类定义
    complete_file = imports_part + complete_class
    
    # 写回主文件
    print("\n正在恢复完整的类结构...")
    with open('tolerance_dialog.py', 'w', encoding='utf-8') as f:
        f.write(complete_file)
    
    print(f"恢复后文件总长度: {len(complete_file)} 字符")
    print("✓ 成功恢复完整的 ToleranceSettingsDialog 类")
    
    # 验证恢复是否成功
    print("\n验证恢复结果：")
    with open('tolerance_dialog.py', 'r', encoding='utf-8', errors='ignore') as f:
        check_content = f.read()
    
    if 'class ToleranceSettingsDialog' in check_content and 'def calculate_tolerances' in check_content:
        print("✓ 类定义和 calculate_tolerances 方法都已成功恢复")
    else:
        print("✗ 恢复失败")
        
except Exception as e:
    print(f"错误: {str(e)}")
    import traceback
    traceback.print_exc()
