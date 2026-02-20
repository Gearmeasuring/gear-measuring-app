#!/usr/bin/env python3
"""
测试基圆映射算法的闭合曲线生成
生成并显示基圆映射后的闭合曲线图表
"""

import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace


def generate_test_data(teeth_count=87):
    """生成测试数据"""
    data = {}
    for tooth_id in range(1, teeth_count + 1):  # 指定齿数
        # 生成带有噪声的正弦波数据
        n_points = 50  # 每个齿50个点，87个齿共4350个点
        x = np.linspace(0, 1, n_points)
        # 主频率为齿数，每个齿添加一个独特的偏移，使每个齿的特征更加明显
        # 为每个齿添加独特的相位偏移，使每个齿的特征不同
        phase_offset = (tooth_id - 1) * (2 * np.pi / teeth_count)
        # 主频率为齿数
        y = 0.5 * np.sin(2 * np.pi * teeth_count * x + phase_offset) + 0.1 * np.sin(2 * np.pi * 3 * teeth_count * x) + np.random.normal(0, 0.05, n_points)
        data[tooth_id] = y
    return data


def calculate_base_diameter(module, teeth, pressure_angle):
    """计算基圆直径"""
    pressure_angle_rad = np.radians(pressure_angle)
    base_diameter = module * teeth * np.cos(pressure_angle_rad)
    return base_diameter


def map_to_base_circle(data, base_diameter, teeth_count):
    """应用基圆映射算法"""
    # 计算基圆周长
    base_circumference = np.pi * base_diameter
    
    # 计算基节
    base_pitch = base_circumference / teeth_count
    
    # 应用基圆映射
    mapped_data = []
    for i, value in enumerate(data):
        # 计算当前点的旋转角度
        angle = 2 * np.pi * (i / len(data))
        
        # 基圆映射：角度保持不变，但幅值可能会有调整
        # 这里简化处理，主要展示角度映射
        mapped_data.append(value)
    
    return np.array(mapped_data)


def build_closed_curve(data_dict, teeth_count, use_base_circle=False, module=1.0, pressure_angle=20.0):
    """构建闭合曲线"""
    all_data = []
    for tooth_id, values in data_dict.items():
        all_data.extend(values)
    
    # 计算闭合曲线
    closed_curve = np.array(all_data)
    
    # 去均值
    closed_curve = closed_curve - np.mean(closed_curve)
    
    # 应用基圆映射
    if use_base_circle:
        base_diameter = calculate_base_diameter(module, teeth_count, pressure_angle)
        closed_curve = map_to_base_circle(closed_curve, base_diameter, teeth_count)
    
    return closed_curve


def plot_closed_curve_with_base_circle():
    """绘制带有基圆映射的闭合曲线"""
    print("=== 生成左齿形闭合曲线图表 ===")
    
    # 生成测试数据（左齿形），87个齿
    teeth_count = 87
    profile_data = generate_test_data(teeth_count=teeth_count)
    
    # 构建闭合曲线
    module = 1.0
    pressure_angle = 20.0
    
    # 计算基圆直径
    base_diameter = calculate_base_diameter(module, teeth_count, pressure_angle)
    print(f"基圆直径: {base_diameter:.4f}")
    
    # 生成普通闭合曲线
    profile_curve = build_closed_curve(profile_data, teeth_count, use_base_circle=False)
    
    # 生成基圆映射后的闭合曲线
    profile_curve_base = build_closed_curve(profile_data, teeth_count, use_base_circle=True, module=module, pressure_angle=pressure_angle)
    
    print(f"普通左齿形闭合曲线长度: {len(profile_curve)}")
    print(f"普通左齿形闭合曲线范围: [{np.min(profile_curve):.4f}, {np.max(profile_curve):.4f}]")
    print(f"基圆映射左齿形闭合曲线长度: {len(profile_curve_base)}")
    print(f"基圆映射左齿形闭合曲线范围: [{np.min(profile_curve_base):.4f}, {np.max(profile_curve_base):.4f}]")
    
    # 绘制闭合曲线
    plt.figure(figsize=(15, 8))
    
    # 生成0到360度的角度数据
    angle_range = np.linspace(0, 360, len(profile_curve))
    
    # 齿形闭合曲线
    plt.subplot(121)
    plt.plot(angle_range, profile_curve)
    plt.title('Left Profile Closed Curve (87 Teeth)')
    plt.xlabel('Angle (degrees)')
    plt.ylabel('Deviation (μm)')
    plt.grid(True)
    # 添加齿的标记线，每4度一条，这样87个齿大约每4度一个齿
    for i in range(0, 361, 4):
        plt.axvline(x=i, color='gray', linestyle='--', linewidth=0.5, alpha=0.3)
    
    # 基圆映射齿形闭合曲线
    plt.subplot(122)
    plt.plot(angle_range, profile_curve_base)
    plt.title('Left Profile Closed Curve (Base Circle Mapped, 87 Teeth)')
    plt.xlabel('Angle (degrees)')
    plt.ylabel('Deviation (μm)')
    plt.grid(True)
    # 添加齿的标记线
    for i in range(0, 361, 4):
        plt.axvline(x=i, color='gray', linestyle='--', linewidth=0.5, alpha=0.3)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('left_profile_closed_curve_87teeth_test.png', dpi=150, bbox_inches='tight')
    print("\n=== 图表生成完成 ===")
    print("左齿形闭合曲线图表已保存为 'left_profile_closed_curve_87teeth_test.png'")


if __name__ == '__main__':
    plot_closed_curve_with_base_circle()
