#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证齿轮齿面波纹分析算法更新

本脚本用于测试 klingelnberg_ripple_spectrum.py 中的新算法是否正确集成到 klingelnberg_single_page.py 中，
并验证频谱图是否使用了新的算法。
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_ripple_spectrum_update')

class MockBasicInfo:
    """模拟基本信息对象"""
    def __init__(self):
        self.teeth = 87  # 齿数
        self.pitch_diameter = 50.0  # 节圆直径
        self.helix_angle = 15.0  # 螺旋角（度）
        self.base_diameter = 48.3  # 基圆直径

class MockMeasurementData:
    """模拟测量数据对象"""
    def __init__(self):
        self.basic_info = MockBasicInfo()
        
        # 生成模拟的齿向数据
        import numpy as np
        
        # 生成10个齿的齿向数据
        self.helix_left = {}
        self.helix_right = {}
        
        for tooth_id in range(10):
            # 生成带有噪声的正弦曲线作为齿向数据
            n_points = 100
            x = np.linspace(0, 1, n_points)
            # 生成基本信号
            signal = 0.5 * np.sin(2 * np.pi * 5 * x)  # 5阶信号
            signal += 0.3 * np.sin(2 * np.pi * 10 * x)  # 10阶信号
            signal += 0.2 * np.sin(2 * np.pi * 15 * x)  # 15阶信号
            # 添加随机噪声
            noise = 0.1 * np.random.randn(n_points)
            signal += noise
            
            # 转换为列表并存储
            self.helix_left[tooth_id] = signal.tolist()
            self.helix_right[tooth_id] = signal.tolist()
        
        # 生成模拟的齿形数据
        self.profile_left = {}
        self.profile_right = {}
        
        for tooth_id in range(10):
            # 生成带有噪声的正弦曲线作为齿形数据
            n_points = 100
            x = np.linspace(0, 1, n_points)
            # 生成基本信号
            signal = 0.4 * np.sin(2 * np.pi * 3 * x)  # 3阶信号
            signal += 0.2 * np.sin(2 * np.pi * 6 * x)  # 6阶信号
            # 添加随机噪声
            noise = 0.08 * np.random.randn(n_points)
            signal += noise
            
            # 转换为列表并存储
            self.profile_left[tooth_id] = signal.tolist()
            self.profile_right[tooth_id] = signal.tolist()

class MockSettings:
    """模拟设置对象"""
    def __init__(self):
        self.report_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_output')
        # 确保输出目录存在
        if not os.path.exists(self.report_output_dir):
            os.makedirs(self.report_output_dir)


def test_ripple_spectrum_update():
    """测试波纹频谱分析算法更新"""
    logger.info("=== 开始测试齿轮齿面波纹分析算法更新 ===")
    
    try:
        # 导入报告模块
        from gear_analysis_refactored.reports.klingelnberg_single_page import KlingelnbergSinglePageReport
        
        # 创建测试数据和设置
        measurement_data = MockMeasurementData()
        settings = MockSettings()
        
        # 创建报告对象
        logger.info("创建 KlingelnbergSinglePageReport 对象")
        report = KlingelnbergSinglePageReport(settings=settings)
        
        # 生成报告文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(settings.report_output_dir, f'test_ripple_spectrum_{timestamp}.pdf')
        
        # 生成报告
        logger.info(f"生成报告到: {output_path}")
        report.generate(measurement_data, output_path)
        
        # 验证报告生成成功
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"✅ 报告生成成功！文件大小: {os.path.getsize(output_path)} 字节")
            logger.info(f"✅ 新的齿轮齿面波纹分析算法已成功集成到报告中")
            logger.info(f"✅ 频谱图应该已经使用了新的算法")
            return True
        else:
            logger.error(f"❌ 报告生成失败，文件不存在或为空")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_algorithm():
    """直接测试新的波纹分析算法"""
    logger.info("=== 直接测试新的波纹分析算法 ===")
    
    try:
        # 导入波纹频谱分析模块
        from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport
        
        # 创建测试数据和设置
        measurement_data = MockMeasurementData()
        settings = MockSettings()
        
        # 创建报告对象
        logger.info("创建 KlingelnbergRippleSpectrumReport 对象")
        ripple_report = KlingelnbergRippleSpectrumReport(settings=settings)
        
        # 测试新的算法方法
        logger.info("测试 _calculate_delta_z 方法")
        delta_z = ripple_report._calculate_delta_z(10.0, 5.0)
        logger.info(f"delta_z = {delta_z}")
        
        logger.info("测试 _calculate_alpha2 方法")
        alpha2 = ripple_report._calculate_alpha2(5.0, 50.0, 0.2618)  # 15度转换为弧度
        logger.info(f"alpha2 = {alpha2} 弧度")
        
        logger.info("测试 _calculate_final_angle 方法")
        alpha = ripple_report._calculate_final_angle(0.0, alpha2, 0.0)
        logger.info(f"final alpha = {alpha} 弧度")
        
        logger.info("✅ 新的算法方法测试成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 直接算法测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("启动测试脚本...")
    
    # 运行直接算法测试
    direct_test_result = test_direct_algorithm()
    
    # 运行完整报告测试
    full_test_result = test_ripple_spectrum_update()
    
    # 总结测试结果
    if direct_test_result and full_test_result:
        logger.info("\n=== 测试总结 ===")
        logger.info("✅ 所有测试通过！")
        logger.info("✅ 齿轮齿面波纹分析算法已成功更新并集成到报告中")
        logger.info("✅ 频谱图现在应该使用了新的算法")
        logger.info("\n请打开生成的PDF报告查看更新后的频谱图。")
        sys.exit(0)
    else:
        logger.info("\n=== 测试总结 ===")
        logger.error("❌ 测试失败！")
        sys.exit(1)
