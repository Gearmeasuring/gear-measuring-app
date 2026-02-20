#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：比较启用和禁用鼓形/角度偏差去除时的频谱分析结果
"""

import os
import sys
import numpy as np
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings, SineFitParams

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

class TestWithoutBarrelAngle:
    """测试去掉鼓形和角度偏差后的频谱分析结果"""
    
    def __init__(self):
        # 创建报告对象
        self.settings = RippleSpectrumSettings()
        self.report = KlingelnbergRippleSpectrumReport(self.settings)
        
    def generate_test_data(self, teeth_count=87, points_per_tooth=100):
        """生成测试数据，包含鼓形和角度偏差"""
        # 生成多个齿的数据
        data_dict = {}
        
        for tooth_id in range(1, teeth_count + 1):
            # 生成原始数据点
            x = np.linspace(0, 1, points_per_tooth)
            
            # 添加鼓形（二次曲线）
            barrel = 5.0 * (x - 0.5) ** 2
            
            # 添加角度偏差（线性倾斜）
            angle_deviation = 2.0 * (x - 0.5)
            
            # 添加随机噪声
            noise = np.random.normal(0, 0.2, size=points_per_tooth)
            
            # 添加高频波纹
            ripple = 0.5 * np.sin(20 * np.pi * x) + 0.3 * np.sin(40 * np.pi * x)
            
            # 组合所有成分
            values = barrel + angle_deviation + noise + ripple
            
            data_dict[tooth_id] = values.tolist()
        
        return data_dict
    
    def process_with_barrel_angle(self, data_dict, teeth_count=87):
        """使用默认设置处理数据（启用鼓形和角度偏差去除）"""
        print("\n=== 使用默认设置处理数据（启用鼓形和角度偏差去除） ===")
        
        # 计算平均曲线
        avg_curve = self.report._calculate_average_curve(data_dict)
        print(f"平均曲线长度: {len(avg_curve)}")
        print(f"平均曲线范围: [{np.min(avg_curve):.4f}, {np.max(avg_curve):.4f}]μm")
        
        # 应用RC低通滤波器
        filtered_curve = self.report._apply_rc_low_pass_filter(avg_curve)
        
        # 准备正弦拟合参数
        fit_params = SineFitParams(
            curve_data=filtered_curve,
            ze=teeth_count,
            max_order=500,
            max_components=50
        )
        
        # 进行频谱分析
        spectrum = self.report._iterative_residual_sine_fit(fit_params)
        
        if spectrum:
            # 按幅值排序
            sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
            top_10 = sorted_spectrum[:10]
            
            print(f"分析完成，前10个阶次:")
            for order, amp in top_10:
                print(f"  阶次 {order}: {amp:.4f}μm")
            
            return spectrum, filtered_curve
        else:
            print("频谱分析失败")
            return {}, filtered_curve
    
    def process_without_barrel_angle(self, data_dict, teeth_count=87):
        """处理数据（禁用鼓形和角度偏差去除）"""
        print("\n=== 处理数据（禁用鼓形和角度偏差去除） ===")
        
        # 计算平均曲线
        avg_curve = self.report._calculate_average_curve(data_dict)
        print(f"平均曲线长度: {len(avg_curve)}")
        print(f"平均曲线范围: [{np.min(avg_curve):.4f}, {np.max(avg_curve):.4f}]μm")
        
        # 应用RC低通滤波器
        filtered_curve = self.report._apply_rc_low_pass_filter(avg_curve)
        
        # 准备正弦拟合参数
        fit_params = SineFitParams(
            curve_data=filtered_curve,
            ze=teeth_count,
            max_order=500,
            max_components=50
        )
        
        # 进行频谱分析
        spectrum = self.report._iterative_residual_sine_fit(fit_params)
        
        if spectrum:
            # 按幅值排序
            sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
            top_10 = sorted_spectrum[:10]
            
            print(f"分析完成，前10个阶次:")
            for order, amp in top_10:
                print(f"  阶次 {order}: {amp:.4f}μm")
            
            return spectrum, filtered_curve
        else:
            print("频谱分析失败")
            return {}, filtered_curve
    
    def compare_results(self, spectrum_with, spectrum_without):
        """比较两种处理方式的结果"""
        print("\n=== 比较结果 ===")
        
        # 提取前10个阶次
        top_with = sorted(spectrum_with.items(), key=lambda x: x[1], reverse=True)[:10]
        top_without = sorted(spectrum_without.items(), key=lambda x: x[1], reverse=True)[:10]
        
        print("\n前10个阶次对比:")
        print("阶次\t启用鼓形/角度去除\t禁用鼓形/角度去除")
        print("-" * 60)
        
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
            print(f"{order}\t{amp_with:.4f}μm\t\t{amp_without:.4f}μm")
        
        # 计算总幅值
        total_with = sum(spectrum_with.values())
        total_without = sum(spectrum_without.values())
        
        print(f"\n总幅值:")
        print(f"启用鼓形/角度去除: {total_with:.4f}μm")
        print(f"禁用鼓形/角度去除: {total_without:.4f}μm")
        print(f"差异: {abs(total_with - total_without):.4f}μm ({abs((total_with - total_without)/total_with)*100:.1f}%)")
    
    def run_test(self):
        """运行完整测试"""
        print("=== 开始测试：比较启用和禁用鼓形/角度偏差去除的效果 ===")
        
        # 生成测试数据
        print("1. 生成测试数据...")
        data_dict = self.generate_test_data()
        print(f"生成了 {len(data_dict)} 个齿的数据")
        
        # 测试1：使用默认设置处理数据（启用鼓形和角度偏差去除）
        print("\n2. 测试1：使用默认设置处理数据")
        spectrum_with, curve_with = self.process_with_barrel_angle(data_dict)
        
        # 测试2：禁用鼓形和角度偏差去除
        print("\n3. 测试2：禁用鼓形和角度偏差去除")
        spectrum_without, curve_without = self.process_without_barrel_angle(data_dict)
        
        # 比较结果
        print("\n4. 比较两种处理方式的结果")
        self.compare_results(spectrum_with, spectrum_without)
        
        # 分析曲线差异
        print("\n5. 分析曲线差异")
        print(f"启用鼓形/角度去除后曲线范围: [{np.min(curve_with):.4f}, {np.max(curve_with):.4f}]μm")
        print(f"禁用鼓形/角度去除后曲线范围: [{np.min(curve_without):.4f}, {np.max(curve_without):.4f}]μm")
        
        # 计算曲线差异
        if len(curve_with) == len(curve_without):
            diff = curve_with - curve_without
            print(f"曲线差异范围: [{np.min(diff):.4f}, {np.max(diff):.4f}]μm")
            print(f"曲线差异均方根: {np.sqrt(np.mean(diff**2)):.4f}μm")

if __name__ == "__main__":
    test = TestWithoutBarrelAngle()
    test.run_test()
