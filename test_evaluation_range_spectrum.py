#!/usr/bin/env python3
"""
测试基于评价范围数据的频谱分析功能

此脚本创建模拟的齿轮测量数据，然后使用基于评价范围数据的频谱分析功能进行分析，
并生成包含分析结果的PDF报告。
"""

import os
import sys
import numpy as np
from types import SimpleNamespace
from matplotlib.backends.backend_pdf import PdfPages

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('gear_analysis_refactored'))

# 导入所需的模块
try:
    from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport
    print("✓ 成功导入 KlingelnbergRippleSpectrumReport")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)


class MockGearData:
    """模拟齿轮测量数据类"""
    
    def __init__(self):
        # 基本信息
        self.basic_info = SimpleNamespace(
            teeth=87,  # 齿数
            module=1.0,  # 模数
            pressure_angle=20.0,  # 压力角
            helix_angle=15.0,  # 螺旋角
            width=20.0,  # 齿宽
            pitch_diameter=87.0,  # 节圆直径
            order_no="TestOrder123",
            drawing_no="TestDrawing456",
            date="2026-02-10",
            time="12:00:00",
            program="TestProgram"
        )
        
        # 齿形数据（左侧和右侧）
        self.profile_data = SimpleNamespace()
        self.profile_data.left = self._generate_profile_data()
        self.profile_data.right = self._generate_profile_data()
        
        # 齿向数据（左侧和右侧）
        self.flank_data = SimpleNamespace()
        self.flank_data.left = self._generate_flank_data()
        self.flank_data.right = self._generate_flank_data()
        
        # 评价范围标记点
        self.basic_info.profile_markers_left = (10.0, 12.0, 18.0, 20.0)  # (da, d1, d2, de)
        self.basic_info.profile_markers_right = (10.0, 12.0, 18.0, 20.0)
        self.basic_info.lead_markers_left = (0.0, 2.0, 18.0, 20.0)  # (ba, b1, b2, be)
        self.basic_info.lead_markers_right = (0.0, 2.0, 18.0, 20.0)
    
    def _generate_profile_data(self):
        """生成模拟的齿形数据"""
        data = {}
        num_teeth = 6  # 生成6个齿的数据
        num_points = 200  # 每个齿200个点
        
        for tooth_num in range(1, num_teeth + 1):
            # 生成基础正弦波 + 噪声
            x = np.linspace(0, 10, num_points)
            # 基础偏差
            base = np.sin(x * 2 * np.pi / 10) * 0.5
            # 添加高阶波纹
            base += np.sin(x * 2 * np.pi * 5 / 10) * 0.2
            base += np.sin(x * 2 * np.pi * 10 / 10) * 0.1
            # 添加噪声
            noise = np.random.normal(0, 0.05, num_points)
            base += noise
            # 每个齿添加不同的偏移
            base += tooth_num * 0.1
            data[tooth_num] = base.tolist()
        
        return data
    
    def _generate_flank_data(self):
        """生成模拟的齿向数据"""
        data = {}
        num_teeth = 6  # 生成6个齿的数据
        num_points = 200  # 每个齿200个点
        
        for tooth_num in range(1, num_teeth + 1):
            # 生成基础正弦波 + 噪声
            x = np.linspace(0, 20, num_points)
            # 基础偏差
            base = np.sin(x * 2 * np.pi / 20) * 0.5
            # 添加高阶波纹
            base += np.sin(x * 2 * np.pi * 3 / 20) * 0.2
            base += np.sin(x * 2 * np.pi * 8 / 20) * 0.1
            # 添加噪声
            noise = np.random.normal(0, 0.05, num_points)
            base += noise
            # 每个齿添加不同的偏移
            base += tooth_num * 0.1
            data[tooth_num] = base.tolist()
        
        return data


def test_evaluation_range_spectrum():
    """测试基于评价范围数据的频谱分析功能"""
    print("=== 开始测试基于评价范围数据的频谱分析功能 ===")
    
    try:
        # 创建模拟数据
        mock_data = MockGearData()
        print("✓ 创建模拟数据成功")
        
        # 创建PDF报告
        output_path = "test_evaluation_range_spectrum.pdf"
        with PdfPages(output_path) as pdf:
            # 创建频谱报告生成器
            reporter = KlingelnbergRippleSpectrumReport()
            print("✓ 创建报告生成器成功")
            
            # 生成基于评价范围数据的频谱分析页面
            reporter.create_evaluation_range_spectrum_page(pdf, mock_data)
            print("✓ 生成基于评价范围数据的频谱分析页面成功")
            
            # 生成预处理对比图表页面
            reporter.create_preprocessing_comparison_page(pdf, mock_data)
            print("✓ 生成预处理对比图表页面成功")
        
        print(f"✓ 测试完成，报告已保存到: {output_path}")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_evaluation_range_spectrum()
    if success:
        print("\n=== 测试成功！基于评价范围数据的频谱分析功能正常工作 ===")
    else:
        print("\n=== 测试失败！请检查错误信息 ===")
    sys.exit(0 if success else 1)
