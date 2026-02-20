#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
计算并显示频谱数据
"""

import os
import sys
import numpy as np
import math

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))

class MockBasicInfo:
    """模拟基本信息类"""
    
    def __init__(self):
        self.teeth = 87
        self.module = 1.0
        self.pressure_angle = 20.0
        self.helix_angle = 0.0

class SineFitParams:
    """正弦拟合参数类"""
    def __init__(self, curve_data, ze, max_order=500, max_components=50):
        self.curve_data = curve_data
        self.ze = ze
        self.max_order = max_order
        self.max_components = max_components

class SimpleSpectrumAnalyzer:
    """简单频谱分析器"""
    
    def _end_match(self, y):
        """端点匹配"""
        if y is None:
            return y
        y = np.asarray(y, dtype=float)
        if y.size <= 1:
            return y
        ramp = np.linspace(y[0], y[-1], y.size, dtype=float)
        return y - ramp
    
    def _calculate_rms(self, amplitudes):
        """计算RMS值"""
        if not amplitudes:
            return 0.0
        squared_amps = [amp ** 2 for amp in amplitudes]
        mean_squared = sum(squared_amps) / len(squared_amps)
        rms = math.sqrt(mean_squared)
        return rms
    
    def _sine_fit_spectrum_analysis(self, params):
        """正弦拟合频谱分析"""
        curve_data = params.curve_data
        ze = params.ze
        max_order = params.max_order
        max_components = params.max_components
        
        n = len(curve_data)
        if n < 8:
            return {}
        
        # 生成候选阶次
        candidate_orders = set()
        
        # 添加ZE及其倍数
        for multiple in range(1, 7):
            order = ze * multiple
            if 1 <= order <= max_order:
                candidate_orders.add(order)
        
        # 添加ZE附近的阶次
        for offset in range(-10, 11):
            order = ze + offset
            if 1 <= order <= max_order:
                candidate_orders.add(order)
        
        # 转换为排序后的列表
        candidate_orders = sorted(candidate_orders)
        
        # 创建旋转角x轴
        x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)
        
        # 对每个候选阶次单独拟合
        spectrum_results = {}
        min_amplitude_um = 0.001
        
        for order in candidate_orders:
            try:
                # 构建矩阵
                sin_x = np.sin(float(order) * x)
                cos_x = np.cos(float(order) * x)
                A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
                
                # 求解最小二乘
                try:
                    coeffs, _, _, _ = np.linalg.lstsq(A, curve_data, rcond=None)
                    a, b, c = coeffs
                except:
                    # 备选方法
                    a = 2.0 * np.mean(curve_data * sin_x)
                    b = 2.0 * np.mean(curve_data * cos_x)
                    c = np.mean(curve_data)
                
                # 计算幅值
                amplitude = float(np.sqrt(a * a + b * b))
                
                # 检查幅值是否合理
                max_reasonable_amplitude = 10.0
                if amplitude > max_reasonable_amplitude:
                    continue
                
                if amplitude > min_amplitude_um:
                    spectrum_results[order] = amplitude
            except:
                continue
        
        if not spectrum_results:
            return {}
        
        # 按幅值排序，取前15个
        sorted_items = sorted(spectrum_results.items(), key=lambda x: x[1], reverse=True)
        top_items = sorted_items[:15]
        
        # 过滤掉振幅接近零的阶次
        filtered_items = [(order, amp) for order, amp in top_items if amp >= 0.001 and amp <= 10.0]
        
        # 确保包含ZE及其倍数阶次
        final_items = []
        ze_orders_included = set()
        
        # 首先添加ZE及其倍数阶次
        for order, amp in filtered_items:
            if order in [ze * i for i in range(1, 7)] or order == ze:
                final_items.append((order, amp))
                ze_orders_included.add(order)
        
        # 然后添加其他阶次
        for order, amp in filtered_items:
            if order not in ze_orders_included:
                final_items.append((order, amp))
        
        # 限制最多15个阶次
        final_items = final_items[:15]
        result_dict = dict(final_items)
        
        return result_dict
    
    def calculate_spectrum(self, data_dict, teeth_count):
        """计算频谱"""
        # 处理数据
        all_tooth_data = []
        
        for tooth_id, values in data_dict.items():
            if values is not None:
                vals = np.array(values, dtype=float)
                if len(vals) >= 8:
                    # 去均值
                    vals = vals - np.mean(vals)
                    # 端点匹配
                    vals = self._end_match(vals)
                    all_tooth_data.append(vals)
        
        if not all_tooth_data:
            return np.array([]), np.array([]), 0.0
        
        # 计算平均曲线
        min_len = min(len(d) for d in all_tooth_data)
        aligned_data = [d[:min_len] for d in all_tooth_data]
        avg_data = np.mean(aligned_data, axis=0)
        
        # 使用正弦拟合方法计算频谱
        params = SineFitParams(
            curve_data=avg_data,
            ze=teeth_count,
            max_order=7 * teeth_count,
            max_components=15
        )
        
        spectrum_results = self._sine_fit_spectrum_analysis(params)
        
        if not spectrum_results:
            # 使用默认值
            default_orders = []
            default_amplitudes = []
            for multiple in range(1, 7):
                order = teeth_count * multiple
                default_orders.append(order)
                default_amplitudes.append(0.01)
            orders = np.array(default_orders, dtype=int)
            amplitudes = np.array(default_amplitudes, dtype=float)
        else:
            orders = np.array(sorted(spectrum_results.keys()), dtype=int)
            amplitudes = np.array([spectrum_results[o] for o in orders], dtype=float)
        
        # 计算RMS值
        rms_value = self._calculate_rms(amplitudes.tolist())
        
        return orders, amplitudes, rms_value

# 生成模拟数据
def generate_mock_data(teeth_count=87, num_teeth=5, points_per_tooth=100):
    """生成模拟数据"""
    data = {}
    for tooth_id in range(num_teeth):
        x = np.linspace(0, 2 * np.pi, points_per_tooth)
        y = 0.1 * np.sin(teeth_count * x) + 0.05 * np.sin(2 * teeth_count * x) + 0.02 * np.sin(3 * teeth_count * x)
        y += 0.01 * np.random.randn(len(x))  # 添加噪声
        data[tooth_id] = y.tolist()
    return data

# 主程序
if __name__ == "__main__":
    print("=== 频谱数据计算 ===")
    print()
    
    # 设置参数
    teeth_count = 87
    print(f"齿数 (ZE): {teeth_count}")
    print()
    
    # 生成模拟数据
    mock_data = generate_mock_data(teeth_count)
    print(f"生成了 {len(mock_data)} 个齿的模拟数据")
    print()
    
    # 创建频谱分析器
    analyzer = SimpleSpectrumAnalyzer()
    
    # 计算频谱
    print("计算频谱...")
    orders, amplitudes, rms_value = analyzer.calculate_spectrum(mock_data, teeth_count)
    
    # 显示结果
    print(f"\n计算得到 {len(orders)} 个阶次")
    print(f"RMS值: {rms_value:.4f} μm")
    print("\n阶次 | 幅值 (μm)")
    print("-" * 25)
    
    # 按阶次排序显示
    sorted_pairs = sorted(zip(orders, amplitudes), key=lambda x: x[0])
    for order, amp in sorted_pairs:
        print(f"{order:5d} | {amp:.4f}")
    
    # 显示ZE倍数的阶次
    print("\n=== ZE倍数阶次 ===")
    print("阶次 | 幅值 (μm)")
    print("-" * 25)
    
    for order, amp in sorted_pairs:
        if order % teeth_count == 0:
            multiple = order // teeth_count
            print(f"{order:5d} ({multiple}ZE) | {amp:.4f}")
    
    print()
    print("=== 计算完成 ===")

