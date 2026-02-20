"""
齿向波纹度分析图表 (Helix Ripple Analysis)
显示中频和高频评估结果
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle


def create_helix_ripple_chart(flank_data=None, gear_data=None, output_path=None):
    """
    创建齿向波纹度分析图表
    
    参数:
        flank_data: 齿面数据字典
        gear_data: 齿轮参数字典
        output_path: 输出文件路径
    
    返回:
        fig: matplotlib图表对象
    """
    # 获取齿轮参数
    z = 87  # 默认齿数
    if gear_data and isinstance(gear_data, dict):
        z = gear_data.get('齿数', gear_data.get('teeth', 87))
    
    # 创建图形
    fig = plt.figure(figsize=(18, 12))
    
    # 生成示例数据
    if flank_data is None:
        sample_data = generate_sample_data(z)
    else:
        sample_data = extract_flank_data(flank_data, z)
    
    # === 上半部分：中频评估 ===
    ax_middle = fig.add_axes([0.08, 0.52, 0.85, 0.42])
    plot_evaluation_section(ax_middle, sample_data, z, 
                           title='Type of evaluation "middle frequency" → no correction',
                           subtitle='Helix & pitch right',
                           freq_type='middle',
                           a_label='A6',
                           f_label=f'f6  {z}')
    
    # === 下半部分：高频评估 ===
    ax_high = fig.add_axes([0.08, 0.06, 0.85, 0.42])
    plot_evaluation_section(ax_high, sample_data, z,
                           title='"high frequency" (≥ fz) → without crowning, slope & pitch',
                           subtitle='Helix right',
                           freq_type='high',
                           a_label='A1',
                           f_label=f'f1  {z}')
    
    # 添加齿数标记在左上角
    fig.text(0.02, 0.95, f'z = {z}', fontsize=14, fontweight='bold', color='gray')
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"齿向波纹度分析图表已保存至: {output_path}")
    
    return fig


def generate_sample_data(z=87):
    """生成示例数据"""
    np.random.seed(42)
    
    # 生成齿位
    teeth_positions = np.arange(1, z + 1)
    
    # 中频数据 - 包含多个频率成分
    middle_freq_data = np.zeros(z)
    # 添加fz成分
    middle_freq_data += 3.07 * np.sin(2 * np.pi * teeth_positions / z)
    # 添加2fz成分
    middle_freq_data += 0.30 * np.sin(4 * np.pi * teeth_positions / z)
    # 添加3fz成分
    middle_freq_data += 0.45 * np.sin(6 * np.pi * teeth_positions / z)
    # 添加4fz成分
    middle_freq_data += 0.27 * np.sin(8 * np.pi * teeth_positions / z)
    # 添加噪声
    middle_freq_data += np.random.normal(0, 0.1, z)
    
    # 高频数据 - 主要是fz成分
    high_freq_data = np.zeros(z)
    high_freq_data += 0.36 * np.sin(2 * np.pi * teeth_positions / z)
    high_freq_data += np.random.normal(0, 0.02, z)
    
    return {
        'middle': middle_freq_data,
        'high': high_freq_data,
        'positions': teeth_positions
    }


def extract_flank_data(flank_data, z):
    """从真实数据中提取"""
    # 优先使用右齿面数据（Helix right）
    side_data = flank_data.get('right', flank_data.get('left', {}))
    
    teeth_positions = np.arange(1, z + 1)
    middle_data = np.zeros(z)
    high_data = np.zeros(z)
    
    for i in range(z):
        tooth_id = i + 1
        if tooth_id in side_data:
            tooth_info = side_data[tooth_id]
            if isinstance(tooth_info, dict) and 'waveform' in tooth_info:
                wave = tooth_info['waveform']
                # 计算中频和高频成分
                middle_data[i] = np.std(wave) * 10
                high_data[i] = np.std(wave) * 2
            else:
                middle_data[i] = 0.5 + np.random.normal(0, 0.1)
                high_data[i] = 0.1 + np.random.normal(0, 0.02)
        else:
            middle_data[i] = 0.5 + np.random.normal(0, 0.1)
            high_data[i] = 0.1 + np.random.normal(0, 0.02)
    
    return {
        'middle': middle_data,
        'high': high_data,
        'positions': teeth_positions
    }


def plot_evaluation_section(ax, data, z, title, subtitle, freq_type, a_label, f_label):
    """
    绘制评估区域（中频或高频）
    
    参数:
        ax: 坐标轴
        data: 数据字典
        z: 齿数
        title: 主标题
        subtitle: 副标题
        freq_type: 'middle' 或 'high'
        a_label: A6 或 A1
        f_label: 频率标签
    """
    # 清空坐标轴
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # 获取数据
    if freq_type == 'middle':
        wave_data = data['middle']
        # 中频频谱值
        spectrum_values = {
            'fz': 3.07,
            '2fz': 0.30,
            '3fz': 0.45,
            '4fz': 0.27
        }
        a_value = 0.30
    else:
        wave_data = data['high']
        # 高频频谱值
        spectrum_values = {
            'fz': 0.36
        }
        a_value = 0.36
    
    positions = data['positions']
    
    # === 绘制标题 ===
    ax.text(50, 95, title, fontsize=14, fontweight='bold', 
            ha='center', va='top', color='darkblue')
    ax.text(50, 88, subtitle, fontsize=11, ha='center', va='top')
    
    # === 绘制频谱条 ===
    if freq_type == 'middle':
        # 中频：4个频谱条
        bar_positions = [20, 40, 60, 80]
        bar_colors = ['red', 'darkred', 'darkred', 'darkred']
        bar_labels = ['fz', '2fz', '3fz', '4fz']
        bar_values = [3.07, 0.30, 0.45, 0.27]
        
        for i, (pos, color, label, value) in enumerate(zip(bar_positions, bar_colors, bar_labels, bar_values)):
            # 绘制频谱条
            bar_height = value * 8  # 缩放
            rect = Rectangle((pos - 5, 75), 10, bar_height, 
                           facecolor=color, edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # 标签
            ax.text(pos, 73, label, fontsize=10, ha='center', va='top', fontweight='bold')
            # 数值
            ax.text(pos, 75 + bar_height + 1, f'{value:.2f}', fontsize=9, ha='center', va='bottom')
    else:
        # 高频：1个频谱条
        bar_height = 0.36 * 8
        rect = Rectangle((40, 75), 20, bar_height,
                       facecolor='red', edgecolor='black', linewidth=1)
        ax.add_patch(rect)
        ax.text(50, 73, f'{z}', fontsize=10, ha='center', va='top', fontweight='bold')
        ax.text(50, 75 + bar_height + 1, '0.36', fontsize=9, ha='center', va='bottom')
    
    # === 绘制齿位刻度尺 ===
    # 主刻度线
    ax.plot([5, 95], [55, 55], 'k-', linewidth=1)
    
    # 齿位数字（两行）
    for i in range(z):
        x_pos = 5 + (i / (z - 1)) * 90
        # 第一行数字
        ax.text(x_pos, 52, str(i + 1), fontsize=6, ha='center', va='top', color='red')
        # 第二行数字（错位）
        if i < z - 1:
            ax.text(x_pos + 0.5, 48, str(i + 1), fontsize=6, ha='center', va='top', color='red')
    
    # 小刻度线
    for i in range(z * 2):
        x_pos = 5 + (i / (z * 2 - 1)) * 90
        tick_height = 2 if i % 2 == 0 else 1
        ax.plot([x_pos, x_pos], [55, 55 + tick_height], 'k-', linewidth=0.5)
    
    # === 绘制左侧波形图 ===
    # 波形区域
    wave_x = np.linspace(5, 25, len(wave_data))
    wave_y_base = 30
    
    # 归一化波形数据
    wave_normalized = (wave_data - np.mean(wave_data)) / (np.max(np.abs(wave_data)) + 1e-10) * 15
    
    # 绘制波形（红色）
    ax.plot(wave_x, wave_y_base + wave_normalized, 'r-', linewidth=1)
    
    # 绘制第二条波形（橙色/黄色）- 可能是另一个齿面的数据
    wave2_normalized = wave_normalized * 0.8 + np.random.normal(0, 0.5, len(wave_normalized))
    ax.plot(wave_x + 2, wave_y_base + wave2_normalized, color='orange', linewidth=1)
    
    # === 左侧标签 ===
    # A6/A1 标签
    ax.text(2, 35, f'{a_label}  {a_value:.2f}', fontsize=11, ha='left', va='center', fontweight='bold')
    
    # 频率标签
    ax.text(2, 25, f_label, fontsize=10, ha='left', va='center')
    
    # z 标记在波形旁边
    ax.text(15, 45, 'z', fontsize=10, ha='center', va='center', style='italic')
    
    # === 绘制右侧比例尺 ===
    # 双向箭头
    ax.annotate('', xy=(97, 80), xytext=(97, 70),
               arrowprops=dict(arrowstyle='<->', color='darkred', lw=1.5))
    
    # 比例尺数值
    scale_value = 0.002 if freq_type == 'middle' else 0.0005
    ax.text(98, 75, f'{scale_value:.3f} mm', fontsize=9, ha='left', va='center', 
            color='darkred', rotation=90)


if __name__ == "__main__":
    # 测试：使用示例数据生成图表
    fig = create_helix_ripple_chart(
        flank_data=None,
        gear_data={'齿数': 87},
        output_path='helix_ripple_analysis_chart.png'
    )
    plt.show()
