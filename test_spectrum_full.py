#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的频谱分析流程
"""

import numpy as np
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

try:
    from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, SpectrumParams
except ImportError as e:
    print(f"导入失败: {e}")
    sys.exit(1)

def test_full_spectrum_analysis():
    """
    测试完整的频谱分析流程
    """
    print("=== 测试完整的频谱分析流程 ===")
    
    # 初始化报告生成器
    report = KlingelnbergRippleSpectrumReport()
    
    # 测试参数
    ze = 87  # 齿数
    points_per_tooth = 1000
    
    # 生成测试数据，只包含ZE和ZE+1的分量，且ZE+1的幅值最大
    x = np.linspace(0, 2*np.pi, points_per_tooth)
    # 直接生成大的幅值，不添加噪声
    signal = 0.10 * np.sin(ze * x) + 0.30 * np.sin((ze+1) * x)
    test_data = {0: signal.tolist()}
    
    print(f"生成的信号 - 最小值: {np.min(signal):.3f}, 最大值: {np.max(signal):.3f}")
    print(f"ZE分量幅值: 0.10, ZE+1分量幅值: 0.30")
    
    # 创建频谱计算参数，不使用评价范围标记点
    spectrum_params = SpectrumParams(
        data_dict=test_data,
        teeth_count=ze,
        eval_markers=None,  # 禁用评价范围标记点，使用完整数据
        max_order=7 * ze,
        eval_length=1.0,
        base_diameter=50.0,
        max_components=50,
        side='right',
        data_type='profile',
        info=None
    )
    
    # 测试完整的频谱分析流程，但禁用滤波和去趋势处理
    try:
        orders, amplitudes, rms = report._calculate_spectrum(spectrum_params, disable_detrend=True, disable_filter=True)
        
        print(f"\n完整频谱分析结果: {len(orders)} 个阶次")
        for order, amp in zip(orders, amplitudes):
            print(f"  阶次 {order}: {amp:.6f} μm")
        print(f"RMS值: {rms:.6f} μm")
        
        # 检查是否提取到了ZE和ZE+1的分量
        if ze in orders:
            idx = np.where(orders == ze)[0][0]
            print(f"\nZE阶次 {ze} 的提取幅值: {amplitudes[idx]:.6f} μm")
        else:
            print(f"\n未提取到ZE阶次 {ze}")
        
        if ze + 1 in orders:
            idx = np.where(orders == ze + 1)[0][0]
            print(f"ZE+1阶次 {ze+1} 的提取幅值: {amplitudes[idx]:.6f} μm")
        else:
            print(f"未提取到ZE+1阶次 {ze+1}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        test_full_spectrum_analysis()
        print("\n=== 测试完成 ===")
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
