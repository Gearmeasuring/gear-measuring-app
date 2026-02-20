"""
波纹度频谱分析图
基于MKA文件数据生成频谱分析图表
显示齿形和齿向的谐波频谱
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contact_pattern_chart_mka import extract_data_from_mka


def create_spectrum_analysis_chart(file_path, output_path=None, max_harmonics=6):
    """
    创建波纹度频谱分析图

    参数:
        file_path: MKA文件路径
        output_path: 输出文件路径
        max_harmonics: 显示的最大谐波次数

    返回:
        fig: matplotlib图形对象
    """

    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 从MKA文件提取数据
    print(f"正在读取MKA文件: {file_path}")
    gear_data, profile_data, pitch_data = extract_data_from_mka(file_path)

    if not gear_data:
        print("错误: 无法从MKA文件提取齿轮数据")
        return None

    z = gear_data.get('teeth', 0)
    if z <= 0:
        print("错误: 无法获取齿数")
        return None

    print(f"齿轮参数: 齿数 z={z}")

    # 创建图形 - 4行布局
    fig = plt.figure(figsize=(16, 12))
    fig.subplots_adjust(left=0.08, right=0.92, top=0.90, bottom=0.08, hspace=0.35)

    # 分析齿形数据（Profile）
    # 左齿面
    ax1 = fig.add_subplot(4, 1, 2)
    spectrum_left = analyze_spectrum(profile_data.get('left', {}), z, '齿形左齿面')
    plot_spectrum(ax1, spectrum_left, z, max_harmonics, '齿形左齿面 (Profile left)')

    # 右齿面
    ax2 = fig.add_subplot(4, 1, 1)
    spectrum_right = analyze_spectrum(profile_data.get('right', {}), z, '齿形右齿面')
    plot_spectrum(ax2, spectrum_right, z, max_harmonics, '齿形右齿面 (Profile right)')

    # 注：MKA文件通常不包含齿向(Helix)数据，这里用轮廓数据模拟或留空
    # 如果有齿向数据，可以用同样的方法分析

    # 添加表格数据
    ax_table_left = fig.add_subplot(4, 1, 3)
    ax_table_right = fig.add_subplot(4, 1, 4)
    plot_spectrum_table(ax_table_left, ax_table_right, spectrum_left, spectrum_right, max_harmonics)

    # 添加总标题
    file_name = os.path.basename(file_path)
    fig.suptitle(f'波纹度频谱分析 (WAV)\n文件: {file_name} | 齿数 z={z}',
                 fontsize=14, fontweight='bold', y=0.98)

    # 保存或返回
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"图表已保存到: {output_path}")

    return fig


def analyze_spectrum(profile_data, z, label):
    """
    对轮廓数据进行频谱分析

    返回:
        {
            'harmonics': {1: amp1, 2: amp2, ...},  # 各阶谐波幅值
            'orders': [1, 2, 3, ...],  # 谐波阶数
            'amplitudes': [amp1, amp2, ...],  # 对应幅值
            'frequencies': [freq1, freq2, ...]  # 对应频率
        }
    """

    if not profile_data or len(profile_data) == 0:
        print(f"  {label}: 无数据")
        return None

    # 收集所有齿的数据
    all_data = []
    tooth_ids = sorted([tid for tid in profile_data.keys() if isinstance(tid, int)])

    for tooth_id in tooth_ids:
        values = profile_data[tooth_id]
        if isinstance(values, (list, np.ndarray)) and len(values) > 0:
            all_data.extend(values)

    if len(all_data) == 0:
        print(f"  {label}: 数据为空")
        return None

    print(f"  {label}: {len(tooth_ids)}个齿, 共{len(all_data)}个数据点")

    # 进行FFT分析
    n = len(all_data)
    yf = fft(all_data)
    xf = fftfreq(n, 1)  # 假设采样间隔为1

    # 只取正频率部分
    positive_freq_idx = xf > 0
    xf_pos = xf[positive_freq_idx]
    yf_pos = np.abs(yf[positive_freq_idx])

    # 计算各阶谐波（基于齿数z的整数倍）
    harmonics = {}

    # 基频对应一个齿距的周期
    # 在FFT结果中，基频 = 1/n（每个数据点对应的角度）
    # 我们需要找到对应于z, 2z, 3z...的频率成分

    # 总数据点数对应的角度 = 2π * (测量的齿数 / 总齿数)
    # 简化处理：假设测量了所有齿，基频对应齿数z

    for harmonic_order in range(1, 11):  # 计算前10阶
        # 目标频率 = harmonic_order * (z / n)
        target_freq = harmonic_order * z / n

        # 找到最接近的频率索引
        idx = np.argmin(np.abs(xf_pos - target_freq))
        freq = xf_pos[idx]
        amp = yf_pos[idx] / n * 2  # 归一化幅值

        harmonics[harmonic_order] = amp

    # 排序并返回
    orders = sorted(harmonics.keys())
    amplitudes = [harmonics[o] for o in orders]

    return {
        'harmonics': harmonics,
        'orders': orders,
        'amplitudes': amplitudes,
        'tooth_count': len(tooth_ids)
    }


def plot_spectrum(ax, spectrum_data, z, max_harmonics, title):
    """绘制频谱图"""

    ax.set_facecolor('#fafafa')

    if not spectrum_data:
        ax.text(0.5, 0.5, '无数据', ha='center', va='center',
                transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=11, fontweight='bold')
        return

    orders = spectrum_data['orders'][:max_harmonics]
    amplitudes = spectrum_data['amplitudes'][:max_harmonics]

    # 绘制柱状图
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    bars = ax.bar(orders, amplitudes, color=[colors[i % len(colors)] for i in range(len(orders))],
                  alpha=0.7, edgecolor='black', linewidth=0.5)

    # 添加数值标签
    for i, (order, amp) in enumerate(zip(orders, amplitudes)):
        # 谐波次数标签（如 1ZE, 2ZE）
        freq_label = f'{order}ZE'
        # 在柱子上方显示幅值
        ax.text(order, amp + max(amplitudes) * 0.02, f'{amp:.2f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
        # 在柱子下方显示谐波次数
        ax.text(order, -max(amplitudes) * 0.05, freq_label,
                ha='center', va='top', fontsize=8, color='red')

    # 添加网格线
    ax.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)

    # 设置坐标轴
    ax.set_xlabel('谐波次数', fontsize=10)
    ax.set_ylabel('幅值 (μm)', fontsize=10)
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)

    # 设置X轴刻度
    ax.set_xticks(orders)
    ax.set_xticklabels([f'{o}' for o in orders])

    # 设置Y轴范围
    y_max = max(amplitudes) * 1.2
    ax.set_ylim(-y_max * 0.1, y_max)

    # 添加零线
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)


def plot_spectrum_table(ax_left, ax_right, spectrum_left, spectrum_right, max_harmonics):
    """绘制频谱数据表格"""

    # 隐藏坐标轴
    ax_left.axis('off')
    ax_right.axis('off')

    # 准备表格数据
    if spectrum_left:
        orders_l = spectrum_left['orders'][:max_harmonics]
        amps_l = spectrum_left['amplitudes'][:max_harmonics]
        # 计算阶数（谐波次数 × 齿数）
        z = max(orders_l)  # 这里简化处理
        freqs_l = [o * z for o in orders_l]
    else:
        orders_l = []
        amps_l = []
        freqs_l = []

    if spectrum_right:
        orders_r = spectrum_right['orders'][:max_harmonics]
        amps_r = spectrum_right['amplitudes'][:max_harmonics]
        z = max(orders_r)
        freqs_r = [o * z for o in orders_r]
    else:
        orders_r = []
        amps_r = []
        freqs_r = []

    # 左齿面表格
    if orders_l:
        table_data_left = [['阶数', '幅值(μm)', '阶数(O)']]
        for o, amp, freq in zip(orders_l, amps_l, freqs_l):
            table_data_left.append([f'{o}ZE', f'{amp:.2f}', str(freq)])

        table_left = ax_left.table(cellText=table_data_left,
                                   loc='center',
                                   cellLoc='center',
                                   colWidths=[0.2, 0.3, 0.3])
        table_left.auto_set_font_size(False)
        table_left.set_fontsize(9)
        table_left.scale(1, 1.5)

        # 设置表头样式
        for i in range(3):
            table_left[(0, i)].set_facecolor('#4472C4')
            table_left[(0, i)].set_text_props(weight='bold', color='white')

        ax_left.set_title('Profile left', fontsize=10, fontweight='bold', pad=10)

    # 右齿面表格
    if orders_r:
        table_data_right = [['阶数', '幅值(μm)', '阶数(O)']]
        for o, amp, freq in zip(orders_r, amps_r, freqs_r):
            table_data_right.append([f'{o}ZE', f'{amp:.2f}', str(freq)])

        table_right = ax_right.table(cellText=table_data_right,
                                     loc='center',
                                     cellLoc='center',
                                     colWidths=[0.2, 0.3, 0.3])
        table_right.auto_set_font_size(False)
        table_right.set_fontsize(9)
        table_right.scale(1, 1.5)

        # 设置表头样式
        for i in range(3):
            table_right[(0, i)].set_facecolor('#4472C4')
            table_right[(0, i)].set_text_props(weight='bold', color='white')

        ax_right.set_title('Profile right', fontsize=10, fontweight='bold', pad=10)


# 测试函数
if __name__ == '__main__':
    import glob

    # 查找目录中的MKA文件
    mka_files = glob.glob('*.mka')

    if not mka_files:
        print("错误: 未找到MKA文件")
        print("请确保当前目录中有.mka文件")
        sys.exit(1)

    # 使用指定的MKA文件或第一个找到的
    target_file = '263751-018-WAV.mka'
    if target_file in mka_files:
        mka_file = target_file
    else:
        mka_file = mka_files[0]

    print(f"\n处理文件: {mka_file}")

    # 生成频谱分析图
    fig = create_spectrum_analysis_chart(
        mka_file,
        output_path='spectrum_analysis.png',
        max_harmonics=6
    )

    if fig:
        plt.show()
        print("频谱分析图生成完成！")
    else:
        print("频谱分析图生成失败")
