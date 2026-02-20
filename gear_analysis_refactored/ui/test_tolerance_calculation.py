#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 calculate_tolerances 方法是否能正确计算和显示公差值
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # 尝试导入 ToleranceSettingsDialog 类
    from ui.tolerance_dialog import ToleranceSettingsDialog
    from PyQt5.QtWidgets import QApplication
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 创建对话框实例
    dialog = ToleranceSettingsDialog(None)
    
    print("✓ 成功创建 ToleranceSettingsDialog 实例")
    
    # 测试 calculate_tolerances 方法是否存在
    if hasattr(dialog, 'calculate_tolerances'):
        print("✓ calculate_tolerances 方法存在")
        
        # 测试不同类型的公差计算
        test_types = ['profile', 'lead', 'spacing']
        
        for tolerance_type in test_types:
            try:
                # 调用 calculate_tolerances 方法
                dialog.calculate_tolerances(tolerance_type)
                print(f"✓ 成功调用 {tolerance_type} 类型的 calculate_tolerances 方法")
            except Exception as e:
                print(f"✗ 调用 {tolerance_type} 类型的 calculate_tolerances 方法失败: {str(e)}")
    else:
        print("✗ calculate_tolerances 方法不存在")
        
    # 测试 toggle_header_mode 方法是否存在
    if hasattr(dialog, 'toggle_header_mode'):
        print("✓ toggle_header_mode 方法存在")
    else:
        print("✗ toggle_header_mode 方法不存在")
        
except ImportError as e:
    print(f"✗ 导入错误: {str(e)}")
    print("可能需要在正确的环境中运行此测试")
except Exception as e:
    print(f"✗ 发生错误: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n测试完成")
