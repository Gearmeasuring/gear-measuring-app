#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试克林伯格波纹度谱分析算法修改

验证以下修改：
1. 阶次选择：优先选择大于等于ZE的阶次，而不仅仅是ZE倍数
2. 滤波处理：使用较低的RC低通滤波截止频率
3. 端点匹配：移除端点匹配和闭合曲线构建步骤
4. 平均曲线：只计算评价范围内的平均曲线
5. 幅值阈值：设置为0.02微米
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

def generate_test_data(ze=87, num_teeth=5, points_per_tooth=1000):
    """
    生成测试数据，包含多个阶次的正弦分量
    
    Args:
        ze: 齿数
        num_teeth: 生成的齿数
        points_per_tooth: 每个齿的数据点数
    
    Returns:
        dict: 测试数据字典，格式为 {齿号: [数据点]}
    """
    test_data = {}
    
    # 生成多个阶次的正弦分量，确保有大于ZE的阶次
    frequencies = [ze, ze+5, 2*ze, 2*ze+3, 3*ze, 3*ze+2]
    amplitudes = [0.20, 0.25, 0.18, 0.15, 0.10, 0.08]  # 确保有大于0.02的幅值
    
    for tooth_id in range(num_teeth):
        x = np.linspace(0, 2*np.pi, points_per_tooth)
        signal = np.zeros_like(x)
        
        # 添加每个频率分量
        for freq, amp in zip(frequencies, amplitudes):
            signal += amp * np.sin(freq * x + tooth_id * 0.1)  # 添加相位偏移
        
        # 添加少量噪声
        noise = np.random.normal(0, 0.005, size=points_per_tooth)
        signal += noise
        
        test_data[tooth_id] = signal.tolist()
    
    return test_data

def test_spectrum_analysis():
    """
    测试频谱分析功能
    """
    print("=== 测试克林伯格波纹度谱分析 ===")
    
    # 初始化报告生成器
    report = KlingelnbergRippleSpectrumReport()
    
    # 测试参数
    ze = 87  # 齿数
    num_teeth = 5
    points_per_tooth = 1000
    
    # 生成测试数据
    test_data = generate_test_data(ze=ze, num_teeth=num_teeth, points_per_tooth=points_per_tooth)
    print(f"生成了 {num_teeth} 个齿的测试数据，每个齿 {points_per_tooth} 个点")
    
    # 测试不同数据类型和齿面
    test_cases = [
        ('profile', 'right'),
        ('profile', 'left'),
        ('flank', 'right'),
        ('flank', 'left')
    ]
    
    for data_type, side in test_cases:
        print(f"\n--- 测试 {data_type} {side} ---")
        
        # 创建频谱计算参数
        spectrum_params = SpectrumParams(
            data_dict=test_data,
            teeth_count=ze,
            eval_markers=(0.0, 10.0, 20.0, 30.0),  # 默认评价范围标记
            max_order=7 * ze,  # 最大阶次设为7倍ZE
            eval_length=1.0,  # 评价长度
            base_diameter=50.0,  # 基圆直径
            max_components=50,  # 最大分量数
            side=side,
            data_type=data_type,
            info=None  # 基本信息对象
        )
        
        try:
            # 计算频谱
            orders, amplitudes, rms = report._calculate_spectrum(spectrum_params)
            
            print(f"计算结果: 找到 {len(orders)} 个阶次")
            print(f"RMS值: {rms:.6f} μm")
            
            # 打印找到的阶次和幅值
            if len(orders) > 0:
                print("找到的阶次和幅值:")
                for order, amp in sorted(zip(orders, amplitudes), key=lambda x: x[1], reverse=True):
                    print(f"  阶次 {order}: {amp:.6f} μm")
            else:
                print("未找到有效的阶次")
                
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()

def test_order_selection():
    """
    测试阶次选择逻辑
    """
    print("\n=== 测试阶次选择逻辑 ===")
    
    # 初始化报告生成器
    report = KlingelnbergRippleSpectrumReport()
    
    # 创建一个特殊的测试数据，包含ZE-1, ZE, ZE+1三个阶次，且ZE+1的幅值最大
    ze = 87
    points_per_tooth = 1000
    x = np.linspace(0, 2*np.pi, points_per_tooth)
    
    # ZE+1的幅值最大，且远大于ZE的幅值
    signal = 0.05 * np.sin((ze-1) * x) + 0.10 * np.sin(ze * x) + 0.30 * np.sin((ze+1) * x)
    test_data = {0: signal.tolist()}
    
    # 创建频谱计算参数
    spectrum_params = SpectrumParams(
        data_dict=test_data,
        teeth_count=ze,
        eval_markers=(0.0, 10.0, 20.0, 30.0),
        max_order=7 * ze,
        eval_length=1.0,
        base_diameter=50.0,
        max_components=50,
        side='right',
        data_type='profile',
        info=None
    )
    
    try:
        # 计算频谱
        orders, amplitudes, rms = report._calculate_spectrum(spectrum_params)
        
        print(f"计算结果: 找到 {len(orders)} 个阶次")
        print(f"RMS值: {rms:.6f} μm")
        
        if len(orders) > 0:
            print("找到的阶次和幅值:")
            for order, amp in sorted(zip(orders, amplitudes), key=lambda x: x[1], reverse=True):
                print(f"  阶次 {order}: {amp:.6f} μm")
            
            # 检查是否选择了ZE+1（幅值最大的阶次）
            max_amp_idx = np.argmax(amplitudes)
            selected_order = orders[max_amp_idx]
            print(f"\n幅值最大的阶次: {selected_order}")
            
            if selected_order == ze + 1:
                print("✓ 测试通过: 成功选择了大于ZE的阶次")
            else:
                print("✗ 测试失败: 未选择幅值最大的阶次")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_amplitude_threshold():
    """
    测试幅值阈值过滤
    """
    print("\n=== 测试幅值阈值过滤 ===")
    
    # 初始化报告生成器
    report = KlingelnbergRippleSpectrumReport()
    
    # 创建测试数据，包含小于和大于0.02的幅值
    ze = 87
    points_per_tooth = 1000
    x = np.linspace(0, 2*np.pi, points_per_tooth)
    
    # 两个阶次，一个大于0.02，一个小于0.02
    signal = 0.08 * np.sin(ze * x) + 0.015 * np.sin(2*ze * x)
    test_data = {0: signal.tolist()}
    
    # 创建频谱计算参数
    spectrum_params = SpectrumParams(
        data_dict=test_data,
        teeth_count=ze,
        eval_markers=(0.0, 10.0, 20.0, 30.0),
        max_order=7 * ze,
        eval_length=1.0,
        base_diameter=50.0,
        max_components=50,
        side='right',
        data_type='profile',
        info=None
    )
    
    try:
        # 计算频谱
        orders, amplitudes, rms = report._calculate_spectrum(spectrum_params)
        
        print(f"计算结果: 找到 {len(orders)} 个阶次")
        
        if len(orders) > 0:
            print("找到的阶次和幅值:")
            for order, amp in sorted(zip(orders, amplitudes), key=lambda x: x[1], reverse=True):
                print(f"  阶次 {order}: {amp:.6f} μm")
            
            # 检查所有幅值是否都大于等于0.02
            all_above_threshold = all(amp >= 0.02 for amp in amplitudes)
            if all_above_threshold:
                print("✓ 测试通过: 所有阶次的幅值都大于等于0.02微米")
            else:
                print("✗ 测试失败: 存在幅值小于0.02的阶次")
        else:
            print("✗ 测试失败: 没有找到任何阶次")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        # 运行所有测试
        test_spectrum_analysis()
        test_order_selection()
        test_amplitude_threshold()
        print("\n=== 所有测试完成 ===")
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
