#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 从备份文件中恢复 calculate_tolerances 方法

try:
    # 读取备份文件内容
    with open('tolerance_dialog.py.bak_fix', 'r', encoding='utf-8', errors='ignore') as f:
        backup_content = f.read()
    
    # 找到 calculate_tolerances 方法的开始和结束位置
    calc_start = backup_content.find('def calculate_tolerances')
    if calc_start == -1:
        print("未找到 calculate_tolerances 方法")
        exit(1)
    
    # 找到下一个方法定义，作为 calculate_tolerances 方法的结束
    next_method_start = backup_content.find('def ', calc_start + len('def calculate_tolerances'))
    if next_method_start == -1:
        calc_end = len(backup_content)
    else:
        calc_end = next_method_start
    
    # 提取 calculate_tolerances 方法
    calc_method = backup_content[calc_start:calc_end]
    
    # 同样处理 toggle_header_mode 方法
    toggle_start = backup_content.find('def toggle_header_mode')
    if toggle_start == -1:
        print("未找到 toggle_header_mode 方法")
        toggle_method = ""
    else:
        next_method_after_toggle = backup_content.find('def ', toggle_start + len('def toggle_header_mode'))
        if next_method_after_toggle == -1:
            toggle_end = len(backup_content)
        else:
            toggle_end = next_method_after_toggle
        
        toggle_method = backup_content[toggle_start:toggle_end]
    
    # 读取主文件内容
    with open('tolerance_dialog.py', 'r', encoding='utf-8', errors='ignore') as f:
        main_content = f.read()
    
    # 将恢复的方法添加到主文件末尾
    updated_content = main_content
    if calc_method:
        updated_content += '\n\n' + calc_method
    if toggle_method:
        updated_content += '\n\n' + toggle_method
    
    # 写回主文件
    with open('tolerance_dialog.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("成功恢复 calculate_tolerances 和 toggle_header_mode 方法")
    print(f"恢复的 calculate_tolerances 方法长度: {len(calc_method)} 字符")
    if toggle_method:
        print(f"恢复的 toggle_header_mode 方法长度: {len(toggle_method)} 字符")
        
except Exception as e:
    print(f"恢复过程中出现错误: {str(e)}")
    import traceback
    traceback.print_exc()