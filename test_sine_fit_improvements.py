#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试拟合正弦曲线改进功能

验证以下功能：
1. O1 标识具有最大振幅的第一主导阶次
2. 将具有该阶次和振幅的拟合正弦绘制到测量曲线中
3. 以主导阶次减少曲线，从剩余的偏差确定新的最大阶次和频谱
4. 如果同时显示 2 个阶次，则仅绘制第二个阶次的拟合正弦
5. 叠加正弦曲线功能，绘制从其他阶次的正弦函数得出的拟合曲线
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath('.'))

# 模拟日志模块
class MockLogger:
    def info(self, msg):
        print(f"INFO: {msg}")
    def warning(self, msg):
        print(f"WARNING: {msg}")
    def debug(self, msg):
        print(f"DEBUG: {msg}")

# 替换模块
import types
mock_logger_module = types.ModuleType('config.logging_config')
mock_logger_module.logger = MockLogger()
sys.modules['config.logging_config'] = mock_logger_module

# 现在导入 KlingelnbergSineFitReport
try:
    from gear_analysis_refactored.reports.klingelnberg_sine_fit import KlingelnbergSineFitReport
    print("成功导入 KlingelnbergSineFitReport")
except Exception as e:
    print(f"导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

class MockInfo:
    """模拟基本信息对象"""
    def __init__(self):
        self.base_diameter = 100.0  # 基圆直径
        self.teeth_count = 87  # 齿数
        self.module = 1.0  # 模数
        self.profile_angle = 20.0  # 压力角
        self.helix_angle = 15.0  # 螺旋角


def generate_test_data(n=1000, noise_level=0.02):
    """生成测试数据，包含多个正弦分量"""
    x = np.linspace(0, 10, n)
    
    # 生成多个正弦分量
    # 主导分量（O1）
    component1 = 0.1 * np.sin(2 * np.pi * 5 * x)  # 5阶
    # 次要分量（O2）
    component2 = 0.05 * np.sin(2 * np.pi * 10 * x + 0.5)  # 10阶
    # 更小的分量
    component3 = 0.02 * np.sin(2 * np.pi * 15 * x + 1.0)  # 15阶
    
    # 添加噪声
    noise = noise_level * np.random.randn(n)
    
    # 合成数据
    data = component1 + component2 + component3 + noise
    
    return data, x, component1, component2, component3


def test_sine_fit_improvements():
    """测试拟合正弦曲线改进功能"""
    print("=== 测试拟合正弦曲线改进功能 ===")
    
    # 生成测试数据
    n = 1000
    data, x, component1, component2, component3 = generate_test_data(n)
    
    # 创建模拟信息对象
    info = MockInfo()
    
    # 创建报告对象
    report = KlingelnbergSineFitReport()
    
    # 测试1：计算主导正弦分量
    print("\n=== 测试1：计算主导正弦分量 ===")
    try:
        result = report._calculate_dominant_sine(data, info, "profile", teeth_count=info.teeth_count)
        print(f"O1: {result['O1']}, A1: {result['A1']:.4f}")
        print(f"O2: {result['O2']}, A2: {result['A2']:.4f}")
    except Exception as e:
        print(f"计算主导正弦分量失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试2：计算多个阶次的正弦分量
    print("\n=== 测试2：计算多个阶次的正弦分量 ===")
    try:
        result_multi = report._calculate_dominant_sine(data, info, "profile", teeth_count=info.teeth_count, max_orders=3)
        print(f"O1: {result_multi.get('O1', 'N/A')}, A1: {result_multi.get('A1', 'N/A'):.4f}")
        print(f"O2: {result_multi.get('O2', 'N/A')}, A2: {result_multi.get('A2', 'N/A'):.4f}")
        print(f"O3: {result_multi.get('O3', 'N/A')}, A3: {result_multi.get('A3', 'N/A'):.4f}")
    except Exception as e:
        print(f"计算多个阶次的正弦分量失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 绘制结果
    print("\n=== 绘制结果 ===")
    try:
        plt.figure(figsize=(15, 10))
        
        # 子图1：原始数据和O1拟合
        plt.subplot(3, 1, 1)
        plt.plot(x, data, 'r-', label='原始数据', linewidth=1)
        if 'sine_fit' in result:
            plt.plot(x, result['sine_fit'], 'b-', label='O1拟合正弦', linewidth=1)
        plt.legend()
        plt.title('原始数据和O1拟合正弦')
        
        # 子图2：原始数据和O2拟合
        plt.subplot(3, 1, 2)
        plt.plot(x, data, 'r-', label='原始数据', linewidth=1)
        if 'sine_fit_o2' in result:
            plt.plot(x, result['sine_fit_o2'], 'g-', label='O2拟合正弦', linewidth=1)
        plt.legend()
        plt.title('原始数据和O2拟合正弦')
        
        # 子图3：原始数据和叠加拟合
        plt.subplot(3, 1, 3)
        plt.plot(x, data, 'r-', label='原始数据', linewidth=1)
        if 'sine_fit_combined' in result:
            plt.plot(x, result['sine_fit_combined'], 'm-', label='叠加拟合正弦 (O1+O2)', linewidth=1)
        # 绘制真实分量
        plt.plot(x, component1 + component2, 'c--', label='真实分量 (O1+O2)', linewidth=1)
        plt.legend()
        plt.title('原始数据和叠加拟合正弦')
        
        plt.tight_layout()
        plt.savefig('sine_fit_test_results.png')
        print("绘制结果已保存为 sine_fit_test_results.png")
        
        # 计算拟合误差
        if 'sine_fit_combined' in result:
            error = np.mean(np.abs(data - result['sine_fit_combined']))
            print(f"\n叠加拟合正弦的平均误差: {error:.4f}")
    except Exception as e:
        print(f"绘制结果失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_sine_fit_improvements()
