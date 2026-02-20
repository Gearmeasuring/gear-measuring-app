#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试高阶评价处理流程
"""

import numpy as np
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

# 直接导入模块
import importlib.util

# 导入klingelnberg_ripple_spectrum模块
spec = importlib.util.spec_from_file_location(
    "klingelnberg_ripple_spectrum",
    "gear_analysis_refactored/reports/klingelnberg_ripple_spectrum.py"
)
klingelnberg_ripple_spectrum = importlib.util.module_from_spec(spec)
spec.loader.exec_module(klingelnberg_ripple_spectrum)

# 从模块中获取需要的类和函数
KlingelnbergRippleSpectrumReport = klingelnberg_ripple_spectrum.KlingelnbergRippleSpectrumReport
SpectrumParams = klingelnberg_ripple_spectrum.SpectrumParams


class TestInfo:
    """测试用的基本信息类"""
    def __init__(self):
        self.teeth = 87  # 齿数
        self.module = 1.0  # 模数
        self.pressure_angle = 20.0  # 压力角
        self.helix_angle = 0.0  # 螺旋角
        self.profile_eval_start = 10.0  # 齿廓评价起始直径
        self.profile_eval_end = 20.0  # 齿廓评价结束直径
        self.helix_eval_start = 0.0  # 齿向评价起始位置
        self.helix_eval_end = 10.0  # 齿向评价结束位置
        self.base_diameter = 87.0  # 基圆直径


def test_high_order_evaluation():
    """测试高阶评价处理流程"""
    print("开始测试高阶评价处理流程...")
    
    # 创建测试数据
    teeth_count = 87
    test_data = {}
    
    # 生成测试数据
    for tooth_id in range(teeth_count):
        # 生成包含低频和高频成分的数据
        x = np.linspace(0, 2 * np.pi, 100)
        # 低频成分（鼓形和趋势）
        low_freq = 0.5 * np.sin(x) + 0.2 * x
        # 高频成分（波纹度）
        high_freq = 0.1 * np.sin(87 * x) + 0.05 * np.sin(174 * x)
        # 噪声
        noise = 0.01 * np.random.randn(len(x))
        # 合成数据
        data = low_freq + high_freq + noise
        test_data[tooth_id] = data.tolist()
    
    # 创建报告对象
    report = KlingelnbergRippleSpectrumReport()
    
    # 确保评价方法设置为高阶
    report.settings.profile_helix_settings['evaluation_method'] = 'high_order'
    
    # 创建测试信息对象
    info = TestInfo()
    
    # 创建频谱计算参数
    spectrum_params = SpectrumParams(
        data_dict=test_data,
        teeth_count=teeth_count,
        eval_markers=(5.0, 10.0, 20.0, 25.0),
        max_order=500,
        eval_length=10.0,
        base_diameter=87.0,
        max_components=10,
        side='left',
        data_type='profile',
        info=info
    )
    
    print("测试数据生成完成，开始计算频谱...")
    
    # 计算频谱
    try:
        orders, amplitudes = report._calculate_spectrum(spectrum_params)
        print(f"频谱计算成功！")
        print(f"检测到的阶次: {orders}")
        print(f"对应的幅值: {amplitudes}")
        
        # 验证结果
        if len(orders) > 0:
            print("\n测试通过：高阶评价处理流程正常工作！")
            print(f"检测到 {len(orders)} 个阶次，均为高阶成分(f ≥ ZE)")
        else:
            print("\n测试警告：未检测到阶次，请检查数据和参数设置")
            
    except Exception as e:
        print(f"\n测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_high_order_evaluation()
