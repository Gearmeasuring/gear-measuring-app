#!/usr/bin/env python
"""
测试非等距点处理功能
验证迭代残差法正弦拟合频谱分析在非等距点情况下的性能
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# 添加项目根目录到路径
sys.path.append(os.path.abspath('gear_analysis_refactored'))

# 导入必要的模块
from reports.klingelnberg_ import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings, SineFitParams

class NonUniformPointsTest:
    """非等距点处理测试类"""
    
    def __init__(self):
        """初始化测试类"""
        self.settings = RippleSpectrumSettings()
        self.report = KlingelnbergRippleSpectrumReport(settings=self.settings)
    
    def generate_test_data(self, n_points=200, non_uniformity=0.1):
        """
        生成测试数据，包含多个频率分量和非等距的x坐标
        
        Args:
            n_points: 数据点数量
            non_uniformity: 非均匀性程度
            
        Returns:
            tuple: (x_coords, y_data)
        """
        # 生成非等距的x坐标
        # 基础等距坐标
        x_uniform = np.linspace(0, 1, n_points, dtype=float)
        # 添加非线性变化，模拟实际测量中的角度偏差
        x_non_uniform = x_uniform + non_uniformity * np.sin(4 * np.pi * x_uniform) + 0.5 * non_uniformity * np.sin(8 * np.pi * x_uniform)
        # 归一化到0-1范围
        x_non_uniform = (x_non_uniform - np.min(x_non_uniform)) / (np.max(x_non_uniform) - np.min(x_non_uniform))
        
        # 生成包含多个频率分量的y数据
        y_data = 0.5 * np.sin(2 * np.pi * 10 * x_non_uniform)  # 10Hz分量
        y_data += 0.3 * np.sin(2 * np.pi * 20 * x_non_uniform)  # 20Hz分量
        y_data += 0.2 * np.sin(2 * np.pi * 30 * x_non_uniform)  # 30Hz分量
        y_data += 0.1 * np.sin(2 * np.pi * 40 * x_non_uniform)  # 40Hz分量
        y_data += 0.05 * np.random.randn(n_points)  # 噪声
        
        return x_non_uniform, y_data
    
    def test_non_uniform_vs_uniform(self):
        """测试非等距点与等距点处理的对比"""
        print("=== 测试非等距点与等距点处理的对比 ===")
        
        # 生成测试数据
        x_non_uniform, y_data = self.generate_test_data(n_points=200, non_uniformity=0.1)
        
        # 生成等距x坐标作为对比
        x_uniform = np.linspace(0, 1, len(y_data), dtype=float)
        
        print(f"测试数据长度: {len(y_data)}")
        print(f"非等距x范围: {np.min(x_non_uniform):.4f} ~ {np.max(x_non_uniform):.4f}")
        print(f"数据范围: {np.min(y_data):.4f} ~ {np.max(y_data):.4f}")
        
        # 创建正弦拟合参数
        params = SineFitParams(
            curve_data=y_data,
            ze=87,  # 假设齿数为87
            max_order=100,  # 最大阶次
            max_components=10
        )
        
        # 1. 使用非等距坐标进行分析
        print("\n1. 使用非等距坐标进行分析:")
        spectrum_non_uniform = self.report._iterative_residual_sine_fit(params, x_coords=x_non_uniform)
        
        # 2. 使用等距坐标进行分析
        print("\n2. 使用等距坐标进行分析:")
        spectrum_uniform = self.report._iterative_residual_sine_fit(params, x_coords=x_uniform)
        
        # 显示结果对比
        print("\n=== 结果对比 ===")
        print("非等距坐标分析结果:")
        for order, amp in sorted(spectrum_non_uniform.items(), key=lambda x: x[1], reverse=True):
            print(f"阶次 {order}: 幅值 {amp:.4f}μm")
        
        print("\n等距坐标分析结果:")
        for order, amp in sorted(spectrum_uniform.items(), key=lambda x: x[1], reverse=True):
            print(f"阶次 {order}: 幅值 {amp:.4f}μm")
        
        # 可视化结果
        self._visualize_results(x_non_uniform, x_uniform, y_data, spectrum_non_uniform, spectrum_uniform)
    
    def _visualize_results(self, x_non_uniform, x_uniform, y_data, spectrum_non_uniform, spectrum_uniform):
        """可视化测试结果"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # 绘制原始数据（非等距坐标）
        ax1.plot(x_non_uniform, y_data, 'b-', linewidth=1.5)
        ax1.set_title('Original Data with Non-uniform Coordinates')
        ax1.set_xlabel('Non-uniform Coordinate')
        ax1.set_ylabel('Deviation (μm)')
        ax1.grid(True)
        
        # 绘制原始数据（等距坐标）
        ax2.plot(x_uniform, y_data, 'r-', linewidth=1.5)
        ax2.set_title('Original Data with Uniform Coordinates')
        ax2.set_xlabel('Uniform Coordinate')
        ax2.set_ylabel('Deviation (μm)')
        ax2.grid(True)
        
        # 绘制非等距坐标分析结果
        if spectrum_non_uniform:
            orders = list(spectrum_non_uniform.keys())
            amps = list(spectrum_non_uniform.values())
            ax3.bar(orders, amps, color='blue')
            ax3.set_title('Spectrum Analysis Result (Non-uniform Coordinates)')
            ax3.set_xlabel('Order')
            ax3.set_ylabel('Amplitude (μm)')
            ax3.grid(True)
        
        # 绘制等距坐标分析结果
        if spectrum_uniform:
            orders = list(spectrum_uniform.keys())
            amps = list(spectrum_uniform.values())
            ax4.bar(orders, amps, color='red')
            ax4.set_title('Spectrum Analysis Result (Uniform Coordinates)')
            ax4.set_xlabel('Order')
            ax4.set_ylabel('Amplitude (μm)')
            ax4.grid(True)
        
        plt.tight_layout()
        plt.savefig('non_uniform_points_test.png')
        print("\n测试结果已保存到 non_uniform_points_test.png")
    
    def test_different_non_uniformity_levels(self):
        """测试不同非均匀性程度对分析结果的影响"""
        print("\n=== 测试不同非均匀性程度对分析结果的影响 ===")
        
        non_uniformity_levels = [0.0, 0.05, 0.1, 0.15, 0.2]
        results = {}
        
        for level in non_uniformity_levels:
            print(f"\n测试非均匀性程度: {level}")
            
            # 生成测试数据
            x_non_uniform, y_data = self.generate_test_data(n_points=200, non_uniformity=level)
            
            # 创建正弦拟合参数
            params = SineFitParams(
                curve_data=y_data,
                ze=87,
                max_order=100,
                max_components=10
            )
            
            # 执行分析
            spectrum = self.report._iterative_residual_sine_fit(params, x_coords=x_non_uniform)
            results[level] = spectrum
            
            # 显示结果
            print("分析结果:")
            for order, amp in sorted(spectrum.items(), key=lambda x: x[1], reverse=True)[:5]:  # 只显示前5个
                print(f"阶次 {order}: 幅值 {amp:.4f}μm")
        
        # 可视化不同非均匀性程度的影响
        self._visualize_non_uniformity_effect(results)
    
    def _visualize_non_uniformity_effect(self, results):
        """可视化不同非均匀性程度的影响"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 绘制不同非均匀性程度的结果
        colors = plt.cm.tab10(np.linspace(0, 1, len(results)))
        
        for i, (level, spectrum) in enumerate(results.items()):
            if spectrum:
                orders = list(spectrum.keys())
                amps = list(spectrum.values())
                # 绘制条形图，使用不同的颜色
                ax.bar(np.array(orders) + i * 0.1, amps, width=0.1, label=f'Non-uniformity: {level}', color=colors[i])
        
        ax.set_title('Effect of Different Non-uniformity Levels on Spectrum Analysis')
        ax.set_xlabel('Order')
        ax.set_ylabel('Amplitude (μm)')
        ax.legend()
        ax.grid(True)
        
        plt.tight_layout()
        plt.savefig('non_uniformity_effect.png')
        print("\n不同非均匀性程度的影响已保存到 non_uniformity_effect.png")

def main():
    """主函数"""
    print("=== 非等距点处理功能测试 ===")
    print("测试迭代残差法正弦拟合频谱分析在非等距点情况下的性能")
    
    test = NonUniformPointsTest()
    
    # 测试1：非等距点与等距点处理的对比
    test.test_non_uniform_vs_uniform()
    
    # 测试2：不同非均匀性程度对分析结果的影响
    test.test_different_non_uniformity_levels()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()
