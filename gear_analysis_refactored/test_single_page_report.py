#!/usr/bin/env python
"""
测试Klingelnberg单页报告生成，验证新算法是否正确集成
"""
import os
import sys
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gear_analysis_refactored.config.logging_config import setup_logging
from reports.klingelnberg_single_page import KlingelnbergSinglePageReport
from reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport
from types import SimpleNamespace
import numpy as np

class MockMeasurementData:
    """模拟测量数据类"""
    def __init__(self):
        # 创建模拟基本信息
        class MockInfo:
            teeth = 92
            module = 1.0
            pressure_angle = 20.0
            helix_angle = 0.0
            profile_eval_start = 43.829
            profile_eval_end = 51.2
            profile_range_left = (42.81, 51.75)
            profile_range_right = (42.81, 51.75)
            lead_range_left = (0.0, 45.7)
            lead_range_right = (0.0, 45.7)
            helix_eval_start = 2.1
            helix_eval_end = 43.7
            drawing_no = "TEST-001"
            customer = "Demo Customer"
            order_no = "ORDER-001"
            program = "test_program"
            date = "2026-01-20"
            operator = "Test User"
            location = "Test Lab"
            profile_markers_left = (42.81, 43.829, 51.2, 51.75)
            profile_markers_right = (42.81, 43.829, 51.2, 51.75)
            lead_markers_left = (0.0, 2.1, 43.7, 45.7)
            lead_markers_right = (0.0, 2.1, 43.7, 45.7)
            tolerance_standard = "ISO 1328"
            accuracy_grade = 5
        
        self.basic_info = MockInfo()
        
        # 创建模拟的齿廓和齿向数据
        self.profile_data = SimpleNamespace()
        self.flank_data = SimpleNamespace()
        
        # 生成模拟数据
        num_teeth = 6  # 只生成6个齿的数据，加快测试速度
        points_per_tooth = 200
        
        self.profile_data.left = {}
        self.profile_data.right = {}
        self.flank_data.left = {}
        self.flank_data.right = {}
        
        # 为每个齿生成包含多个阶次的模拟数据
        for tooth_id in range(num_teeth):
            # 齿廓数据：沿直径方向的测量点
            x_profile = np.linspace(42.81, 51.75, points_per_tooth)
            # 齿向数据：沿齿宽方向的测量点
            x_flank = np.linspace(0.0, 45.7, points_per_tooth)
            
            # 生成包含多个阶次的信号（模拟波纹度）
            def generate_signal(x, base_freq=10.0):
                signal = 0.0
                # 添加不同阶次的正弦波（模拟波纹度）
                signal += 0.5 * np.sin(2 * np.pi * base_freq * x)  # 基频
                signal += 0.3 * np.sin(2 * np.pi * base_freq * 2 * x)  # 2倍频
                signal += 0.2 * np.sin(2 * np.pi * base_freq * 3 * x)  # 3倍频
                signal += 0.1 * np.sin(2 * np.pi * base_freq * 4 * x)  # 4倍频
                signal += 0.05 * np.random.randn(len(x))  # 添加噪声
                return signal
            
            # 齿廓数据（左、右齿面）
            profile_signal = generate_signal(x_profile, base_freq=10.0)
            self.profile_data.left[tooth_id] = profile_signal
            self.profile_data.right[tooth_id] = profile_signal
            
            # 齿向数据（左、右齿面）
            flank_signal = generate_signal(x_flank, base_freq=2.0)
            self.flank_data.left[tooth_id] = flank_signal
            self.flank_data.right[tooth_id] = flank_signal

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("开始测试Klingelnberg单页报告生成")
    
    try:
        # 1. 创建模拟数据
        mock_data = MockMeasurementData()
        
        # 2. 创建单页报告生成器
        report_generator = KlingelnbergSinglePageReport()
        
        # 3. 创建输出路径
        output_path = os.path.join(os.path.dirname(__file__), 'test_single_page_report.pdf')
        
        # 4. 生成报告
        success = report_generator.generate_report(
            measurement_data=mock_data,
            deviation_results={},
            output_path=output_path
        )
        
        if success:
            logger.info(f"测试成功！报告已生成: {output_path}")
            print(f"测试成功！报告已生成: {output_path}")
        else:
            logger.error("测试失败！报告生成失败")
            print("测试失败！报告生成失败")
            return False
        
    except Exception as e:
        logger.exception(f"测试过程中发生错误: {e}")
        print(f"测试过程中发生错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
