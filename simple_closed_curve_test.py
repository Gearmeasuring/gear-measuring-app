#!/usr/bin/env python3
"""
简单测试闭合曲线生成
生成并显示闭合曲线图表
"""

import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace


def generate_test_data():
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


def build_closed_curve(data_dict, teeth_count):
    """构建闭合曲线"""
    all_data = []
    for tooth_id, values in data_dict.items():
        all_data.extend(values)
    
    # 计算闭合曲线
    closed_curve = np.array(all_data)
    
    # 去均值
    closed_curve = closed_curve - np.mean(closed_curve)
    
    return closed_curve


def plot_closed_curve():
    """绘制闭合曲线"""
    print("=== 生成闭合曲线图表 ===")
    
    # 生成测试数据
    profile_data = generate_test_data()
    flank_data = generate_test_data()
    
    # 构建闭合曲线
    teeth_count = 20
    profile_curve = build_closed_curve(profile_data, teeth_count)
    flank_curve = build_closed_curve(flank_data, teeth_count)
    
    print(f"齿形闭合曲线长度: {len(profile_curve)}")
    print(f"齿形闭合曲线范围: [{np.min(profile_curve):.4f}, {np.max(profile_curve):.4f}]")
    print(f"齿向闭合曲线长度: {len(flank_curve)}")
    print(f"齿向闭合曲线范围: [{np.min(flank_curve):.4f}, {np.max(flank_curve):.4f}]")
    
    # 绘制闭合曲线
    plt.figure(figsize=(12, 6))
    
    # 齿形闭合曲线
    plt.subplot(121)
    plt.plot(profile_curve)
    plt.title('Profile Closed Curve')
    plt.xlabel('Data Point')
    plt.ylabel('Deviation (μm)')
    plt.grid(True)
    
    # 齿向闭合曲线
    plt.subplot(122)
    plt.plot(flank_curve)
    plt.title('Flank Closed Curve')
    plt.xlabel('Data Point')
    plt.ylabel('Deviation (μm)')
    plt.grid(True)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('closed_curve_test.png', dpi=150, bbox_inches='tight')
    print("\n=== 图表生成完成 ===")
    print("闭合曲线图表已保存为 'closed_curve_test.png'")


if __name__ == '__main__':
    plot_closed_curve()
