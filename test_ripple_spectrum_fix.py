#!/usr/bin/env python3
"""
测试波纹度频谱分析修复
"""
import os
import sys
import numpy as np
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored/reports'))

from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, SpectrumParams

class MockInfo:
    """模拟基本信息对象"""
    def __init__(self):
        self.teeth = 87
        self.module = 1.0
        self.pressure_angle = 20.0
        self.helix_angle = 0.0
        self.profile_eval_start = 10.0
        self.profile_eval_end = 20.0
        self.profile_range_left = (5.0, 25.0)
        self.profile_range_right = (5.0, 25.0)
        self.helix_eval_start = 1.0
        self.helix_eval_end = 9.0
        self.lead_range_left = (0.0, 10.0)
        self.lead_range_right = (0.0, 10.0)

class MockMeasurementData:
    """模拟测量数据对象"""
    def __init__(self):
        self.basic_info = MockInfo()
        
        # 创建模拟的齿形数据
        np.random.seed(42)  # 固定随机种子以获得可重复的结果
        self.profile_data = type('ProfileData', (), {})
        self.profile_data.left = {}
        self.profile_data.right = {}
        
        # 为每个齿生成模拟数据
        for tooth_id in range(1, 5):  # 生成4个齿的数据
            # 生成正弦波数据，包含多个阶次
            n_points = 100
            x = np.linspace(0, 2 * np.pi, n_points)
            
            # 生成包含多个阶次的信号
            signal = 0.1 * np.sin(87 * x)  # 87阶（齿数）
            signal += 0.05 * np.sin(174 * x)  # 174阶（2*87）
            signal += 0.03 * np.sin(261 * x)  # 261阶（3*87）
            signal += 0.02 * np.sin(348 * x)  # 348阶（4*87）
            signal += 0.01 * np.sin(435 * x)  # 435阶（5*87）
            signal += np.random.normal(0, 0.005, n_points)  # 添加噪声
            
            # 存储到数据结构中
            self.profile_data.left[tooth_id] = signal.tolist()
            self.profile_data.right[tooth_id] = signal.tolist()
        
        # 创建模拟的齿向数据
        self.flank_data = type('FlankData', (), {})
        self.flank_data.left = {}
        self.flank_data.right = {}
        
        # 为每个齿生成模拟数据
        for tooth_id in range(1, 5):  # 生成4个齿的数据
            # 生成正弦波数据，包含多个阶次
            n_points = 100
            x = np.linspace(0, 2 * np.pi, n_points)
            
            # 生成包含多个阶次的信号
            signal = 0.08 * np.sin(87 * x)  # 87阶（齿数）
            signal += 0.04 * np.sin(174 * x)  # 174阶（2*87）
            signal += 0.02 * np.sin(261 * x)  # 261阶（3*87）
            signal += np.random.normal(0, 0.004, n_points)  # 添加噪声
            
            # 存储到数据结构中
            self.flank_data.left[tooth_id] = signal.tolist()
            self.flank_data.right[tooth_id] = signal.tolist()

def test_ripple_spectrum_fix():
    """测试波纹度频谱分析修复"""
    print("开始测试波纹度频谱分析修复...")
    
    # 创建测试数据
    measurement_data = MockMeasurementData()
    
    # 创建报告生成器
    reporter = KlingelnbergRippleSpectrumReport()
    
    # 测试Profile Left频谱分析
    print("\n测试Profile Left频谱分析:")
    try:
        # 获取数据
        data_dict = measurement_data.profile_data.left
        teeth_count = measurement_data.basic_info.teeth
        eval_markers = (5.0, 10.0, 20.0, 25.0)
        eval_length = 10.0
        base_diameter = 87.0  # 假设基圆直径为87mm
        
        # 创建频谱计算参数
        params = SpectrumParams(
            data_dict=data_dict,
            teeth_count=teeth_count,
            eval_markers=eval_markers,
            max_order=500,
            eval_length=eval_length,
            base_diameter=base_diameter,
            max_components=10,
            side='left',
            data_type='profile',
            info=measurement_data.basic_info
        )
        
        # 计算频谱
        orders, amplitudes, rms_value = reporter._calculate_spectrum(params)
        
        print(f"成功计算频谱: {len(orders)}个阶次")
        print(f"阶次: {orders}")
        print(f"幅值: {[round(a, 4) for a in amplitudes]}")
        print(f"RMS值: {round(rms_value, 4)}μm")
        
        if len(orders) > 0:
            print("✓ Profile Left频谱分析成功！")
        else:
            print("✗ Profile Left频谱分析失败，未找到阶次")
            
    except Exception as e:
        print(f"✗ Profile Left频谱分析失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试Profile Right频谱分析
    print("\n测试Profile Right频谱分析:")
    try:
        # 获取数据
        data_dict = measurement_data.profile_data.right
        teeth_count = measurement_data.basic_info.teeth
        eval_markers = (5.0, 10.0, 20.0, 25.0)
        eval_length = 10.0
        base_diameter = 87.0  # 假设基圆直径为87mm
        
        # 创建频谱计算参数
        params = SpectrumParams(
            data_dict=data_dict,
            teeth_count=teeth_count,
            eval_markers=eval_markers,
            max_order=500,
            eval_length=eval_length,
            base_diameter=base_diameter,
            max_components=10,
            side='right',
            data_type='profile',
            info=measurement_data.basic_info
        )
        
        # 计算频谱
        orders, amplitudes, rms_value = reporter._calculate_spectrum(params)
        
        print(f"成功计算频谱: {len(orders)}个阶次")
        print(f"阶次: {orders}")
        print(f"幅值: {[round(a, 4) for a in amplitudes]}")
        print(f"RMS值: {round(rms_value, 4)}μm")
        
        if len(orders) > 0:
            print("✓ Profile Right频谱分析成功！")
        else:
            print("✗ Profile Right频谱分析失败，未找到阶次")
            
    except Exception as e:
        print(f"✗ Profile Right频谱分析失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试Flank Left频谱分析
    print("\n测试Flank Left频谱分析:")
    try:
        # 获取数据
        data_dict = measurement_data.flank_data.left
        teeth_count = measurement_data.basic_info.teeth
        eval_markers = (0.0, 1.0, 9.0, 10.0)
        eval_length = 8.0
        base_diameter = 87.0  # 假设基圆直径为87mm
        
        # 创建频谱计算参数
        params = SpectrumParams(
            data_dict=data_dict,
            teeth_count=teeth_count,
            eval_markers=eval_markers,
            max_order=500,
            eval_length=eval_length,
            base_diameter=base_diameter,
            max_components=10,
            side='left',
            data_type='flank',
            info=measurement_data.basic_info
        )
        
        # 计算频谱
        orders, amplitudes, rms_value = reporter._calculate_spectrum(params)
        
        print(f"成功计算频谱: {len(orders)}个阶次")
        print(f"阶次: {orders}")
        print(f"幅值: {[round(a, 4) for a in amplitudes]}")
        print(f"RMS值: {round(rms_value, 4)}μm")
        
        if len(orders) > 0:
            print("✓ Flank Left频谱分析成功！")
        else:
            print("✗ Flank Left频谱分析失败，未找到阶次")
            
    except Exception as e:
        print(f"✗ Flank Left频谱分析失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试Flank Right频谱分析
    print("\n测试Flank Right频谱分析:")
    try:
        # 获取数据
        data_dict = measurement_data.flank_data.right
        teeth_count = measurement_data.basic_info.teeth
        eval_markers = (0.0, 1.0, 9.0, 10.0)
        eval_length = 8.0
        base_diameter = 87.0  # 假设基圆直径为87mm
        
        # 创建频谱计算参数
        params = SpectrumParams(
            data_dict=data_dict,
            teeth_count=teeth_count,
            eval_markers=eval_markers,
            max_order=500,
            eval_length=eval_length,
            base_diameter=base_diameter,
            max_components=10,
            side='right',
            data_type='flank',
            info=measurement_data.basic_info
        )
        
        # 计算频谱
        orders, amplitudes, rms_value = reporter._calculate_spectrum(params)
        
        print(f"成功计算频谱: {len(orders)}个阶次")
        print(f"阶次: {orders}")
        print(f"幅值: {[round(a, 4) for a in amplitudes]}")
        print(f"RMS值: {round(rms_value, 4)}μm")
        
        if len(orders) > 0:
            print("✓ Flank Right频谱分析成功！")
        else:
            print("✗ Flank Right频谱分析失败，未找到阶次")
            
    except Exception as e:
        print(f"✗ Flank Right频谱分析失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_ripple_spectrum_fix()
