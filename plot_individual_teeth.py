#!/usr/bin/env python3
"""
显示每个齿的详细视图
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from parse_mka_file import MKAParser
from klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport


def plot_individual_teeth():
    """
    显示每个齿的详细视图
    """
    # 读取MKA文件数据
    mka_file = '004-xiaoxiao1.mka'
    parser = MKAParser(mka_file)
    
    # 获取齿轮齿数
    teeth_count = parser.get_teeth_count()
    if teeth_count == 0:
        teeth_count = 26  # Fallback to 26 based on the data
    
    print(f"Gear teeth count: {teeth_count}")
    
    # 获取旋转图表数据
    combined_data = parser.get_combined_data(use_evaluation_range=True)
    
    # 创建频谱分析器
    analyzer = KlingelnbergRippleSpectrumReport()
    
    # 创建PDF报告
    output_pdf = 'individual_teeth_detail_004-xiaoxiao1_closed_curve.pdf'
    
    with PdfPages(output_pdf) as pdf:
        # 创建分析页面 - 每个齿的详细视图
        fig = plt.figure(figsize=(12, 16), dpi=200)  # 增大图表尺寸和分辨率
        fig.suptitle(f'Individual Teeth Detail View (Closed Curve) (Teeth Count: {teeth_count})', fontsize=16, fontweight='bold')
        
        # 创建子图 - 为每个数据集创建一个大图
        gs = fig.add_gridspec(4, 1, height_ratios=[1, 1, 1, 1])
        
        # 数据集颜色
        colors = ['blue', 'red', 'green', 'magenta']
        
        # 数据集标签
        datasets = [
            ('Left Profile', 'profile_left'),
            ('Right Profile', 'profile_right'),
            ('Left Flank', 'flank_left'),
            ('Right Flank', 'flank_right')
        ]
        
        for i, (title, key) in enumerate(datasets):
            if key in combined_data:
                # 提取数据
                data = combined_data[key]
                angles = [item[0] for item in data]
                values = [item[1] for item in data]
                
                if angles and values:
                    # 创建子图
                    ax = fig.add_subplot(gs[i])
                    ax.set_title(f'{title} - Individual Teeth View (Closed Curve)', fontsize=14, fontweight='bold')
                    ax.set_xlabel('Rotation Angle (degrees)', fontsize=10)
                    ax.set_ylabel('Deviation (μm)', fontsize=10)
                    ax.tick_params(axis='both', labelsize=9)
                    ax.grid(True, alpha=0.3, linestyle='--')
                    
                    # 计算每个齿的角度范围
                    angle_per_tooth = 360.0 / teeth_count
                    
                    # 为每个齿绘制单独的曲线
                    # 首先将数据按角度排序
                    sorted_data = sorted(zip(angles, values), key=lambda x: x[0])
                    sorted_angles = [item[0] for item in sorted_data]
                    sorted_values = [item[1] for item in sorted_data]
                    
                    # 按齿分组数据
                    tooth_data = {}
                    for angle, value in zip(sorted_angles, sorted_values):
                        # 计算当前角度属于哪个齿
                        tooth_num = int(angle / angle_per_tooth) + 1
                        if tooth_num not in tooth_data:
                            tooth_data[tooth_num] = {'angles': [], 'values': []}
                        tooth_data[tooth_num]['angles'].append(angle)
                        tooth_data[tooth_num]['values'].append(value)
                    
                    # 为每个齿绘制单独的曲线
                    for tooth_num, data in tooth_data.items():
                        if data['angles'] and data['values']:
                            # 绘制当前齿的曲线
                            ax.plot(data['angles'], data['values'], color=colors[i], linewidth=1.0)
                    
                    # 闭合曲线：将首尾相连
                    if len(sorted_angles) > 1:
                        # 添加连接首尾的线段
                        ax.plot([sorted_angles[-1], sorted_angles[0] + 360], [sorted_values[-1], sorted_values[0]], 
                                color=colors[i], linewidth=1.0, linestyle='--', alpha=0.7)
                    
                    # 计算并绘制最大阶次的正弦波
                    # 准备数据
                    # 闭合数据：将首尾相连，用于更准确的拟合
                    closed_values = sorted_values.copy()
                    if len(sorted_values) > 1:
                        # 添加一个点连接首尾，形成闭合曲线
                        closed_values.append(sorted_values[0])
                    values_array = np.array(closed_values)
                    
                    # 计算频谱，寻找最大阶次的正弦波
                    spectrum = analyzer._calculate_ripple_spectrum(values_array, max_harmonics=10, min_order=1, max_order=200)
                    
                    if spectrum:
                        # 找到阶次最大的正弦波
                        max_order_component = max(spectrum, key=lambda x: x['order'])
                        
                        # 计算正弦波的值
                        # 归一化角度到0-1范围
                        min_angle = np.min(sorted_angles)
                        max_angle = np.max(sorted_angles)
                        angle_range = max_angle - min_angle
                        if angle_range > 0:
                            normalized_angles = (np.array(sorted_angles) - min_angle) / angle_range
                        else:
                            normalized_angles = np.linspace(0, 1, len(sorted_angles))
                        
                        # 计算正弦波
                        amp = max_order_component['amplitude']
                        freq = max_order_component['frequency']
                        phase = max_order_component['phase']
                        offset = max_order_component['offset']
                        
                        # 使用频谱分析器的正弦函数计算值
                        sine_wave = analyzer._sin_function(normalized_angles, amp, freq, phase, offset)
                        
                        # 闭合正弦波：添加一个点连接首尾
                        closed_sorted_angles = sorted_angles.copy()
                        closed_sine_wave = sine_wave.copy()
                        if len(sorted_angles) > 1:
                            # 添加一个点连接首尾，形成闭合曲线
                            closed_sorted_angles.append(sorted_angles[0] + 360)
                            closed_sine_wave = np.append(closed_sine_wave, sine_wave[0])
                        
                        # 绘制最大阶次的正弦波
                        ax.plot(closed_sorted_angles, closed_sine_wave, color='black', linestyle='--', linewidth=1.5, 
                                label=f'Max Order Sine Wave (Order: {int(max_order_component["order"])}, Amp: {amp:.2f})')
                        
                        # 添加图例
                        ax.legend(fontsize=10, loc='upper right')
                    
                    # 添加齿的分隔线和标签
                    for tooth_num in range(1, teeth_count + 1):
                        # 计算每个齿的起始角度
                        start_angle = (tooth_num - 1) * angle_per_tooth
                        # 添加垂直分隔线
                        ax.axvline(x=start_angle, color='gray', linestyle='--', alpha=0.5, linewidth=0.5)
                        # 添加齿号标签
                        ax.text(start_angle + angle_per_tooth / 2, ax.get_ylim()[1] * 0.95, 
                                f'Tooth {tooth_num}', ha='center', va='top', 
                                fontsize=7, rotation=90, alpha=0.7)
                    
                    # 设置x轴范围为0-370度，以便显示闭合的曲线
                    ax.set_xlim(0, 370)
                    # 隐藏右侧和顶部边框
                    ax.spines['right'].set_visible(False)
                    ax.spines['top'].set_visible(False)
                else:
                    # 无数据时的处理
                    ax = fig.add_subplot(gs[i])
                    ax.set_title(f'{title} - Individual Teeth View', fontsize=14, fontweight='bold')
                    ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                    ax.set_xlabel('Rotation Angle (degrees)', fontsize=10)
                    ax.set_ylabel('Deviation (μm)', fontsize=10)
            else:
                # 无数据时的处理
                ax = fig.add_subplot(gs[i])
                ax.set_title(f'{title} - Individual Teeth View', fontsize=14, fontweight='bold')
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                ax.set_xlabel('Rotation Angle (degrees)', fontsize=10)
                ax.set_ylabel('Deviation (μm)', fontsize=10)
        
        # 调整布局
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print(f"Individual teeth detail view completed. Results saved to: {output_pdf}")


if __name__ == '__main__':
    plot_individual_teeth()
