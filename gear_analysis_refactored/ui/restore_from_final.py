#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 从 .bak_final 备份文件中恢复完整的 calculate_tolerances 方法

try:
    # 读取 .bak_final 备份文件内容
    with open('tolerance_dialog.py.bak_final', 'r', encoding='utf-8', errors='ignore') as f:
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
    print(f"从 .bak_final 提取的 calculate_tolerances 方法长度: {len(calc_method)} 字符")
    
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
        print(f"从 .bak_final 提取的 toggle_header_mode 方法长度: {len(toggle_method)} 字符")
    
    # 读取当前主文件内容
    with open('tolerance_dialog.py', 'r', encoding='utf-8', errors='ignore') as f:
        main_content = f.read()
    
    # 移除旧的方法定义（如果存在）
    if 'def calculate_tolerances' in main_content:
        old_calc_start = main_content.find('def calculate_tolerances')
        old_calc_end = main_content.find('def ', old_calc_start + len('def calculate_tolerances'))
        if old_calc_end == -1:
            old_calc_end = len(main_content)
        
        # 保留主文件内容直到旧方法开始
        main_content = main_content[:old_calc_start]
    
    if 'def toggle_header_mode' in main_content:
        old_toggle_start = main_content.find('def toggle_header_mode')
        old_toggle_end = main_content.find('def ', old_toggle_start + len('def toggle_header_mode'))
        if old_toggle_end == -1:
            old_toggle_end = len(main_content)
        
        # 保留主文件内容直到旧方法开始
        main_content = main_content[:old_toggle_start]
    
    # 将恢复的方法添加到主文件末尾
    updated_content = main_content
    if calc_method:
        updated_content += '\n\n' + calc_method
    if toggle_method:
        updated_content += '\n\n' + toggle_method
    
    # 写回主文件
    with open('tolerance_dialog.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("成功从 .bak_final 备份文件恢复 calculate_tolerances 和 toggle_header_mode 方法")
    
except Exception as e:
    print(f"恢复过程中出现错误: {str(e)}")
    import traceback
    traceback.print_exc()
