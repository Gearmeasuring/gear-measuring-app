#!/usr/bin/env python3
"""
测试闭合曲线生成
生成并显示基圆映射后的闭合曲线图表
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

# 直接导入 gear_analysis_refactored 中的类
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport
from types import SimpleNamespace

# 模拟设置类
class MockSettings:
    def __init__(self):
        self.profile_helix_settings = {
            'detrend_settings': {'enabled': True},
            'filter_params': {'enabled': True},
            'order_filtering': {'max_order': 500}
        }
        self.display_settings = {
            'table_settings': {'max_components': 10}
        }

# 创建设置实例
settings = MockSettings()


class MockMeasurementData:
    """模拟测量数据对象"""
    
    def __init__(self):
        # 基本信息
        self.basic_info = SimpleNamespace(
            teeth=20,
            module=1.0,
            pressure_angle=20.0,
            helix_angle=0.0,
            profile_markers_left=[0.0, 0.2, 0.8, 1.0],
            profile_markers_right=[0.0, 0.2, 0.8, 1.0],
            lead_markers_left=[0.0, 0.2, 0.8, 1.0],
            lead_markers_right=[0.0, 0.2, 0.8, 1.0]
        )
        
        # 生成测试数据
        self.profile_data = SimpleNamespace(
            left=self._generate_test_data(),
            right=self._generate_test_data()
        )
        
        self.flank_data = SimpleNamespace(
            left=self._generate_test_data(),
            right=self._generate_test_data()
        )
    
    def _generate_test_data(self):
        """生成测试数据"""
        data = {}
        for tooth_id in range(1, 21):  # 20个齿
            # 生成带有噪声的正弦波数据
            n_points = 100
            x = np.linspace(0, 1, n_points)
            # 主频率为20（齿数）
            y = 0.5 * np.sin(2 * np.pi * 20 * x) + 0.1 * np.sin(2 * np.pi * 60 * x) + np.random.normal(0, 0.05, n_points)
            data[tooth_id] = y
        return data


def test_closed_curve_generation():
    """测试闭合曲线生成"""
    print("=== 测试闭合曲线生成 ===")
    
    # 创建频谱报告对象
    spectrum_report = KlingelnbergRippleSpectrumReport()
    
    # 创建模拟测量数据
    measurement_data = MockMeasurementData()
    
    # 测试齿形数据的闭合曲线生成
    print("\n--- 测试齿形数据闭合曲线生成 ---")
    try:
        # 获取齿形数据
        profile_data = measurement_data.profile_data.left
        all_tooth_data = []
        for tooth_id, values in profile_data.items():
            all_tooth_data.append(values)
        
        # 计算闭合曲线
        info = measurement_data.basic_info
        eval_length = 1.0
        base_diameter = spectrum_report._get_base_diameter(info)
        teeth_count = info.teeth
        
        print(f"基圆直径: {base_diameter:.4f}")
        print(f"齿数: {teeth_count}")
        print(f"评价长度: {eval_length}")
        
        # 生成闭合曲线
        closed_curve = spectrum_report._build_common_closed_curve_angle(
            all_tooth_data, 
            eval_length, 
            base_diameter, 
            teeth_count, 
            info=info
        )
        
        if closed_curve is not None:
            print(f"齿形闭合曲线长度: {len(closed_curve)}")
            print(f"齿形闭合曲线范围: [{np.min(closed_curve):.4f}, {np.max(closed_curve):.4f}]")
            
            # 绘制齿形闭合曲线
            plt.figure(figsize=(12, 6))
            plt.subplot(121)
            plt.plot(closed_curve)
            plt.title('Profile Closed Curve')
            plt.xlabel('Angle (degrees)')
            plt.ylabel('Deviation (μm)')
            plt.grid(True)
        else:
            print("无法生成齿形闭合曲线")
    except Exception as e:
        print(f"测试齿形闭合曲线失败: {e}")
    
    # 测试齿向数据的闭合曲线生成
    print("\n--- 测试齿向数据闭合曲线生成 ---")
    try:
        # 获取齿向数据
        flank_data = measurement_data.flank_data.left
        all_tooth_data = []
        for tooth_id, values in flank_data.items():
            all_tooth_data.append(values)
        
        # 计算闭合曲线
        closed_curve = spectrum_report._build_helix_closed_curve_angle(
            all_tooth_data, 
            eval_length, 
            base_diameter, 
            teeth_count, 
            info=info
        )
        
        if closed_curve is not None:
            print(f"齿向闭合曲线长度: {len(closed_curve)}")
            print(f"齿向闭合曲线范围: [{np.min(closed_curve):.4f}, {np.max(closed_curve):.4f}]")
            
            # 绘制齿向闭合曲线
            plt.subplot(122)
            plt.plot(closed_curve)
            plt.title('Flank Closed Curve')
            plt.xlabel('Angle (degrees)')
            plt.ylabel('Deviation (μm)')
            plt.grid(True)
        else:
            print("无法生成齿向闭合曲线")
    except Exception as e:
        print(f"测试齿向闭合曲线失败: {e}")
    
    # 测试基圆映射后的闭合曲线
    print("\n--- 测试基圆映射后的闭合曲线 ---")
    try:
        # 使用 _analyze_evaluation_range_spectrum 方法，该方法使用基圆映射
        spectrum_results = spectrum_report._analyze_evaluation_range_spectrum(measurement_data, 'profile', 'left')
        
        if spectrum_results:
            print("基圆映射频谱分析成功:")
            for order, amp in sorted(spectrum_results.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  阶次 {order}: 幅值 {amp:.4f} μm")
        else:
            print("基圆映射频谱分析失败")
    except Exception as e:
        print(f"测试基圆映射失败: {e}")
    
    # 显示图表
    plt.tight_layout()
    plt.savefig('closed_curve_test.png', dpi=150, bbox_inches='tight')
    print("\n=== 测试完成 ===")
    print("闭合曲线图表已保存为 'closed_curve_test.png'")


if __name__ == '__main__':
    test_closed_curve_generation()
