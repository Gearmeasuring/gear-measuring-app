#!/usr/bin/env python
"""
波纹度频谱模块使用示例
演示如何正确使用 KlingelnbergRippleSpectrumReport 模块
"""
import os
import sys
import logging
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings
from gear_analysis_refactored.config.logging_config import setup_logging

class MockGearData:
    """模拟齿轮测量数据类"""
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
        
        self.basic_info = MockInfo()
        
        # 创建模拟的齿廓和齿向数据
        self.profile_data = type('obj', (), {})
        self.flank_data = type('obj', (), {})
        
        # 生成模拟数据
        num_teeth = 92
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
            self.profile_data.left[tooth_id] = {'values': profile_signal}
            self.profile_data.right[tooth_id] = {'values': profile_signal}
            
            # 齿向数据（左、右齿面）
            flank_signal = generate_signal(x_flank, base_freq=2.0)
            self.flank_data.left[tooth_id] = {'values': flank_signal}
            self.flank_data.right[tooth_id] = {'values': flank_signal}

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("开始演示波纹度频谱模块使用")
    
    try:
        # 1. 创建波纹度频谱报告实例
        settings = RippleSpectrumSettings()
        report = KlingelnbergRippleSpectrumReport(settings=settings)
        
        # 2. 创建模拟数据
        mock_data = MockGearData()
        
        # 3. 创建PDF文件
        output_path = os.path.join(os.path.dirname(__file__), 'demo_ripple_spectrum.pdf')
        with PdfPages(output_path) as pdf:
            # 4. 调用create_page方法生成波纹度频谱页面
            report.create_page(pdf, mock_data)
        
        logger.info(f"波纹度频谱报告生成成功: {output_path}")
        logger.info("您可以在PDF查看器中打开该文件查看结果")
        
    except Exception as e:
        logger.exception(f"演示过程中发生错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)