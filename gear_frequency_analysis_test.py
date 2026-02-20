#!/usr/bin/env python3
"""
测试齿轮频率分析图表生成
生成类似参考图片的齿轮频率分析图表
"""

import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace


def generate_frequency_data(teeth_count=23, n_points=500):
    """生成不同频率成分的数据"""
    # 生成时间序列
    t = np.linspace(0, 1, n_points)
    
    # 生成不同频率成分
    data = {
        '1z': 0.307 * np.sin(2 * np.pi * 1 * teeth_count * t),  # 1倍齿数频率
        '2z': 0.26 * np.sin(2 * np.pi * 2 * teeth_count * t),   # 2倍齿数频率
        '3z': 0.46 * np.sin(2 * np.pi * 3 * teeth_count * t),   # 3倍齿数频率
        '4z': 0.27 * np.sin(2 * np.pi * 4 * teeth_count * t),   # 4倍齿数频率
        'noise': np.random.normal(0, 0.05, n_points)           # 噪声
    }
    
    # 计算合成信号
    data['total'] = data['1z'] + data['2z'] + data['3z'] + data['4z'] + data['noise']
    
    return data


def generate_high_frequency_data(teeth_count=23, n_points=500):
    """生成高频数据"""
    # 生成时间序列
    t = np.linspace(0, 1, n_points)
    
    # 生成不同频率成分
    data = {
        '1f': 0.36 * np.sin(2 * np.pi * 1 * teeth_count * t),   # 1倍齿数频率
        '2f': 0.1 * np.sin(2 * np.pi * 2 * teeth_count * t),    # 2倍齿数频率
        '3f': 0.08 * np.sin(2 * np.pi * 3 * teeth_count * t),    # 3倍齿数频率
        '4f': 0.06 * np.sin(2 * np.pi * 4 * teeth_count * t),    # 4倍齿数频率
        '5f': 0.05 * np.sin(2 * np.pi * 5 * teeth_count * t),    # 5倍齿数频率
        '6f': 0.04 * np.sin(2 * np.pi * 6 * teeth_count * t),    # 6倍齿数频率
        '7f': 0.03 * np.sin(2 * np.pi * 7 * teeth_count * t),    # 7倍齿数频率
        '8f': 0.02 * np.sin(2 * np.pi * 8 * teeth_count * t),    # 8倍齿数频率
        '9f': 0.02 * np.sin(2 * np.pi * 9 * teeth_count * t),    # 9倍齿数频率
        '10f': 0.01 * np.sin(2 * np.pi * 10 * teeth_count * t),   # 10倍齿数频率
        '11f': 0.01 * np.sin(2 * np.pi * 11 * teeth_count * t),   # 11倍齿数频率
        'noise': np.random.normal(0, 0.02, n_points)            # 噪声
    }
    
    # 计算合成信号
    data['total'] = (data['1f'] + data['2f'] + data['3f'] + data['4f'] + 
                    data['5f'] + data['6f'] + data['7f'] + data['8f'] + 
                    data['9f'] + data['10f'] + data['11f'] + data['noise'])
    
    return data


def plot_gear_frequency_analysis():
    """绘制齿轮频率分析图表"""
    print("=== 生成齿轮频率分析图表 ===")
    
    # 生成数据
    teeth_count = 23
    middle_freq_data = generate_frequency_data(teeth_count=teeth_count)
    high_freq_data = generate_high_frequency_data(teeth_count=teeth_count)
    
    # 创建图表
    fig = plt.figure(figsize=(12, 10))
    
    # 上部分：中频分析
    ax1 = fig.add_subplot(211)
    
    # 生成时间轴（0到1对应一个完整旋转）
    t = np.linspace(0, 1, len(middle_freq_data['total']))
    
    # 绘制不同频率成分
    colors = ['red', 'orange', 'blue', 'purple']
    freq_labels = ['1z', '2z', '3z', '4z']
    
    for i, freq in enumerate(freq_labels):
        ax1.plot(t, middle_freq_data[freq], color=colors[i], linewidth=1.0, alpha=0.7)
    
    # 绘制合成信号
    ax1.plot(t, middle_freq_data['total'], color='black', linewidth=1.2, alpha=0.9)
    
    # 添加标题和标签
    ax1.set_title(f'Type of evaluation "middle frequency" → no correction (z = {teeth_count})', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Deviation (mm)', fontsize=10)
    
    # 添加频率标记
    freq_positions = [0.1, 0.25, 0.4, 0.55, 0.7, 0.85]
    freq_texts = ['1z', '2z', '3z', '4z', '5z', '6z']
    for pos, text in zip(freq_positions, freq_texts):
        ax1.text(pos, 0.9, text, transform=ax1.transAxes, fontsize=8, ha='center')
    
    # 添加振幅刻度
    ax1.text(0.95, 0.9, '0.002 mm', transform=ax1.transAxes, fontsize=8, ha='right', 
             bbox=dict(boxstyle='square,pad=0.3', facecolor='white', edgecolor='black', linewidth=0.8))
    
    # 添加数据标签
    ax1.text(0.15, 0.8, 'A6 0.30', transform=ax1.transAxes, fontsize=8, ha='center')
    ax1.text(0.15, 0.75, 'T6 36', transform=ax1.transAxes, fontsize=8, ha='center')
    ax1.text(0.4, 0.8, 'A1 0.30', transform=ax1.transAxes, fontsize=8, ha='center')
    ax1.text(0.65, 0.8, '0.46', transform=ax1.transAxes, fontsize=8, ha='center')
    ax1.text(0.85, 0.8, '0.27', transform=ax1.transAxes, fontsize=8, ha='center')
    
    # 添加高频说明
    ax1.text(0.05, 0.1, '"high frequency" (≥ fz) → without crowning, slope & pitch', 
             transform=ax1.transAxes, fontsize=8, ha='left', color='orange')
    
    # 下部分：高频分析
    ax2 = fig.add_subplot(212)
    
    # 绘制高频数据
    t_high = np.linspace(0, 1, len(high_freq_data['total']))
    
    # 绘制不同频率成分
    high_freq_colors = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta', 'pink', 'brown', 'gray']
    high_freq_labels = ['1f', '2f', '3f', '4f', '5f', '6f', '7f', '8f', '9f', '10f', '11f']
    
    for i, freq in enumerate(high_freq_labels):
        ax2.plot(t_high, high_freq_data[freq], color=high_freq_colors[i], linewidth=0.8, alpha=0.6)
    
    # 绘制合成信号
    ax2.plot(t_high, high_freq_data['total'], color='black', linewidth=1.2, alpha=0.9)
    
    # 添加标题和标签
    ax2.set_title('"high frequency" (≥ fz) → without crowning, slope & pitch', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Deviation (mm)', fontsize=10)
    ax2.set_xlabel('Normalized Position', fontsize=10)
    
    # 添加频率标记
    high_freq_positions = [0.1, 0.18, 0.26, 0.34, 0.42, 0.5, 0.58, 0.66, 0.74, 0.82, 0.9]
    high_freq_texts = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
    for pos, text in zip(high_freq_positions, high_freq_texts):
        ax2.text(pos, 0.9, text, transform=ax2.transAxes, fontsize=7, ha='center')
    
    # 添加振幅刻度
    ax2.text(0.95, 0.9, '0.001 mm', transform=ax2.transAxes, fontsize=8, ha='right', 
             bbox=dict(boxstyle='square,pad=0.3', facecolor='white', edgecolor='black', linewidth=0.8))
    
    # 添加数据标签
    ax2.text(0.1, 0.8, 'A1 0.36', transform=ax2.transAxes, fontsize=8, ha='center')
    ax2.text(0.1, 0.75, 'f1 36', transform=ax2.transAxes, fontsize=8, ha='center')
    
    # 添加网格
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('gear_frequency_analysis_test.png', dpi=150, bbox_inches='tight')
    print("\n=== 图表生成完成 ===")
    print("齿轮频率分析图表已保存为 'gear_frequency_analysis_test.png'")


if __name__ == '__main__':
    plot_gear_frequency_analysis()
