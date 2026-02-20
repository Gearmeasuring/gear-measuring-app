#!/usr/bin/env python3
# 简单测试脚本验证表格数据与图表数据一致

import sys
import os
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath('.'))

# 直接导入文件，避免依赖config模块
import importlib.util
spec = importlib.util.spec_from_file_location("klingelnberg_ripple_spectrum", 
                                             "gear_analysis_refactored/reports/klingelnberg_ripple_spectrum.py")
klingelnberg_ripple_spectrum = importlib.util.module_from_spec(spec)
sys.modules["klingelnberg_ripple_spectrum"] = klingelnberg_ripple_spectrum
spec.loader.exec_module(klingelnberg_ripple_spectrum)

KlingelnbergRippleSpectrumReport = klingelnberg_ripple_spectrum.KlingelnbergRippleSpectrumReport

@dataclass
class BasicInfo:
    """基本信息类"""
    teeth: int = 87
    module: float = 2.0
    pressure_angle: float = 20.0
    helix_angle: float = 0.0
    profile_eval_start: float = 10.0
    profile_eval_end: float = 20.0
    helix_eval_start: float = 10.0
    helix_eval_end: float = 20.0
    profile_markers_right: tuple = (0.0, 10.0, 20.0, 30.0)
    profile_markers_left: tuple = (0.0, 10.0, 20.0, 30.0)
    lead_markers_right: tuple = (0.0, 10.0, 20.0, 30.0)
    lead_markers_left: tuple = (0.0, 10.0, 20.0, 30.0)

@dataclass
class ProfileData:
    """齿廓数据类"""
    right: dict = None
    left: dict = None

@dataclass
class FlankData:
    """齿向数据类"""
    right: dict = None
    left: dict = None

@dataclass
class MeasurementData:
    """测量数据类"""
    basic_info: BasicInfo = None
    profile_data: ProfileData = None
    flank_data: FlankData = None

def generate_test_data(teeth_count=87, points_per_tooth=100):
    """生成测试数据"""
    test_data = {}
    for i in range(teeth_count):
        # 生成包含ZE倍数的正弦波
        x = np.linspace(0, 2 * np.pi, points_per_tooth)
        y = 0.1 * np.sin(2 * np.pi * teeth_count * x)  # ZE倍频
        y += 0.05 * np.sin(2 * np.pi * 2 * teeth_count * x)  # 2ZE倍频
        y += 0.03 * np.sin(2 * np.pi * 3 * teeth_count * x)  # 3ZE倍频
        y += 0.01 * np.random.randn(len(x))  # 添加噪声
        test_data[i] = y.tolist()
    return test_data

def test_table_data_consistency():
    """测试表格数据与图表数据一致性"""
    print("开始测试表格数据与图表数据一致性...")
    
    # 创建测试数据
    teeth_count = 87
    test_profile_data = generate_test_data(teeth_count)
    test_flank_data = generate_test_data(teeth_count)
    
    # 创建数据对象
    basic_info = BasicInfo(teeth=teeth_count)
    profile_data = ProfileData(right=test_profile_data, left=test_profile_data)
    flank_data = FlankData(right=test_flank_data, left=test_flank_data)
    measurement_data = MeasurementData(basic_info=basic_info, profile_data=profile_data, flank_data=flank_data)
    
    # 创建报告生成器
    report = KlingelnbergRippleSpectrumReport()
    
    # 创建PDF文件
    pdf_path = "test_table_consistency.pdf"
    print(f"创建PDF报告: {pdf_path}")
    
    with PdfPages(pdf_path) as pdf:
        # 创建页面
        report.create_page(pdf, measurement_data)
    
    print(f"PDF报告已生成: {pdf_path}")
    print("测试完成! 请检查生成的PDF报告，确保表格数据与图表数据一致。")

if __name__ == "__main__":
    test_table_data_consistency()
