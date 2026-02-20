#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试残差迭代分析功能（使用真实MKA文件）

此脚本使用真实的MKA文件测试齿轮波纹度频谱分析的残差迭代功能，
包括首次分析、第二次分析（移除1个最大幅值分量）和第三次分析（移除2个最大幅值分量）。
"""

import sys
import os
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

# 导入MKA文件读取器
try:
    from gear_analysis_refactored.readers.mka_reader import MKAReader
    print("成功导入MKAReader")
except ImportError as e:
    print(f"导入MKAReader错误: {e}")
    # 尝试直接导入
    try:
        from readers.mka_reader import MKAReader
        print("成功直接导入MKAReader")
    except ImportError as e:
        print(f"直接导入MKAReader错误: {e}")
        print("使用模拟数据进行测试")
        # 定义模拟的MKAReader类
        class MKAReader:
            def __init__(self, file_path):
                self.file_path = file_path
                self.measurement_data = self._create_measurement_data()
            
            def _create_measurement_data(self):
                """创建模拟的测量数据"""
                class MeasurementData:
                    def __init__(self):
                        self.basic_info = self._create_basic_info()
                        self.profile_left = self._create_test_data()
                        self.profile_right = self._create_test_data()
                        self.helix_left = self._create_test_data()
                        self.helix_right = self._create_test_data()
                    
                    def _create_basic_info(self):
                        """创建基本信息对象"""
                        class BasicInfo:
                            def __init__(self):
                                self.teeth = 87
                                self.module = 2.0
                                self.pressure_angle = 20.0
                                self.helix_angle = 15.0
                                self.order_no = "263751-018-WAV"
                                self.drawing_no = "84-T3.2.47.02.76-G-WAV"
                                self.date = "14.02.25"
                                self.time = "21:04:11"
                                self.program = "263751-018-WAV"
                                self.part_name = "Gear Test Part"
                        return BasicInfo()
                    
                    def _create_test_data(self):
                        """创建测试数据"""
                        data = {}
                        num_teeth = 87
                        points_per_tooth = 100
                        
                        for tooth_id in range(1, num_teeth + 1):
                            # 创建包含多个频率成分的测试数据
                            x = np.linspace(0, 1, points_per_tooth)
                            # 主频率（87阶）
                            y = 0.509 * np.sin(2 * np.pi * 87 * x)
                            # 添加其他频率成分
                            y += 0.3 * np.sin(2 * np.pi * 174 * x)
                            y += 0.2 * np.sin(2 * np.pi * 261 * x)
                            y += 0.1 * np.sin(2 * np.pi * 348 * x)
                            y += 0.05 * np.sin(2 * np.pi * 435 * x)
                            # 添加噪声
                            y += 0.02 * np.random.randn(points_per_tooth)
                            data[tooth_id] = y.tolist()
                        
                        return data
                # 返回MeasurementData实例
                return MeasurementData()
        
        class MeasurementData:
            def __init__(self):
                self.basic_info = self._create_basic_info()
                self.profile_left = self._create_test_data()
                self.profile_right = self._create_test_data()
                self.helix_left = self._create_test_data()
                self.helix_right = self._create_test_data()
            
            def _create_basic_info(self):
                """创建基本信息对象"""
                class BasicInfo:
                    def __init__(self):
                        self.teeth = 87
                        self.module = 2.0
                        self.pressure_angle = 20.0
                        self.helix_angle = 15.0
                        self.order_no = "263751-018-WAV"
                        self.drawing_no = "84-T3.2.47.02.76-G-WAV"
                        self.date = "14.02.25"
                        self.time = "21:04:11"
                        self.program = "263751-018-WAV"
                        self.part_name = "Gear Test Part"
                return BasicInfo()
            
            def _create_test_data(self):
                """创建测试数据"""
                data = {}
                num_teeth = 87
                points_per_tooth = 100
                
                for tooth_id in range(1, num_teeth + 1):
                    # 创建包含多个频率成分的测试数据
                    x = np.linspace(0, 1, points_per_tooth)
                    # 主频率（87阶）
                    y = 0.509 * np.sin(2 * np.pi * 87 * x)
                    # 添加其他频率成分
                    y += 0.3 * np.sin(2 * np.pi * 174 * x)
                    y += 0.2 * np.sin(2 * np.pi * 261 * x)
                    y += 0.1 * np.sin(2 * np.pi * 348 * x)
                    y += 0.05 * np.sin(2 * np.pi * 435 * x)
                    # 添加噪声
                    y += 0.02 * np.random.randn(points_per_tooth)
                    data[tooth_id] = y.tolist()
                
                return data

def main():
    """主函数"""
    print("=== 测试残差迭代分析功能（使用真实MKA文件） ===")
    
    try:
        # MKA文件路径
        mka_file = "263751-018-WAV.mka"
        
        # 检查文件是否存在
        if os.path.exists(mka_file):
            print(f"使用真实MKA文件: {mka_file}")
            # 读取MKA文件
            reader = MKAReader(mka_file)
            measurement_data = reader.measurement_data
        else:
            print(f"MKA文件不存在: {mka_file}，使用模拟数据")
            # 使用模拟数据
            measurement_data = MeasurementData()
        
        print("成功创建测量数据对象")
        
        # 检查基本信息
        if hasattr(measurement_data, 'basic_info'):
            info = measurement_data.basic_info
            print(f"齿数: {getattr(info, 'teeth', '未知')}")
            print(f"模数: {getattr(info, 'module', '未知')}")
            print(f"压力角: {getattr(info, 'pressure_angle', '未知')}")
            print(f"螺旋角: {getattr(info, 'helix_angle', '未知')}")
        
        # 2. 导入KlingelnbergRippleSpectrumReport
        try:
            from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport
            print("成功导入KlingelnbergRippleSpectrumReport")
        except ImportError as e:
            print(f"导入错误: {e}")
            # 尝试直接导入
            from reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport
            print("成功直接导入KlingelnbergRippleSpectrumReport")
        
        # 3. 创建KlingelnbergRippleSpectrumReport实例
        report = KlingelnbergRippleSpectrumReport()
        print("成功创建KlingelnbergRippleSpectrumReport实例")
        
        # 4. 执行第一次残差迭代分析（residual_iteration=0）
        print("\n=== 执行第一次残差迭代分析（原始数据）===")
        pdf_file_0 = "klingelnberg_ripple_spectrum_residual_0_mka.pdf"
        
        with PdfPages(pdf_file_0) as pdf:
            report.create_page(pdf, measurement_data, residual_iteration=0)
        
        print(f"成功生成第一次残差迭代分析报告: {pdf_file_0}")
        
        # 5. 执行第二次残差迭代分析（residual_iteration=1）
        print("\n=== 执行第二次残差迭代分析（在第一次残差基础上）===")
        pdf_file_1 = "klingelnberg_ripple_spectrum_residual_1_mka.pdf"
        
        with PdfPages(pdf_file_1) as pdf:
            report.create_page(pdf, measurement_data, residual_iteration=1)
        
        print(f"成功生成第二次残差迭代分析报告: {pdf_file_1}")
        
        # 6. 执行第三次残差迭代分析（residual_iteration=2）
        print("\n=== 执行第三次残差迭代分析（在第二次残差基础上）===")
        pdf_file_2 = "klingelnberg_ripple_spectrum_residual_2_mka.pdf"
        
        with PdfPages(pdf_file_2) as pdf:
            report.create_page(pdf, measurement_data, residual_iteration=2)
        
        print(f"成功生成第三次残差迭代分析报告: {pdf_file_2}")
        
        # 7. 执行第四次残差迭代分析（residual_iteration=3）
        print("\n=== 执行第四次残差迭代分析（在第三次残差基础上）===")
        pdf_file_3 = "klingelnberg_ripple_spectrum_residual_3_mka.pdf"
        
        with PdfPages(pdf_file_3) as pdf:
            report.create_page(pdf, measurement_data, residual_iteration=3)
        
        print(f"成功生成第四次残差迭代分析报告: {pdf_file_3}")
        
        print("\n=== 测试完成 ===")
        print("生成的报告文件:")
        print(f"1. 首次分析: {pdf_file_0}")
        print(f"2. 第二次分析: {pdf_file_1}")
        print(f"3. 第三次分析: {pdf_file_2}")
        print(f"4. 第四次分析: {pdf_file_3}")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
