#!/usr/bin/env python3
"""
基于真实MKA数据生成齿轮频率分析图表
"""

import numpy as np
import matplotlib.pyplot as plt
from parse_mka_file import MKAParser
from scipy.signal import find_peaks


def remove_crowning(data):
    """
    去除鼓形误差
    使用二次多项式拟合来去除鼓形
    """
    # 提取数据值和角度
    angles = np.array([point[0] for point in data])
    values = np.array([point[1] for point in data])
    
    # 归一化角度到0-1范围
    t = (angles % 360) / 360.0
    
    # 拟合二次多项式
    coeffs = np.polyfit(t, values, 2)
    crowning = np.polyval(coeffs, t)
    
    # 去除鼓形
    values_no_crowning = values - crowning
    
    # 重新组合数据
    processed_data = [(angles[i], values_no_crowning[i]) for i in range(len(angles))]
    
    return processed_data


def remove_slope(data):
    """
    去除倾斜误差
    使用线性拟合来去除倾斜
    """
    # 提取数据值和角度
    angles = np.array([point[0] for point in data])
    values = np.array([point[1] for point in data])
    
    # 归一化角度到0-1范围
    t = (angles % 360) / 360.0
    
    # 拟合线性多项式
    coeffs = np.polyfit(t, values, 1)
    slope = np.polyval(coeffs, t)
    
    # 去除倾斜
    values_no_slope = values - slope
    
    # 重新组合数据
    processed_data = [(angles[i], values_no_slope[i]) for i in range(len(angles))]
    
    return processed_data


def preprocess_data(data):
    """
    数据预处理
    去除鼓形和倾斜
    """
    # 首先去除鼓形
    data_no_crowning = remove_crowning(data)
    # 然后去除倾斜
    data_processed = remove_slope(data_no_crowning)
    
    return data_processed


def calculate_frequency_components(data, teeth_count, max_harmonics=4):
    """
    从真实数据计算不同频率成分
    使用傅里叶变换分析频率成分
    """
    # 提取数据值
    values = np.array([point[1] for point in data])
    
    # 傅里叶变换
    n = len(values)
    fft_vals = np.fft.fft(values)
    fft_freqs = np.fft.fftfreq(n)
    
    # 只取正频率
    positive_freqs = fft_freqs[:n//2]
    positive_vals = np.abs(fft_vals[:n//2])
    
    # 计算基频 (齿数频率)
    fundamental_freq = teeth_count
    
    # 计算各次谐波的振幅
    freq_components = {}
    
    for i in range(1, max_harmonics + 1):
        target_freq = i * fundamental_freq
        # 找到最接近目标频率的索引
        idx = np.argmin(np.abs(positive_freqs - target_freq))
        
        # 搜索峰值
        peaks, _ = find_peaks(positive_vals)
        # 找到目标频率附近的峰值
        nearby_peaks = [peak for peak in peaks if abs(positive_freqs[peak] - target_freq) < 0.5]
        
        if nearby_peaks:
            # 取最近的峰值
            nearby_peaks.sort(key=lambda peak: abs(positive_freqs[peak] - target_freq))
            peak_idx = nearby_peaks[0]
            amplitude = positive_vals[peak_idx] / (n/2)  # 归一化
        else:
            # 如果没有找到峰值，使用最接近的点
            amplitude = positive_vals[idx] / (n/2)
        
        freq_components[f'{i}z'] = amplitude
    
    return freq_components


def generate_real_frequency_data(data, teeth_count, freq_components):
    """
    基于真实数据和计算出的频率成分生成合成信号
    """
    # 提取数据值和角度
    angles = np.array([point[0] for point in data])
    values = np.array([point[1] for point in data])
    
    # 归一化角度到0-1范围
    t = (angles % 360) / 360.0
    
    # 生成不同频率成分
    freq_data = {}
    
    for key, amplitude in freq_components.items():
        harmonic = int(key[0])
        freq_data[key] = amplitude * np.sin(2 * np.pi * harmonic * teeth_count * t)
    
    # 计算合成信号
    freq_data['total'] = values
    
    return freq_data


def plot_gear_frequency_analysis_real_data():
    """
    使用真实MKA数据绘制齿轮频率分析图表
    """
    print("=== 基于真实MKA数据生成齿轮频率分析图表 ===")
    
    # 读取MKA文件
    file_path = '263751-018-WAV.mka'
    parser = MKAParser(file_path)
    
    # 获取齿轮参数
    teeth_count = parser.get_teeth_count()
    if teeth_count == 0:
        teeth_count = 26  # 回退值
    
    print(f"齿轮齿数: {teeth_count}")
    print(f"模数: {parser.get_module()}")
    print(f"螺旋角: {parser.get_helix_angle()}")
    
    # 获取组合数据
    combined_data = parser.get_combined_data()
    
    # 使用左侧齿形数据进行分析
    profile_left_data = combined_data['profile_left']
    
    if not profile_left_data:
        print("错误: 没有找到左侧齿形数据")
        return
    
    print(f"左侧齿形数据点数量: {len(profile_left_data)}")
    
    # 数据预处理：去除鼓形和倾斜
    print("\n=== 数据预处理 ===")
    print("正在去除鼓形和倾斜...")
    processed_data = preprocess_data(profile_left_data)
    print("预处理完成！")
    
    # 计算频率成分
    max_harmonics_middle = 4  # 中频分析到4次谐波
    max_harmonics_high = 11    # 高频分析到11次谐波
    
    # 计算中频成分
    middle_freq_components = calculate_frequency_components(processed_data, teeth_count, max_harmonics_middle)
    print("\n中频成分振幅:")
    for key, amp in middle_freq_components.items():
        print(f"{key}: {amp:.3f}")
    
    # 计算高频成分
    high_freq_components = calculate_frequency_components(processed_data, teeth_count, max_harmonics_high)
    print("\n高频成分振幅:")
    for key, amp in high_freq_components.items():
        print(f"{key}: {amp:.3f}")
    
    # 生成频率数据
    middle_freq_data = generate_real_frequency_data(processed_data, teeth_count, middle_freq_components)
    high_freq_data = generate_real_frequency_data(processed_data, teeth_count, high_freq_components)
    
    # 创建图表
    fig = plt.figure(figsize=(12, 10))
    
    # 上部分：中频分析
    ax1 = fig.add_subplot(211)
    
    # 生成时间轴（0到1对应一个完整旋转）
    angles = np.array([point[0] for point in profile_left_data])
    t = (angles % 360) / 360.0
    
    # 绘制不同频率成分
    colors = ['red', 'orange', 'blue', 'purple']
    freq_labels = [f'{i}z' for i in range(1, max_harmonics_middle + 1)]
    
    for i, freq in enumerate(freq_labels):
        if freq in middle_freq_data:
            ax1.plot(t, middle_freq_data[freq], color=colors[i], linewidth=1.0, alpha=0.7)
    
    # 绘制合成信号（真实数据）
    ax1.plot(t, middle_freq_data['total'], color='black', linewidth=1.2, alpha=0.9)
    
    # 添加标题和标签
    ax1.set_title(f'Type of evaluation "middle frequency" → with crowning and slope correction (z = {teeth_count})', fontsize=12, fontweight='bold')
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
    for i, (key, amp) in enumerate(middle_freq_components.items()):
        if i < 4:  # 只显示前4个
            pos = 0.15 + i * 0.2
            ax1.text(pos, 0.8, f'{key} {amp:.3f}', transform=ax1.transAxes, fontsize=8, ha='center')
    
    # 添加高频说明
    ax1.text(0.05, 0.1, '"high frequency" (≥ fz) → without crowning, slope & pitch', 
             transform=ax1.transAxes, fontsize=8, ha='left', color='orange')
    
    # 下部分：高频分析
    ax2 = fig.add_subplot(212)
    
    # 绘制高频数据
    t_high = t  # 与中频使用相同的时间轴
    
    # 绘制不同频率成分
    high_freq_colors = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta', 'pink', 'brown', 'gray']
    high_freq_labels = [f'{i}f' for i in range(1, max_harmonics_high + 1)]
    
    for i, (key, color) in enumerate(zip(high_freq_labels, high_freq_colors)):
        harmonic = i + 1
        if f'{harmonic}z' in high_freq_data:
            ax2.plot(t_high, high_freq_data[f'{harmonic}z'], color=color, linewidth=0.8, alpha=0.6)
    
    # 绘制合成信号（真实数据）
    ax2.plot(t_high, high_freq_data['total'], color='black', linewidth=1.2, alpha=0.9)
    
    # 添加标题和标签
    ax2.set_title('"high frequency" (≥ fz) → with crowning and slope correction', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Deviation (mm)', fontsize=10)
    ax2.set_xlabel('Normalized Position', fontsize=10)
    
    # 添加频率标记
    high_freq_positions = np.linspace(0.1, 0.9, max_harmonics_high)
    high_freq_texts = [str(i) for i in range(1, max_harmonics_high + 1)]
    for pos, text in zip(high_freq_positions, high_freq_texts):
        ax2.text(pos, 0.9, text, transform=ax2.transAxes, fontsize=7, ha='center')
    
    # 添加振幅刻度
    ax2.text(0.95, 0.9, '0.001 mm', transform=ax2.transAxes, fontsize=8, ha='right', 
             bbox=dict(boxstyle='square,pad=0.3', facecolor='white', edgecolor='black', linewidth=0.8))
    
    # 添加数据标签
    if '1z' in high_freq_components:
        ax2.text(0.1, 0.8, f'A1 {high_freq_components["1z"]:.3f}', transform=ax2.transAxes, fontsize=8, ha='center')
        ax2.text(0.1, 0.75, f'f1 {teeth_count}', transform=ax2.transAxes, fontsize=8, ha='center')
    
    # 添加网格
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('gear_frequency_analysis_real_data_corrected.png', dpi=150, bbox_inches='tight')
    print("\n=== 图表生成完成 ===")
    print("齿轮频率分析图表已保存为 'gear_frequency_analysis_real_data_corrected.png'")


if __name__ == '__main__':
    plot_gear_frequency_analysis_real_data()
