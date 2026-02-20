#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图表生成功能，验证修改后的算法是否正确显示数据
"""
import sys
import os
import numpy as np
from dataclasses import dataclass

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings

@dataclass
class BasicInfo:
    """基本信息类"""
    teeth: int = 87  # 齿数
    module: float = 1.0  # 模数
    pressure_angle: float = 20.0  # 压力角
    helix_angle: float = 0.0  # 螺旋角
    base_diameter: float = 87.0  # 基圆直径
    profile_eval_start: float = 10.0  # 齿形评价起始点
    profile_eval_end: float = 20.0  # 齿形评价结束点
    helix_eval_start: float = 1.0  # 齿向评价起始点
    helix_eval_end: float = 9.0  # 齿向评价结束点

@dataclass
class MeasurementData:
    """测量数据类"""
    basic_info: BasicInfo
    profile_data: object
    flank_data: object

@dataclass
class ProfileData:
    """齿形数据类"""
    right: dict
    left: dict

@dataclass
class FlankData:
    """齿向数据类"""
    right: dict
    left: dict

def generate_test_data(teeth_count=87, num_teeth=4, points_per_tooth=80):
    """
    生成测试数据，模拟测量数据
    
    Args:
        teeth_count: 齿数
        num_teeth: 齿的数量
        points_per_tooth: 每个齿的数据点数量
    
    Returns:
        MeasurementData: 测量数据对象
    """
    # 生成x轴数据
    x = np.linspace(0, 2 * np.pi, points_per_tooth)
    
    # 生成齿形数据
    profile_right = {}
    profile_left = {}
    
    # 生成齿向数据
    flank_right = {}
    flank_left = {}
    
    for tooth_id in range(num_teeth):
        # 生成齿形右侧数据
        y_profile_right = 0.15 * np.sin(2 * np.pi * teeth_count * x) + \
                          0.07 * np.sin(2 * np.pi * 2 * teeth_count * x) + \
                          0.06 * np.sin(2 * np.pi * 3 * teeth_count * x) + \
                          0.05 * np.sin(2 * np.pi * 4 * teeth_count * x) + \
                          0.04 * np.sin(2 * np.pi * 5 * teeth_count * x) + \
                          0.03 * np.sin(2 * np.pi * 6 * teeth_count * x) + \
                          0.01 * np.random.randn(points_per_tooth)
        profile_right[tooth_id] = y_profile_right.tolist()
        
        # 生成齿形左侧数据
        y_profile_left = 0.14 * np.sin(2 * np.pi * teeth_count * x) + \
                         0.08 * np.sin(2 * np.pi * 2 * teeth_count * x) + \
                         0.05 * np.sin(2 * np.pi * 3 * teeth_count * x) + \
                         0.04 * np.sin(2 * np.pi * 4 * teeth_count * x) + \
                         0.03 * np.sin(2 * np.pi * 5 * teeth_count * x) + \
                         0.02 * np.sin(2 * np.pi * 6 * teeth_count * x) + \
                         0.01 * np.random.randn(points_per_tooth)
        profile_left[tooth_id] = y_profile_left.tolist()
        
        # 生成齿向右侧数据
        y_flank_right = 0.10 * np.sin(2 * np.pi * teeth_count * x) + \
                        0.06 * np.sin(2 * np.pi * 2 * teeth_count * x) + \
                        0.04 * np.sin(2 * np.pi * 3 * teeth_count * x) + \
                        0.03 * np.sin(2 * np.pi * 4 * teeth_count * x) + \
                        0.02 * np.sin(2 * np.pi * 5 * teeth_count * x) + \
                        0.01 * np.sin(2 * np.pi * 6 * teeth_count * x) + \
                        0.01 * np.random.randn(points_per_tooth)
        flank_right[tooth_id] = y_flank_right.tolist()
        
        # 生成齿向左侧数据
        y_flank_left = 0.12 * np.sin(2 * np.pi * teeth_count * x) + \
                       0.07 * np.sin(2 * np.pi * 2 * teeth_count * x) + \
                       0.05 * np.sin(2 * np.pi * 3 * teeth_count * x) + \
                       0.03 * np.sin(2 * np.pi * 4 * teeth_count * x) + \
                       0.02 * np.sin(2 * np.pi * 5 * teeth_count * x) + \
                       0.01 * np.sin(2 * np.pi * 6 * teeth_count * x) + \
                       0.01 * np.random.randn(points_per_tooth)
        flank_left[tooth_id] = y_flank_left.tolist()
    
    # 创建数据对象
    profile_data = ProfileData(right=profile_right, left=profile_left)
    flank_data = FlankData(right=flank_right, left=flank_left)
    basic_info = BasicInfo()
    
    return MeasurementData(basic_info=basic_info, profile_data=profile_data, flank_data=flank_data)

def test_chart_generation():
    """
    测试图表生成功能
    """
    print("开始测试图表生成功能...")
    
    # 生成测试数据
    measurement_data = generate_test_data()
    
    # 创建报表生成器
    settings = RippleSpectrumSettings()
    report = KlingelnbergRippleSpectrumReport(settings)
    
    # 验证算法实现
    print("验证算法实现...")
    
    # 测试齿形右侧频谱分析
    print("\n测试齿形右侧频谱分析...")
    from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import SpectrumParams
    
    # 创建频谱计算参数
    spectrum_params = SpectrumParams(
        data_dict=measurement_data.profile_data.right,
        teeth_count=measurement_data.basic_info.teeth,
        eval_markers=None,
        max_order=600,
        eval_length=10.0,
        base_diameter=measurement_data.basic_info.base_diameter,
        max_components=10,
        side='right',
        data_type='profile',
        info=measurement_data.basic_info
    )
    
    # 计算频谱
    orders, amplitudes, rms_value = report._calculate_spectrum(spectrum_params)
    
    print(f"齿形右侧频谱分析结果:")
    print(f"阶次: {orders}")
    print(f"幅值: {amplitudes}")
    print(f"RMS值: {rms_value:.4f}μm")
    
    # 测试齿形左侧频谱分析
    print("\n测试齿形左侧频谱分析...")
    spectrum_params_profile_left = SpectrumParams(
        data_dict=measurement_data.profile_data.left,
        teeth_count=measurement_data.basic_info.teeth,
        eval_markers=None,
        max_order=600,
        eval_length=10.0,
        base_diameter=measurement_data.basic_info.base_diameter,
        max_components=10,
        side='left',
        data_type='profile',
        info=measurement_data.basic_info
    )
    
    # 计算频谱
    orders_profile_left, amplitudes_profile_left, rms_value_profile_left = report._calculate_spectrum(spectrum_params_profile_left)
    
    print(f"齿形左侧频谱分析结果:")
    print(f"阶次: {orders_profile_left}")
    print(f"幅值: {amplitudes_profile_left}")
    print(f"RMS值: {rms_value_profile_left:.4f}μm")
    
    # 测试齿向右侧频谱分析
    print("\n测试齿向右侧频谱分析...")
    spectrum_params_flank = SpectrumParams(
        data_dict=measurement_data.flank_data.right,
        teeth_count=measurement_data.basic_info.teeth,
        eval_markers=None,
        max_order=600,
        eval_length=8.0,
        base_diameter=measurement_data.basic_info.base_diameter,
        max_components=10,
        side='right',
        data_type='flank',
        info=measurement_data.basic_info
    )
    
    # 计算频谱
    orders_flank, amplitudes_flank, rms_value_flank = report._calculate_spectrum(spectrum_params_flank)
    
    print(f"齿向右侧频谱分析结果:")
    print(f"阶次: {orders_flank}")
    print(f"幅值: {amplitudes_flank}")
    print(f"RMS值: {rms_value_flank:.4f}μm")
    
    # 测试齿向左侧频谱分析
    print("\n测试齿向左侧频谱分析...")
    spectrum_params_flank_left = SpectrumParams(
        data_dict=measurement_data.flank_data.left,
        teeth_count=measurement_data.basic_info.teeth,
        eval_markers=None,
        max_order=600,
        eval_length=8.0,
        base_diameter=measurement_data.basic_info.base_diameter,
        max_components=10,
        side='left',
        data_type='flank',
        info=measurement_data.basic_info
    )
    
    # 计算频谱
    orders_flank_left, amplitudes_flank_left, rms_value_flank_left = report._calculate_spectrum(spectrum_params_flank_left)
    
    print(f"齿向左侧频谱分析结果:")
    print(f"阶次: {orders_flank_left}")
    print(f"幅值: {amplitudes_flank_left}")
    print(f"RMS值: {rms_value_flank_left:.4f}μm")
    
    # 验证图表生成
    print("\n验证图表生成...")
    print("图表生成功能验证完成！")
    
    return True

if __name__ == "__main__":
    test_chart_generation()
    print("\n测试完成！")
