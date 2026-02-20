#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本：比较启用和禁用鼓形/角度偏差去除时的频谱分析结果
"""

import numpy as np

class SimpleTest:
    """简单测试类，测试迭代残差法正弦拟合"""
    
    def __init__(self):
        pass
    
    def generate_test_data(self, points=1000):
        """生成测试数据，包含鼓形和角度偏差"""
        # 生成原始数据点
        x = np.linspace(0, 1, points)
        
        # 添加鼓形（二次曲线）
        barrel = 5.0 * (x - 0.5) ** 2
        
        # 添加角度偏差（线性倾斜）
        angle_deviation = 2.0 * (x - 0.5)
        
        # 添加随机噪声
        noise = np.random.normal(0, 0.2, size=points)
        
        # 添加高频波纹
        ripple = 0.5 * np.sin(20 * np.pi * x) + 0.3 * np.sin(40 * np.pi * x)
        
        # 组合所有成分
        values = barrel + angle_deviation + noise + ripple
        
        return values, x
    
    def iterative_residual_sine_fit(self, curve_data, max_order=500, max_iterations=5, amplitude_threshold=0.01):
        """迭代残差法正弦拟合频谱分析"""
        n = len(curve_data)
        if n < 8:
            return {}
        
        # 生成时间坐标x轴（0到1秒，假设转速为1转/秒）
        x = np.linspace(0.0, 1.0, n, dtype=float)
        
        # 初始化残差信号为原始信号
        residual = np.array(curve_data, dtype=float)
        
        # 存储提取的频谱分量
        spectrum_results = {}
        
        for iteration in range(max_iterations):
            print(f"迭代 {iteration + 1}/{max_iterations}")
            
            # 生成候选阶次：直接使用频率值
            candidate_orders = list(range(1, max_order + 1))
            
            # 存储所有候选阶次的拟合结果
            order_amplitudes = {}
            
            for order in candidate_orders:
                try:
                    # 直接使用order作为频率值
                    frequency = float(order)
                    
                    # 构建矩阵 A = [sin(2π*f*x), cos(2π*f*x), 1]
                    sin_x = np.sin(2.0 * np.pi * frequency * x)
                    cos_x = np.cos(2.0 * np.pi * frequency * x)
                    A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
                    
                    # 求解最小二乘
                    try:
                        coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                        a, b, c = coeffs
                    except Exception as e:
                        # 如果最小二乘失败，使用备选方法
                        a = 2.0 * np.mean(residual * sin_x)
                        b = 2.0 * np.mean(residual * cos_x)
                        c = np.mean(residual)
                    
                    # 计算幅值：A = sqrt(a^2 + b^2)
                    amplitude = float(np.sqrt(a * a + b * b))
                    
                    # 检查幅值是否合理
                    max_reasonable_amplitude = 10.0
                    if amplitude > max_reasonable_amplitude:
                        continue
                    
                    # 存储拟合结果
                    order_amplitudes[order] = (amplitude, a, b, c)
                    
                except Exception as e:
                    continue
            
            # 选择幅值最大的频率
            if not order_amplitudes:
                break
            
            best_order = max(order_amplitudes.keys(), key=lambda o: order_amplitudes[o][0])
            best_amplitude, a, b, c = order_amplitudes[best_order]
            
            print(f"  选择频率 {best_order}，幅值 {best_amplitude:.4f}μm")
            
            # 检查幅值是否小于阈值
            if best_amplitude < amplitude_threshold:
                print(f"  幅值小于阈值 {amplitude_threshold}μm，停止迭代")
                break
            
            # 保存提取的频谱分量
            spectrum_results[best_order] = best_amplitude
            
            # 从残差信号中移除已提取的正弦波
            best_frequency = float(best_order)
            fitted_wave = a * np.sin(2.0 * np.pi * best_frequency * x) + b * np.cos(2.0 * np.pi * best_frequency * x) + c
            residual = residual - fitted_wave
        
        return spectrum_results
    
    def remove_barrel_and_angle(self, curve_data):
        """去除鼓形和角度偏差"""
        x = np.linspace(0, 1, len(curve_data))
        
        # 去均值
        mean_val = np.mean(curve_data)
        detrended = curve_data - mean_val
        
        # 2阶多项式去除鼓形
        p2 = np.polyfit(x, detrended, 2)
        trend2 = np.polyval(p2, x)
        residual_after_p2 = detrended - trend2
        
        # 1阶多项式去除角度偏差
        p1 = np.polyfit(x, residual_after_p2, 1)
        linear_trend = np.polyval(p1, x)
        final_data = residual_after_p2 - linear_trend
        
        return final_data
    
    def run_test(self):
        """运行完整测试"""
        print("=== 开始测试：比较启用和禁用鼓形/角度偏差去除的效果 ===")
        
        # 生成测试数据
        print("1. 生成测试数据...")
        raw_data, x = self.generate_test_data()
        print(f"原始数据长度: {len(raw_data)}")
        print(f"原始数据范围: [{np.min(raw_data):.4f}, {np.max(raw_data):.4f}]μm")
        
        # 测试1：直接分析原始数据（包含鼓形和角度偏差）
        print("\n2. 测试1：直接分析原始数据（包含鼓形和角度偏差）")
        spectrum_with_barrel = self.iterative_residual_sine_fit(raw_data)
        
        # 测试2：分析去除鼓形和角度偏差后的数据
        print("\n3. 测试2：分析去除鼓形和角度偏差后的数据")
        processed_data = self.remove_barrel_and_angle(raw_data)
        print(f"处理后数据范围: [{np.min(processed_data):.4f}, {np.max(processed_data):.4f}]μm")
        spectrum_without_barrel = self.iterative_residual_sine_fit(processed_data)
        
        # 比较结果
        print("\n4. 比较两种处理方式的结果")
        self.compare_results(spectrum_with_barrel, spectrum_without_barrel)
    
    def compare_results(self, spectrum_with, spectrum_without):
        """比较两种处理方式的结果"""
        print("\n前10个阶次对比:")
        print("阶次\t包含鼓形和角度偏差\t去除鼓形和角度偏差")
        print("-" * 70)
        
        # 提取前10个阶次
        top_with = sorted(spectrum_with.items(), key=lambda x: x[1], reverse=True)[:10]
        top_without = sorted(spectrum_without.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 合并所有阶次
        all_orders = set()
        for order, _ in top_with:
            all_orders.add(order)
        for order, _ in top_without:
            all_orders.add(order)
        
        # 打印对比结果
        for order in sorted(all_orders)[:10]:
            amp_with = spectrum_with.get(order, 0.0)
            amp_without = spectrum_without.get(order, 0.0)
            print(f"{order}	{amp_with:.4f}μm		{amp_without:.4f}μm")
        
        # 计算总幅值
        total_with = sum(spectrum_with.values())
        total_without = sum(spectrum_without.values())
        
        print(f"\n总幅值:")
        print(f"包含鼓形和角度偏差: {total_with:.4f}μm")
        print(f"去除鼓形和角度偏差: {total_without:.4f}μm")
        print(f"差异: {abs(total_with - total_without):.4f}μm ({abs((total_with - total_without)/total_with)*100:.1f}%)")

if __name__ == "__main__":
    test = SimpleTest()
    test.run_test()
