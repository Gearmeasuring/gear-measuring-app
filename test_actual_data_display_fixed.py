#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的klingelnberg_ripple_spectrum.py是否正确使用实际测量数据
"""

import sys
import os
import numpy as np
from dataclasses import dataclass

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored/reports'))

from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings

@dataclass
class MockBasicInfo:
    """模拟基本信息类"""
    teeth: int = 87
    module: float = 1.0
    pressure_angle: float = 20.0
    helix_angle: float = 0.0
    profile_eval_start: float = 10.0
    profile_eval_end: float = 20.0
    helix_eval_start: float = 5.0
    helix_eval_end: float = 15.0
    profile_range_left: tuple = (5.0, 25.0)
    profile_range_right: tuple = (5.0, 25.0)
    lead_range_left: tuple = (0.0, 20.0)
    lead_range_right: tuple = (0.0, 20.0)

@dataclass
class MockMeasurementData:
    """模拟测量数据类"""
    basic_info: MockBasicInfo
    profile_left: dict = None
    profile_right: dict = None
    helix_left: dict = None
    helix_right: dict = None

    def __post_init__(self):
        # 生成模拟的实际测量数据
        if self.profile_left is None:
            self.profile_left = self._generate_profile_data('left')
        if self.profile_right is None:
            self.profile_right = self._generate_profile_data('right')
        if self.helix_left is None:
            self.helix_left = self._generate_helix_data('left')
        if self.helix_right is None:
            self.helix_right = self._generate_helix_data('right')

    def _generate_profile_data(self, side):
        """生成Profile数据"""
        data = {}
        teeth = self.basic_info.teeth
        for tooth in range(teeth):
            # 生成带有噪声的实际测量数据
            x = np.linspace(0, 2 * np.pi, 100)
            if side == 'left':
                y = 0.140 * np.sin(2 * np.pi * teeth * x) + 0.140 * np.sin(2 * np.pi * 3 * teeth * x) + 0.040 * np.sin(2 * np.pi * 5 * teeth * x)
            else:  # right
                y = 0.145 * np.sin(2 * np.pi * teeth * x) + 0.100 * np.sin(2 * np.pi * 4 * teeth * x) + 0.035 * np.sin(2 * np.pi * 5 * teeth * x)
            y += 0.01 * np.random.randn(len(x))  # 添加噪声
            data[tooth] = y.tolist()
        return data

    def _generate_helix_data(self, side):
        """生成Helix数据"""
        data = {}
        teeth = self.basic_info.teeth
        for tooth in range(teeth):
            # 生成带有噪声的实际测量数据
            x = np.linspace(0, 2 * np.pi, 100)
            if side == 'left':
                y = 0.12 * np.sin(2 * np.pi * teeth * x) + 0.07 * np.sin(2 * np.pi * 2 * teeth * x) + 0.03 * np.sin(2 * np.pi * 3 * teeth * x)
            else:  # right
                y = 0.08 * np.sin(2 * np.pi * teeth * x) + 0.06 * np.sin(2 * np.pi * 2 * teeth * x) + 0.03 * np.sin(2 * np.pi * 3 * teeth * x)
            y += 0.01 * np.random.randn(len(x))  # 添加噪声
            data[tooth] = y.tolist()
        return data

def test_actual_data_display():
    """测试实际数据显示"""
    print("=" * 80)
    print("测试修复后的klingelnberg_ripple_spectrum.py是否正确使用实际测量数据")
    print("=" * 80)

    # 创建模拟数据
    basic_info = MockBasicInfo()
    measurement_data = MockMeasurementData(basic_info)

    # 创建报表对象
    settings = RippleSpectrumSettings()
    report = KlingelnbergRippleSpectrumReport(settings)

    print("\n1. 测试数据获取和处理")
    print("-" * 60)

    # 测试Profile Right数据
    print("\n测试Profile Right数据:")
    from matplotlib import pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 6))
    
    try:
        # 调用创建频谱图表的方法
        report._create_spectrum_chart(ax, "Profile right", measurement_data, 'profile', 'right')
        print("✓ 成功调用_create_spectrum_chart方法")
        
        # 检查是否使用了实际数据
        # 通过日志输出判断是否使用了测试数据
        print("\n检查日志输出，确认是否使用了实际数据...")
        print("如果日志中没有'using test data'的警告，则说明使用了实际数据")
        
        # 保存图表以便查看
        plt.title("Profile Right Spectrum")
        plt.tight_layout()
        plt.savefig("test_profile_right_spectrum.png")
        print("✓ 保存了Profile Right频谱图表: test_profile_right_spectrum.png")
        plt.close()
        
    except Exception as e:
        print(f"✗ 调用_create_spectrum_chart方法失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试数据表格
    print("\n2. 测试数据表格生成")
    print("-" * 60)
    
    try:
        fig, ax = plt.subplots(figsize=(12, 8))
        report._create_data_table(ax, measurement_data, 'right')
        print("✓ 成功调用_create_data_table方法")
        
        plt.title("Data Table")
        plt.tight_layout()
        plt.savefig("test_data_table.png")
        print("✓ 保存了数据表格: test_data_table.png")
        plt.close()
        
    except Exception as e:
        print(f"✗ 调用_create_data_table方法失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n3. 测试完整页面生成")
    print("-" * 60)
    
    try:
        from matplotlib.backends.backend_pdf import PdfPages
        pdf = PdfPages("test_ripple_spectrum_report.pdf")
        report.create_page(pdf, measurement_data)
        pdf.close()
        print("✓ 成功生成完整的波纹度频谱报告: test_ripple_spectrum_report.pdf")
        
    except Exception as e:
        print(f"✗ 生成完整报告失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("测试完成，请查看生成的图表和日志输出")
    print("=" * 80)

if __name__ == "__main__":
    test_actual_data_display()
