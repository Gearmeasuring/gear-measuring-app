#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试残差迭代分析功能
执行第一次和第二次残差迭代分析，并生成相应的PDF报告
"""

import os
import sys
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

# 直接导入KlingelnbergRippleSpectrumReport，绕过reports包的导入
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport

class BasicInfo:
    """基本信息类，用于模拟齿轮的基本参数"""
    def __init__(self):
        self.teeth = 87  # 齿数
        self.module = 2.0  # 模数
        self.pressure_angle = 20.0  # 压力角
        self.helix_angle = 0.0  # 螺旋角
        self.width = 20.0  # 齿宽
        self.accuracy_grade = 6  # 精度等级

class MeasurementData:
    """测量数据类，用于模拟MKAReader返回的数据结构"""
    def __init__(self):
        # 创建设置对象
        from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import RippleSpectrumSettings
        self.settings = RippleSpectrumSettings()
        
        # 创建基本信息对象
        self.basic_info = BasicInfo()
        
        # 生成测试数据
        teeth_count = self.basic_info.teeth
        
        # 生成齿形数据
        self.profile_left = {}
        self.profile_right = {}
        
        # 生成齿向数据
        self.helix_left = {}
        self.helix_right = {}
        
        # 为每个齿生成测试数据
        for i in range(teeth_count):
            # 生成齿形测试数据
            x = np.linspace(0, 2 * np.pi, 100)
            
            # 左侧齿形：包含87, 174, 261等阶次的信号
            y_left = 0.509 * np.sin(2 * np.pi * 87 * x) + 0.3 * np.sin(2 * np.pi * 174 * x) + 0.2 * np.sin(2 * np.pi * 261 * x) + 0.05 * np.random.randn(len(x))
            self.profile_left[i] = y_left.tolist()
            
            # 右侧齿形：包含87, 174等阶次的信号
            y_right = 0.4 * np.sin(2 * np.pi * 87 * x) + 0.2 * np.sin(2 * np.pi * 174 * x) + 0.05 * np.random.randn(len(x))
            self.profile_right[i] = y_right.tolist()
            
            # 生成齿向测试数据
            y_helix_left = 0.3 * np.sin(2 * np.pi * 87 * x) + 0.1 * np.sin(2 * np.pi * 174 * x) + 0.05 * np.random.randn(len(x))
            self.helix_left[i] = y_helix_left.tolist()
            
            y_helix_right = 0.25 * np.sin(2 * np.pi * 87 * x) + 0.15 * np.sin(2 * np.pi * 174 * x) + 0.05 * np.random.randn(len(x))
            self.helix_right[i] = y_helix_right.tolist()

def main():
    """主函数"""
    print("=== 测试残差迭代分析功能 ===")
    
    try:
        # 创建模拟的测量数据对象
        measurement_data = MeasurementData()
        print("成功创建模拟测量数据对象")
        
        # 检查基本信息
        if hasattr(measurement_data, 'basic_info'):
            info = measurement_data.basic_info
            print(f"齿数: {getattr(info, 'teeth', '未知')}")
            print(f"模数: {getattr(info, 'module', '未知')}")
            print(f"压力角: {getattr(info, 'pressure_angle', '未知')}")
            print(f"螺旋角: {getattr(info, 'helix_angle', '未知')}")
        
        # 2. 创建KlingelnbergRippleSpectrumReport实例
        report = KlingelnbergRippleSpectrumReport()
        print("成功创建KlingelnbergRippleSpectrumReport实例")
        
        # 3. 执行第一次残差迭代分析（residual_iteration=0）
        print("\n=== 执行第一次残差迭代分析（原始数据）===")
        pdf_file_0 = "klingelnberg_ripple_spectrum_residual_0.pdf"
        
        from matplotlib.backends.backend_pdf import PdfPages
        with PdfPages(pdf_file_0) as pdf:
            report.create_page(pdf, measurement_data, residual_iteration=0)
        
        print(f"成功生成第一次残差迭代分析报告: {pdf_file_0}")
        
        # 4. 执行第二次残差迭代分析（residual_iteration=1）
        print("\n=== 执行第二次残差迭代分析（在第一次残差基础上）===")
        pdf_file_1 = "klingelnberg_ripple_spectrum_residual_1.pdf"
        
        with PdfPages(pdf_file_1) as pdf:
            report.create_page(pdf, measurement_data, residual_iteration=1)
        
        print(f"成功生成第二次残差迭代分析报告: {pdf_file_1}")
        
        print("\n=== 测试完成 ===")
        print(f"生成的报告文件:")
        print(f"1. 第一次残差迭代分析: {pdf_file_0}")
        print(f"2. 第二次残差迭代分析: {pdf_file_1}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
