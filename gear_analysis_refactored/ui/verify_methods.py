#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证 calculate_tolerances 方法的结构和基本功能
"""

try:
    # 读取 tolerance_dialog.py 文件内容
    with open('tolerance_dialog.py', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # 找到 calculate_tolerances 方法
    calc_start = content.find('def calculate_tolerances')
    if calc_start == -1:
        print("✗ 未找到 calculate_tolerances 方法")
        exit(1)
    
    calc_end = content.find('def ', calc_start + len('def calculate_tolerances'))
    if calc_end == -1:
        calc_end = len(content)
    
    calc_method = content[calc_start:calc_end]
    
    # 验证方法结构
    print("=== 验证 calculate_tolerances 方法结构 ===")
    
    # 检查是否包含所有必要的质量等级获取逻辑
    checks = [
        ('quality_spins 字典查找', 'quality_spins.get'),
        ('当前页面 QSpinBox 查找', 'findChildren'),
        ('profile 类型处理', 'if type_ == "profile"'),
        ('lead 类型处理', 'if type_ == "lead"'),
        ('spacing 类型处理', 'if type_ == "spacing"'),
        ('公差表定义', 'tolerance_tables'),
        ('UI 更新逻辑', 'self.ui.'),
    ]
    
    for check_name, check_pattern in checks:
        if check_pattern in calc_method:
            print(f"✓ {check_name}")
        else:
            print(f"✗ {check_name}")
    
    # 检查质量等级获取的统一机制
    quality_get_methods = [
        'quality_spins.get',
        'findChildren',
        'quality_spin.value()'
    ]
    
    has_quality_get = any(method in calc_method for method in quality_get_methods)
    if has_quality_get:
        print("✓ 包含质量等级获取机制")
    else:
        print("✗ 缺少质量等级获取机制")
    
    # 检查公差值计算逻辑
    tolerance_calculation = ['fHa =', 'ffb =', 'fp =', 'tolerance_table']
    has_calculation = any(calc in calc_method for calc in tolerance_calculation)
    if has_calculation:
        print("✓ 包含公差值计算逻辑")
    else:
        print("✗ 缺少公差值计算逻辑")
    
    # 检查 UI 更新逻辑
    ui_updates = ['self.ui.', 'setText', 'value()']
    has_ui_updates = any(update in calc_method for update in ui_updates)
    if has_ui_updates:
        print("✓ 包含 UI 更新逻辑")
    else:
        print("✗ 缺少 UI 更新逻辑")
    
    print(f"\n方法长度: {len(calc_method)} 字符")
    print("\n=== 验证完成 ===")
    
    print("\n建议：")
    print("1. 启动应用程序并测试质量等级点击功能")
    print("2. 检查各类型（profile、lead、spacing）的公差值是否正确显示")
    print("3. 验证不同质量等级（1-12级）的公差值是否符合预期")
    
except Exception as e:
    print(f"✗ 发生错误: {str(e)}")
    import traceback
    traceback.print_exc()
