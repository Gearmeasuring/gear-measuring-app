#!/usr/bin/env python3
"""
测试不同齿数的情况，确保算法在不同齿数下都能正确工作
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

# 生成测试数据
def generate_test_data(teeth_count=87, num_teeth=5, num_points=100):
    """生成测试数据"""
    profile_data = {}
    flank_data = {}
    
    # 为每个齿生成数据
    for tooth_id in range(num_teeth):
        # 生成含有多个阶次的测试数据
        x = np.linspace(0, 2 * np.pi, num_points)
        
        # 生成含有ZE及其倍数阶次的信号
        signal = np.zeros_like(x)
        
        # 添加ZE阶次
        signal += 0.1 * np.sin(teeth_count * x + 0.1 * tooth_id)
        
        # 添加2ZE阶次
        signal += 0.05 * np.sin(2 * teeth_count * x + 0.2 * tooth_id)
        
        # 添加3ZE阶次
        signal += 0.03 * np.sin(3 * teeth_count * x + 0.3 * tooth_id)
        
        # 添加4ZE阶次
        signal += 0.02 * np.sin(4 * teeth_count * x + 0.4 * tooth_id)
        
        # 添加噪声
        signal += 0.01 * np.random.randn(len(x))
        
        # 添加线性趋势
        signal += 0.0001 * x
        
        profile_data[tooth_id] = signal.tolist()
        flank_data[tooth_id] = signal.tolist()
    
    return profile_data, flank_data

def test_different_teeth():
    """测试不同齿数的情况"""
    print("=== 测试不同齿数的情况 ===")
    
    # 测试不同的齿数
    test_teeth = [20, 40, 60, 87, 100, 120]
    
    for teeth_count in test_teeth:
        print(f"\n=== 测试齿数: {teeth_count} ===")
        
        # 创建基本信息
        basic_info = BasicInfo(teeth=teeth_count)
        
        # 生成测试数据
        profile_data, flank_data = generate_test_data(teeth_count=teeth_count)
        
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
        report = KlingelnbergRippleSpectrumReport(settings)
        
        # 导入必要的类
        from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import SpectrumParams
        
        # 测试Profile数据
        print(f"\nProfile Right:")
        spectrum_params = SpectrumParams(
            data_dict=profile_data,
            teeth_count=teeth_count,
            max_order=7 * teeth_count,
            max_components=10,
            side="right",
            data_type="profile",
            info=basic_info
        )
        
        try:
            orders, amplitudes, rms = report._calculate_spectrum(spectrum_params)
            print(f"阶次: {orders}")
            print(f"幅值: {amplitudes}")
            print(f"RMS: {rms:.4f}")
            print(f"成功计算频谱，得到 {len(orders)} 个阶次")
            
            # 检查是否包含ZE倍数阶次
            ze_multiples_found = []
            for i in range(1, 7):
                ze_order = i * teeth_count
                if ze_order in orders:
                    ze_multiples_found.append(ze_order)
            
            if ze_multiples_found:
                print(f"找到ZE倍数阶次: {ze_multiples_found}")
            else:
                print("警告: 未找到ZE倍数阶次")
                
        except Exception as e:
            print(f"计算频谱失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_different_teeth()
