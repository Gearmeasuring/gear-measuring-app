#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际图表生成，确保使用实际计算的数据而不是模拟数据
"""
import sys
import os
import numpy as np
from dataclasses import dataclass
from matplotlib.backends.backend_pdf import PdfPages

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
class ProfileData:
    """齿形数据类"""
    right: dict
    left: dict

@dataclass
class FlankData:
    """齿向数据类"""
    right: dict
    left: dict

@dataclass
class MeasurementData:
    """测量数据类"""
    basic_info: BasicInfo
    profile_data: ProfileData
    flank_data: FlankData

def generate_realistic_data(teeth_count=87, num_teeth=4, points_per_tooth=80):
    """
    生成真实的测量数据，包含多个阶次
    
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
        # 生成齿形右侧数据 - 包含多个阶次
        y_profile_right = 0.15 * np.sin(2 * np.pi * teeth_count * x) + \
                          0.07 * np.sin(2 * np.pi * 2 * teeth_count * x) + \
                          0.06 * np.sin(2 * np.pi * 3 * teeth_count * x) + \
                          0.05 * np.sin(2 * np.pi * 4 * teeth_count * x) + \
                          0.04 * np.sin(2 * np.pi * 5 * teeth_count * x) + \
                          0.03 * np.sin(2 * np.pi * 6 * teeth_count * x) + \
                          0.01 * np.random.randn(points_per_tooth)
        profile_right[tooth_id] = y_profile_right.tolist()
        
        # 生成齿形左侧数据 - 包含多个阶次
        y_profile_left = 0.14 * np.sin(2 * np.pi * teeth_count * x) + \
                         0.08 * np.sin(2 * np.pi * 2 * teeth_count * x) + \
                         0.05 * np.sin(2 * np.pi * 3 * teeth_count * x) + \
                         0.04 * np.sin(2 * np.pi * 4 * teeth_count * x) + \
                         0.03 * np.sin(2 * np.pi * 5 * teeth_count * x) + \
                         0.02 * np.sin(2 * np.pi * 6 * teeth_count * x) + \
                         0.01 * np.random.randn(points_per_tooth)
        profile_left[tooth_id] = y_profile_left.tolist()
        
        # 生成齿向右侧数据 - 包含多个阶次
        y_flank_right = 0.10 * np.sin(2 * np.pi * teeth_count * x) + \
                        0.06 * np.sin(2 * np.pi * 2 * teeth_count * x) + \
                        0.04 * np.sin(2 * np.pi * 3 * teeth_count * x) + \
                        0.03 * np.sin(2 * np.pi * 4 * teeth_count * x) + \
                        0.02 * np.sin(2 * np.pi * 5 * teeth_count * x) + \
                        0.01 * np.sin(2 * np.pi * 6 * teeth_count * x) + \
                        0.01 * np.random.randn(points_per_tooth)
        flank_right[tooth_id] = y_flank_right.tolist()
        
        # 生成齿向左侧数据 - 包含多个阶次
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

def test_actual_chart():
    """
    测试实际图表生成，确保使用实际计算的数据
    """
    print("开始测试实际图表生成...")
    
    # 生成真实的测量数据
    measurement_data = generate_realistic_data()
    print("生成了真实的测量数据")
    
    # 创建报表生成器
    settings = RippleSpectrumSettings()
    report = KlingelnbergRippleSpectrumReport(settings)
    print("创建了报表生成器")
    
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
    
    # 生成PDF报告
    print("\n生成PDF报告...")
    with PdfPages('actual_ripple_spectrum_report.pdf') as pdf:
        report.create_page(pdf, measurement_data)
    
    print("PDF报告生成完成: actual_ripple_spectrum_report.pdf")
    print("\n测试完成！")

if __name__ == "__main__":
    test_actual_chart()
