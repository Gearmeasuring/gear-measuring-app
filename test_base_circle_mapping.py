#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基圆映射功能

测试新实现的基圆映射功能，确保齿形和齿向曲线能够正确映射到基圆上，
并验证频谱分析结果是否合理。
"""

import os
import sys
import numpy as np
from dataclasses import dataclass

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('..'))

# 直接导入KlingelnbergRippleSpectrumReport类
import importlib.util
spec = importlib.util.spec_from_file_location(
    "KlingelnbergRippleSpectrumReport",
    r"e:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\gear_analysis_refactored\reports\klingelnberg_ripple_spectrum.py"
)
klingelnberg_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(klingelnberg_module)
KlingelnbergRippleSpectrumReport = klingelnberg_module.KlingelnbergRippleSpectrumReport

@dataclass
class MockBasicInfo:
    """模拟基本信息对象"""
    teeth: int = 20  # 齿数
    module: float = 2.0  # 模数
    pressure_angle: float = 20.0  # 压力角
    helix_angle: float = 15.0  # 螺旋角
    pitch_diameter: float = 40.0  # 节圆直径
    base_diameter: float = 37.5877  # 基圆直径
    profile_eval_start: float = 38.0  # 齿形起评点直径
    profile_eval_end: float = 42.0  # 齿形终评点直径
    helix_eval_start: float = 0.0  # 齿向起评点轴向位置
    helix_eval_end: float = 30.0  # 齿向终评点轴向位置
    profile_range_left: tuple = (36.0, 44.0)  # 左侧齿形测量范围
    profile_range_right: tuple = (36.0, 44.0)  # 右侧齿形测量范围
    lead_range_left: tuple = (0.0, 35.0)  # 左侧齿向测量范围
    lead_range_right: tuple = (0.0, 35.0)  # 右侧齿向测量范围

@dataclass
class MockMeasurementData:
    """模拟测量数据对象"""
    basic_info: MockBasicInfo
    profile_data: dict
    flank_data: dict

@dataclass
class MockProfileData:
    """模拟齿形数据对象"""
    left: dict
    right: dict

@dataclass
class MockFlankData:
    """模拟齿向数据对象"""
    left: dict
    right: dict

def generate_mock_gear_data():
    """生成模拟齿轮测量数据"""
    # 创建基本信息
    basic_info = MockBasicInfo()
    
    # 生成齿形数据
    profile_left = {}
    profile_right = {}
    
    # 生成20个齿的齿形数据
    for tooth_id in range(1, 21):
        # 生成齿形偏差数据（包含一些正弦波纹）
        n_points = 100
        x = np.linspace(0, 1, n_points)
        # 生成包含多种频率成分的偏差数据
        values = (0.5 * np.sin(2 * np.pi * 5 * x) +  # 5阶波纹
                  0.2 * np.sin(2 * np.pi * 10 * x) +  # 10阶波纹
                  0.1 * np.sin(2 * np.pi * 20 * x) +  # 20阶波纹
                  0.05 * np.random.randn(n_points))  # 随机噪声
        
        profile_left[tooth_id] = {'values': values.tolist()}
        profile_right[tooth_id] = {'values': values.tolist()}
    
    # 生成齿向数据
    flank_left = {}
    flank_right = {}
    
    # 生成20个齿的齿向数据
    for tooth_id in range(1, 21):
        # 生成齿向偏差数据
        n_points = 100
        x = np.linspace(0, 1, n_points)
        # 生成包含多种频率成分的偏差数据
        values = (0.4 * np.sin(2 * np.pi * 4 * x) +  # 4阶波纹
                  0.15 * np.sin(2 * np.pi * 8 * x) +  # 8阶波纹
                  0.08 * np.sin(2 * np.pi * 16 * x) +  # 16阶波纹
                  0.03 * np.random.randn(n_points))  # 随机噪声
        
        flank_left[tooth_id] = {'values': values.tolist()}
        flank_right[tooth_id] = {'values': values.tolist()}
    
    # 创建数据结构
    profile_data = MockProfileData(left=profile_left, right=profile_right)
    flank_data = MockFlankData(left=flank_left, right=flank_right)
    
    # 创建测量数据对象
    measurement_data = MockMeasurementData(
        basic_info=basic_info,
        profile_data=profile_data,
        flank_data=flank_data
    )
    
    return measurement_data

def test_base_circle_mapping():
    """测试基圆映射功能"""
    print("=== 开始测试基圆映射功能 ===")
    
    # 生成模拟数据
    measurement_data = generate_mock_gear_data()
    
    # 创建报告对象
    reporter = KlingelnbergRippleSpectrumReport()
    
    # 测试齿形基圆映射
    print("\n--- 测试齿形基圆映射 ---")
    try:
        # 获取左侧齿形数据
        tooth_data = measurement_data.profile_data.left[1]['values']
        info = measurement_data.basic_info
        
        # 测试基圆映射
        angles, mapped_values = reporter._map_to_base_circle('profile', tooth_data, info, None)
        
        if angles is not None and mapped_values is not None:
            print(f"✓ 齿形基圆映射成功")
            print(f"  原始数据点数: {len(tooth_data)}")
            print(f"  映射后角度点数: {len(angles)}")
            print(f"  角度范围: [{np.min(angles):.3f}, {np.max(angles):.3f}] rad")
            print(f"  映射后值范围: [{np.min(mapped_values):.3f}, {np.max(mapped_values):.3f}] μm")
        else:
            print("✗ 齿形基圆映射失败")
    except Exception as e:
        print(f"✗ 齿形基圆映射测试失败: {e}")
    
    # 测试齿向基圆映射
    print("\n--- 测试齿向基圆映射 ---")
    try:
        # 获取左侧齿向数据
        tooth_data = measurement_data.flank_data.left[1]['values']
        info = measurement_data.basic_info
        
        # 测试基圆映射
        angles, mapped_values = reporter._map_to_base_circle('flank', tooth_data, info, None)
        
        if angles is not None and mapped_values is not None:
            print(f"✓ 齿向基圆映射成功")
            print(f"  原始数据点数: {len(tooth_data)}")
            print(f"  映射后角度点数: {len(angles)}")
            print(f"  角度范围: [{np.min(angles):.3f}, {np.max(angles):.3f}] rad")
            print(f"  映射后值范围: [{np.min(mapped_values):.3f}, {np.max(mapped_values):.3f}] μm")
        else:
            print("✗ 齿向基圆映射失败")
    except Exception as e:
        print(f"✗ 齿向基圆映射测试失败: {e}")
    
    # 测试基于评价范围的频谱分析
    print("\n--- 测试基于评价范围的频谱分析 ---")
    try:
        # 测试左侧齿形频谱分析
        spectrum_results = reporter._analyze_evaluation_range_spectrum(
            measurement_data, 'profile', 'left'
        )
        
        if spectrum_results:
            print(f"✓ 左侧齿形频谱分析成功")
            print(f"  提取的阶次数: {len(spectrum_results)}")
            print("  主要阶次和幅值:")
            for order, amp in sorted(spectrum_results.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    阶次 {order}: {amp:.4f} μm")
        else:
            print("✗ 左侧齿形频谱分析失败")
        
        # 测试左侧齿向频谱分析
        spectrum_results = reporter._analyze_evaluation_range_spectrum(
            measurement_data, 'flank', 'left'
        )
        
        if spectrum_results:
            print(f"\n✓ 左侧齿向频谱分析成功")
            print(f"  提取的阶次数: {len(spectrum_results)}")
            print("  主要阶次和幅值:")
            for order, amp in sorted(spectrum_results.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    阶次 {order}: {amp:.4f} μm")
        else:
            print("✗ 左侧齿向频谱分析失败")
            
    except Exception as e:
        print(f"✗ 频谱分析测试失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_base_circle_mapping()
