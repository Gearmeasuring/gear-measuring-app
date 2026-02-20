#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
详细验证 calculate_tolerances 方法的功能组件
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
    
    print("=== 详细验证 calculate_tolerances 方法 ===")
    print(f"方法总长度: {len(calc_method)} 字符")
    print("\n" + "="*50)
    
    # 1. 质量等级获取机制
    print("\n1. 质量等级获取机制")
    print("-" * 30)
    
    # 检查 profile 类型的质量等级获取
    if 'profile_quality_spin.value()' in calc_method:
        print("✓ profile 类型使用 profile_quality_spin.value() 获取质量等级")
    elif 'self.ui.profile_quality_spin.value()' in calc_method:
        print("✓ profile 类型使用 self.ui.profile_quality_spin.value() 获取质量等级")
    else:
        print("✗ profile 类型质量等级获取机制不明确")
    
    # 检查 lead 类型的质量等级获取
    if 'lead_quality_spin.value()' in calc_method:
        print("✓ lead 类型使用 lead_quality_spin.value() 获取质量等级")
    elif 'self.ui.lead_quality_spin.value()' in calc_method:
        print("✓ lead 类型使用 self.ui.lead_quality_spin.value() 获取质量等级")
    else:
        print("✗ lead 类型质量等级获取机制不明确")
    
    # 检查 spacing 类型的质量等级获取
    if 'spacing_quality_spin.value()' in calc_method:
        print("✓ spacing 类型使用 spacing_quality_spin.value() 获取质量等级")
    elif 'self.ui.spacing_quality_spin.value()' in calc_method:
        print("✓ spacing 类型使用 self.ui.spacing_quality_spin.value() 获取质量等级")
    else:
        print("✗ spacing 类型质量等级获取机制不明确")
    
    # 2. 公差表定义
    print("\n2. 公差表定义")
    print("-" * 30)
    
    if 'tolerance_table = {' in calc_method:
        print("✓ 包含公差表定义")
        
        # 检查是否包含所有质量等级
        quality_levels = [str(i) for i in range(1, 13)]  # 1-12级
        found_levels = []
        
        for level in quality_levels:
            if f' {level}:' in calc_method:
                found_levels.append(level)
        
        if len(found_levels) == 12:
            print("✓ 包含完整的1-12级质量等级公差值")
        else:
            print(f"✗ 缺少部分质量等级，仅找到 {len(found_levels)}/{12} 级")
    else:
        print("✗ 未找到公差表定义")
    
    # 3. UI 更新逻辑
    print("\n3. UI 更新逻辑")
    print("-" * 30)
    
    # 检查是否更新质量等级显示
    if 'setText(str(Q))' in calc_method:
        print("✓ 包含质量等级显示更新")
    else:
        print("✗ 缺少质量等级显示更新")
    
    # 检查是否更新公差值显示
    tolerance_fields = ['fHa', 'ffa', 'Fa', 'fHb', 'ffb', 'Fb', 'fp', 'fu', 'Fp']
    found_fields = []
    
    for field in tolerance_fields:
        if f'[{field}]' in calc_method or f'.{field}' in calc_method:
            found_fields.append(field)
    
    if found_fields:
        print(f"✓ 更新的公差字段: {', '.join(found_fields)}")
    else:
        print("✗ 缺少公差值显示更新")
    
    # 检查是否使用固定值显示
    if 'setText(f"{fHa:.1f}")' in calc_method or 'setText(f"{ffa:.1f}")' in calc_method:
        print("✓ 使用固定值显示公差（符合要求）")
    else:
        print("✗ 可能未使用固定值显示公差")
    
    # 4. 错误处理
    print("\n4. 错误处理")
    print("-" * 30)
    
    if 'try:' in calc_method and 'except:' in calc_method:
        print("✓ 包含异常处理")
    else:
        print("✗ 缺少异常处理")
    
    # 5. 类型处理完整性
    print("\n5. 类型处理完整性")
    print("-" * 30)
    
    types = ['profile', 'lead', 'spacing']
    for type_ in types:
        if f'type_ == "{type_}"' in calc_method:
            print(f"✓ 包含 {type_} 类型处理")
        else:
            print(f"✗ 缺少 {type_} 类型处理")
    
    print("\n" + "="*50)
    print("\n验证完成！")
    
    # 总结
    print("\n=== 验证总结 ===")
    all_checks = [
        ("质量等级获取机制", 'quality_levels'),
        ("公差表定义", 'tolerance_table'),
        ("UI 更新逻辑", 'setText'),
        ("异常处理", 'try:'),
        ("类型处理完整性", 'profile'),
    ]
    
    passed = 0
    total = len(all_checks)
    
    for check_name, check_pattern in all_checks:
        if check_pattern in calc_method:
            passed += 1
            print(f"✓ {check_name}")
        else:
            print(f"✗ {check_name}")
    
    print(f"\n总体验证结果: {passed}/{total} 项通过")
    
    if passed >= 4:
        print("\n🎉 方法看起来已经包含了主要功能，可以正常工作！")
        print("建议：启动应用程序测试质量等级点击功能")
    else:
        print("\n⚠️  方法可能缺少一些关键功能，建议进一步检查")
        
except Exception as e:
    print(f"✗ 发生错误: {str(e)}")
    import traceback
    traceback.print_exc()
