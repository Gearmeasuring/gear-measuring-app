#!/usr/bin/env python3
"""
增强版测试脚本：使用更复杂的测试数据测试Klingelnberg波纹度频谱报告生成器
"""

import sys
import os
import numpy as np
from dataclasses import dataclass

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings

@dataclass
class BasicInfo:
    """基本信息类"""
    teeth: int = 87
    module: float = 1.0
    pressure_angle: float = 20.0
    helix_angle: float = 0.0
    drawing_no: str = "Test Drawing"
    customer: str = "Test Customer"
    order_no: str = "Test Order"
    type: str = "gear"
    program: str = "Test Program"
    date: str = "2026-01-31"
    profile_eval_start: float = 10.0
    profile_eval_end: float = 20.0
    profile_range_right: tuple = (5.0, 25.0)
    profile_range_left: tuple = (5.0, 25.0)
    lead_eval_start: float = 5.0
    lead_eval_end: float = 15.0
    lead_range_right: tuple = (0.0, 20.0)
    lead_range_left: tuple = (0.0, 20.0)

@dataclass
class MeasurementData:
    """测量数据类"""
    basic_info: BasicInfo
    profile_data: dict
    flank_data: dict
    tolerance: object = None

@dataclass
class Tolerance:
    """公差类"""
    ripple_tolerance_enabled: bool = True
    ripple_tolerance_R: float = 2.0
    ripple_tolerance_N0: float = 1.0
    ripple_tolerance_K: float = 0.0

# 生成增强版测试数据
def generate_enhanced_test_data(teeth_count=87, num_teeth=10, num_points=200):
    """生成增强版测试数据，包含更多频率分量"""
    profile_data = {}
    flank_data = {}
    
    # 为每个齿生成数据
    for tooth_id in range(num_teeth):
        # 生成含有多个阶次的测试数据
        x = np.linspace(0, 2 * np.pi, num_points)
        
        # 生成含有ZE及其倍数阶次的信号
        signal = np.zeros_like(x)
        
        # 添加ZE阶次（87）- 主分量
        signal += 0.50 * np.sin(teeth_count * x + 0.1 * tooth_id)
        
        # 添加2ZE阶次（174）
        signal += 0.37 * np.sin(2 * teeth_count * x + 0.2 * tooth_id)
        
        # 添加3ZE阶次（261）
        signal += 0.28 * np.sin(3 * teeth_count * x + 0.3 * tooth_id)
        
        # 添加4ZE阶次（348）
        signal += 0.27 * np.sin(4 * teeth_count * x + 0.4 * tooth_id)
        
        # 添加5ZE阶次（435）
        signal += 0.21 * np.sin(5 * teeth_count * x + 0.5 * tooth_id)
        
        # 添加噪声
        signal += 0.05 * np.random.randn(len(x))
        
        # 添加线性趋势
        signal += 0.0001 * x
        
        profile_data[tooth_id] = signal.tolist()
        flank_data[tooth_id] = signal.tolist()
    
    return profile_data, flank_data

def test_enhanced_ripple_spectrum():
    """测试增强版波纹度频谱报告生成器"""
    print("=== 测试增强版 Klingelnberg 波纹度频谱报告生成器 ===")
    
    # 创建基本信息
    basic_info = BasicInfo()
    
    # 生成增强版测试数据
    profile_data, flank_data = generate_enhanced_test_data()
    
    # 创建测量数据
    tolerance = Tolerance()
    measurement_data = MeasurementData(
        basic_info=basic_info,
        profile_data=profile_data,
        flank_data=flank_data,
        tolerance=tolerance
    )
    
    # 创建报告生成器
    settings = RippleSpectrumSettings()
    # 确保启用去趋势处理
    settings.update_profile_helix_settings(
        detrend_settings={'enabled': True},
        filter_params={'enabled': True}
    )
    report = KlingelnbergRippleSpectrumReport(settings)
    
    # 测试数据获取
    print("1. 测试数据获取")
    print(f"Profile data: {len(profile_data)} teeth")
    print(f"Flank data: {len(flank_data)} teeth")
    
    # 测试频谱计算
    print("\n2. 测试频谱计算")

    # 导入必要的类
    from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import SpectrumParams

    # 测试Profile Right数据
    print("\n=== Profile Right ===")
    params = SpectrumParams(
        data_dict=profile_data,
        teeth_count=87,
        max_order=500,
        max_components=10,
        side="right",
        data_type="profile",
        info=basic_info
    )

    try:
        orders, amplitudes, rms = report._calculate_spectrum(params)
        print(f"Orders: {orders}")
        print(f"Amplitudes: {amplitudes}")
        print(f"RMS: {rms:.4f}")
        print(f"Successfully calculated spectrum for Profile Right")
    except Exception as e:
        print(f"Error calculating spectrum for Profile Right: {e}")

    # 测试Profile Left数据
    print("\n=== Profile Left ===")
    params = SpectrumParams(
        data_dict=profile_data,
        teeth_count=87,
        max_order=500,
        max_components=10,
        side="left",
        data_type="profile",
        info=basic_info
    )

    try:
        orders, amplitudes, rms = report._calculate_spectrum(params)
        print(f"Orders: {orders}")
        print(f"Amplitudes: {amplitudes}")
        print(f"RMS: {rms:.4f}")
        print(f"Successfully calculated spectrum for Profile Left")
    except Exception as e:
        print(f"Error calculating spectrum for Profile Left: {e}")

    # 测试Flank Right数据
    print("\n=== Flank Right ===")
    params = SpectrumParams(
        data_dict=flank_data,
        teeth_count=87,
        max_order=500,
        max_components=10,
        side="right",
        data_type="flank",
        info=basic_info
    )

    try:
        orders, amplitudes, rms = report._calculate_spectrum(params)
        print(f"Orders: {orders}")
        print(f"Amplitudes: {amplitudes}")
        print(f"RMS: {rms:.4f}")
        print(f"Successfully calculated spectrum for Flank Right")
    except Exception as e:
        print(f"Error calculating spectrum for Flank Right: {e}")

    # 测试Flank Left数据
    print("\n=== Flank Left ===")
    params = SpectrumParams(
        data_dict=flank_data,
        teeth_count=87,
        max_order=500,
        max_components=10,
        side="left",
        data_type="flank",
        info=basic_info
    )

    try:
        orders, amplitudes, rms = report._calculate_spectrum(params)
        print(f"Orders: {orders}")
        print(f"Amplitudes: {amplitudes}")
        print(f"RMS: {rms:.4f}")
        print(f"Successfully calculated spectrum for Flank Left")
    except Exception as e:
        print(f"Error calculating spectrum for Flank Left: {e}")
    
    # 测试PDF生成
    print("\n3. 测试PDF生成")
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        
        with PdfPages('enhanced_test_ripple_spectrum.pdf') as pdf:
            report.create_page(pdf, measurement_data)
        print("Successfully generated enhanced PDF report")
    except Exception as e:
        print(f"Error generating PDF: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_enhanced_ripple_spectrum()
