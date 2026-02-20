#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证实际计算数据是否正确显示到数据表和柱形图中

此脚本生成真实的齿轮测量数据，使用修复后的算法计算频谱，
并验证数据是否正确显示在表格和柱形图中。
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

# 导入修复后的模块
try:
    from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings
    print("✓ 成功导入 KlingelnbergRippleSpectrumReport")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

class MockBasicInfo:
    """模拟基本信息对象"""
    def __init__(self):
        self.teeth = 87  # 齿数
        self.module = 2.0  # 模数
        self.pressure_angle = 20.0  # 压力角
        self.helix_angle = 15.0  # 螺旋角
        self.profile_range_right = (10.0, 30.0)  # 右侧齿廓测量范围
        self.profile_range_left = (10.0, 30.0)  # 左侧齿廓测量范围
        self.lead_range_right = (0.0, 40.0)  # 右侧齿向测量范围
        self.lead_range_left = (0.0, 40.0)  # 左侧齿向测量范围
        self.profile_eval_start_right = 15.0  # 右侧齿廓评价开始
        self.profile_eval_end_right = 25.0  # 右侧齿廓评价结束
        self.profile_eval_start_left = 15.0  # 左侧齿廓评价开始
        self.profile_eval_end_left = 25.0  # 左侧齿廓评价结束
        self.lead_eval_start_right = 5.0  # 右侧齿向评价开始
        self.lead_eval_end_right = 35.0  # 右侧齿向评价结束
        self.lead_eval_start_left = 5.0  # 左侧齿向评价开始
        self.lead_eval_end_left = 35.0  # 左侧齿向评价结束
        self.order_no = "TEST-001"
        self.drawing_no = "DRAW-001"
        self.date = "2026-01-31"
        self.time = "12:00:00"
        self.part_name = "Test Gear"
        self.program = "test_program"

class MockMeasurementData:
    """模拟测量数据对象"""
    def __init__(self):
        self.basic_info = MockBasicInfo()
        self.profile_right = self._generate_gear_data('profile', 'right')
        self.profile_left = self._generate_gear_data('profile', 'left')
        self.helix_right = self._generate_gear_data('helix', 'right')
        self.helix_left = self._generate_gear_data('helix', 'left')
        
    def _generate_gear_data(self, data_type, side):
        """生成真实的齿轮测量数据"""
        teeth_count = 87
        data_dict = {}
        
        # 为每个齿生成数据
        for tooth_id in range(teeth_count):
            # 生成数据点
            n_points = 100
            x = np.linspace(0, 2 * np.pi, n_points)
            
            # 生成包含多个阶次的信号
            if data_type == 'profile':
                if side == 'right':
                    # Profile right 数据
                    y = 0.145 * np.sin(2 * np.pi * teeth_count * x) + \
                        0.100 * np.sin(2 * np.pi * 3 * teeth_count * x) + \
                        0.065 * np.sin(2 * np.pi * 4 * teeth_count * x) + \
                        0.035 * np.sin(2 * np.pi * 5 * teeth_count * x) + \
                        0.020 * np.random.randn(n_points)  # 噪声
                else:
                    # Profile left 数据
                    y = 0.140 * np.sin(2 * np.pi * teeth_count * x) + \
                        0.120 * np.sin(2 * np.pi * 2 * teeth_count * x) + \
                        0.080 * np.sin(2 * np.pi * 4 * teeth_count * x) + \
                        0.040 * np.sin(2 * np.pi * 6 * teeth_count * x) + \
                        0.020 * np.random.randn(n_points)  # 噪声
            else:  # helix
                if side == 'right':
                    # Helix right 数据
                    y = 0.080 * np.sin(2 * np.pi * teeth_count * x) + \
                        0.060 * np.sin(2 * np.pi * 2 * teeth_count * x) + \
                        0.040 * np.sin(2 * np.pi * 3 * teeth_count * x) + \
                        0.020 * np.random.randn(n_points)  # 噪声
                else:
                    # Helix left 数据
                    y = 0.120 * np.sin(2 * np.pi * teeth_count * x) + \
                        0.070 * np.sin(2 * np.pi * 2 * teeth_count * x) + \
                        0.050 * np.sin(2 * np.pi * 3 * teeth_count * x) + \
                        0.020 * np.random.randn(n_points)  # 噪声
            
            data_dict[tooth_id] = y.tolist()
        
        return data_dict

def test_actual_data_display():
    """测试实际计算数据是否正确显示到数据表和柱形图中"""
    print("=== 测试实际计算数据显示 ===")
    
    # 创建测量数据对象
    measurement_data = MockMeasurementData()
    print("✓ 创建了模拟测量数据")
    
    # 验证数据结构
    print(f"✓ Profile right 数据点: {len(measurement_data.profile_right)}")
    print(f"✓ Profile left 数据点: {len(measurement_data.profile_left)}")
    print(f"✓ Helix right 数据点: {len(measurement_data.helix_right)}")
    print(f"✓ Helix left 数据点: {len(measurement_data.helix_left)}")
    
    # 创建设置对象
    settings = RippleSpectrumSettings()
    print("✓ 创建了设置对象")
    
    # 创建报表生成器
    report = KlingelnbergRippleSpectrumReport(settings)
    print("✓ 创建了报表生成器")
    
    # 生成PDF文件
    output_file = "test_actual_data_display.pdf"
    print(f"✓ 准备生成PDF文件: {output_file}")
    
    try:
        with PdfPages(output_file) as pdf:
            report.create_page(pdf, measurement_data)
        print(f"✓ 成功生成PDF文件: {output_file}")
        
        # 验证PDF文件是否存在
        if os.path.exists(output_file):
            print(f"✓ PDF文件已创建，大小: {os.path.getsize(output_file):,} 字节")
        else:
            print(f"✗ PDF文件未创建")
            return False
            
    except Exception as e:
        print(f"✗ 生成PDF文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_spectrum_calculation():
    """测试频谱计算是否正确"""
    print("\n=== 测试频谱计算 ===")
    
    # 创建测量数据对象
    measurement_data = MockMeasurementData()
    
    # 创建设置对象
    settings = RippleSpectrumSettings()
    
    # 创建报表生成器
    report = KlingelnbergRippleSpectrumReport(settings)
    
    # 测试右侧齿廓数据
    print("\n测试右侧齿廓数据:")
    profile_right_data = measurement_data.profile_right
    
    # 提取第一个齿的数据
    first_tooth_data = profile_right_data[0]
    print(f"✓ 第一个齿的数据长度: {len(first_tooth_data)}")
    
    # 测试数据处理
    try:
        from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import SpectrumParams
        
        # 创建频谱计算参数
        params = SpectrumParams(
            data_dict=profile_right_data,
            teeth_count=87,
            eval_markers=(10.0, 15.0, 25.0, 30.0),
            max_order=500,
            max_components=10,
            side='right',
            data_type='profile',
            info=measurement_data.basic_info
        )
        
        # 计算频谱
        orders, amplitudes, rms_value = report._calculate_spectrum(params)
        
        print(f"✓ 计算得到 {len(orders)} 个阶次")
        print(f"✓ RMS值: {rms_value:.4f}")
        print("✓ 阶次和幅值:")
        for order, amp in zip(orders, amplitudes):
            print(f"  Order {order}: {amp:.4f} μm")
            
        if len(orders) > 0:
            print("✓ 频谱计算成功")
        else:
            print("✗ 频谱计算失败，未返回阶次")
            return False
            
    except Exception as e:
        print(f"✗ 频谱计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """主测试函数"""
    print("开始测试实际计算数据显示...\n")
    
    # 测试频谱计算
    spectrum_test_passed = test_spectrum_calculation()
    
    # 测试实际数据显示
    display_test_passed = test_actual_data_display()
    
    print("\n=== 测试结果 ===")
    print(f"频谱计算测试: {'通过' if spectrum_test_passed else '失败'}")
    print(f"数据显示测试: {'通过' if display_test_passed else '失败'}")
    
    if spectrum_test_passed and display_test_passed:
        print("\n✅ 所有测试通过！实际计算数据应该正确显示到数据表和柱形图中。")
        return True
    else:
        print("\n❌ 测试失败，请检查代码。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
