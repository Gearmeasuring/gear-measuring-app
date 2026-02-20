#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从 .bak_final 备份文件中完整恢复 calculate_tolerances 方法
"""

try:
    # 读取 .bak_final 备份文件内容
    print("正在读取备份文件...")
    with open('tolerance_dialog.py.bak_final', 'r', encoding='utf-8', errors='ignore') as f:
        backup_content = f.read()
    
    print(f"备份文件总长度: {len(backup_content)} 字符")
    
    # 找到 calculate_tolerances 方法的开始位置
    calc_start = backup_content.find('def calculate_tolerances')
    if calc_start == -1:
        print("错误：未找到 calculate_tolerances 方法")
        exit(1)
    
    print(f"calculate_tolerances 方法开始位置: {calc_start}")
    
    # 找到 toggle_header_mode 方法的开始位置（作为 calculate_tolerances 方法的结束）
    toggle_start = backup_content.find('def toggle_header_mode')
    if toggle_start == -1:
        print("警告：未找到 toggle_header_mode 方法，将使用文件末尾作为结束位置")
        calc_end = len(backup_content)
    else:
        print(f"toggle_header_mode 方法开始位置: {toggle_start}")
        calc_end = toggle_start
    
    # 提取 calculate_tolerances 方法
    calc_method = backup_content[calc_start:calc_end]
    print(f"提取的 calculate_tolerances 方法长度: {len(calc_method)} 字符")
    
    # 验证提取的方法是否完整
    if 'def calculate_tolerances' not in calc_method:
        print("错误：提取的方法不完整")
        exit(1)
    
    # 读取当前主文件内容
    print("\n正在读取主文件...")
    with open('tolerance_dialog.py', 'r', encoding='utf-8', errors='ignore') as f:
        main_content = f.read()
    
    print(f"主文件总长度: {len(main_content)} 字符")
    
    # 查找主文件中是否已有 calculate_tolerances 方法
    old_calc_start = main_content.find('def calculate_tolerances')
    if old_calc_start != -1:
        # 找到旧方法的结束位置
        old_calc_end = main_content.find('def ', old_calc_start + len('def calculate_tolerances'))
        if old_calc_end == -1:
            old_calc_end = len(main_content)
        
        print(f"主文件中旧方法开始位置: {old_calc_start}")
        print(f"主文件中旧方法结束位置: {old_calc_end}")
        print(f"主文件中旧方法长度: {old_calc_end - old_calc_start} 字符")
        
        # 替换旧方法
        updated_content = main_content[:old_calc_start] + calc_method + main_content[old_calc_end:]
    else:
        # 在文件末尾添加新方法
        updated_content = main_content + '\n\n' + calc_method
    
    # 写回主文件
    print("\n正在更新主文件...")
    with open('tolerance_dialog.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"更新后主文件总长度: {len(updated_content)} 字符")
    print("✓ 成功恢复 calculate_tolerances 方法")
    
    # 验证恢复是否成功
    print("\n验证恢复结果：")
    with open('tolerance_dialog.py', 'r', encoding='utf-8', errors='ignore') as f:
        check_content = f.read()
    
    if 'def calculate_tolerances' in check_content:
        check_start = check_content.find('def calculate_tolerances')
        check_end = check_content.find('def ', check_start + len('def calculate_tolerances'))
        if check_end == -1:
            check_end = len(check_content)
        
        print(f"恢复后方法长度: {check_end - check_start} 字符")
        print("✓ 方法已成功恢复")
    else:
        print("✗ 恢复失败")
        
except Exception as e:
    print(f"错误: {str(e)}")
    import traceback
    traceback.print_exc()
