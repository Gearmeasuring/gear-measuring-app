"""
齿轮加工方法对比分析图表生成器
Gear Manufacturing Method Comparison Chart Generator

生成对比不同加工方法（拉削 vs 展成磨削）产生的波纹度特征图表
支持从MKA文件提取真实数据
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as path_effects
from scipy import fft
from scipy.signal import butter, filtfilt


def generate_sample_broaching_data(num_teeth=26, num_points=915):
    """生成拉削加工示例数据（噪声激励特征）"""
    np.random.seed(42)
    
    x = np.linspace(0, num_teeth, num_teeth * num_points)
    
    # 拉削特征：周期性噪声，基频为fz
    # 主要包含fz及其倍频，幅值较大
    wave = 0.015 * np.sin(2 * np.pi * x)  # 基频
    wave += 0.008 * np.sin(4 * np.pi * x)  # 2fz
    wave += 0.005 * np.sin(6 * np.pi * x)  # 3fz
    wave += 0.003 * np.random.randn(len(x))  # 噪声
    
    return wave, x


def generate_sample_grinding_data(num_teeth=26, num_points=915):
    """生成展成磨削示例数据（高频波纹特征）"""
    np.random.seed(43)
    
    x = np.linspace(0, num_teeth, num_teeth * num_points)
    
    # 磨削特征：高频波纹，频率更高但幅值较小
    wave = 0.008 * np.sin(10 * np.pi * x)  # 高频
    wave += 0.005 * np.sin(20 * np.pi * x)  # 更高频
    wave += 0.002 * np.random.randn(len(x))  # 噪声
    
    return wave, x


def calculate_manufacturing_spectrum(data, teeth_count):
    """
    计算加工方法相关的频谱
    
    Parameters:
    -----------
    data : np.ndarray
        测量数据
    teeth_count : int
        齿轮齿数
        
    Returns:
    --------
    spectrum_data : dict
        频谱数据 {阶次: 幅值}
    """
    if len(data) == 0:
        return {}
    
    data = np.array(data)
    
    # 计算FFT
    fft_result = np.fft.fft(data)
    fft_magnitude = np.abs(fft_result)
    
    n = len(data)
    frequencies = np.fft.fftfreq(n)
    
    # 转换为以齿数为基频的阶次
    orders = frequencies * n / (n / teeth_count)
    
    # 只取正频率部分
    positive_freq_idx = frequencies > 0
    orders = orders[positive_freq_idx]
    magnitudes = fft_magnitude[positive_freq_idx]
    
    # 提取主要频率成分
    spectrum_data = {}
    fz = teeth_count
    
    # 查找fz, 2fz, 3fz, 4fz附近的峰值
    for i in range(1, 5):
        target_order = i * fz
        idx_range = np.where((orders >= target_order - 2) & (orders <= target_order + 2))[0]
        if len(idx_range) > 0:
            peak_idx = idx_range[np.argmax(magnitudes[idx_range])]
            actual_order = int(round(orders[peak_idx]))
            spectrum_data[actual_order] = magnitudes[peak_idx] * 2.0 / n
    
    return spectrum_data


def process_manufacturing_data(flank_data, gear_data, method='broaching', teeth_count=26):
    """
    处理加工方法相关数据
    
    Parameters:
    -----------
    flank_data : dict
        齿向测量数据
    gear_data : dict
        齿轮基本信息
    method : str
        加工方法：'broaching'(拉削) 或 'grinding'(磨削)
    teeth_count : int
        齿数
        
    Returns:
    --------
    wave_data : np.ndarray
        波形数据
    spectrum_data : dict
        频谱数据
    x : np.ndarray
        x轴数据
    num_teeth : int
        实际测量齿数
    """
    # 获取实际齿数
    if gear_data and isinstance(gear_data, dict):
        teeth_count = gear_data.get('齿数', gear_data.get('teeth', teeth_count))
    
    # 使用齿向数据
    side = 'right'
    if flank_data and isinstance(flank_data, dict):
        if 'right' in flank_data and flank_data['right']:
            side_data = flank_data['right']
        elif 'left' in flank_data and flank_data['left']:
            side_data = flank_data['left']
        else:
            side_data = {}
    else:
        side_data = {}
    
    if not side_data:
        # 如果没有真实数据，使用示例数据
        if method == 'broaching':
            wave_data, x = generate_sample_broaching_data(num_teeth=teeth_count)
        else:
            wave_data, x = generate_sample_grinding_data(num_teeth=teeth_count)
        spectrum_data = calculate_manufacturing_spectrum(wave_data, teeth_count)
        return wave_data, spectrum_data, x, teeth_count
    
    # 处理真实数据
    measured_teeth = len(side_data)
    all_teeth_data = []
    for tooth_id in sorted(side_data.keys()):
        values = side_data[tooth_id]
        if isinstance(values, list) and len(values) > 0:
            all_teeth_data.extend(values)
    
    if len(all_teeth_data) == 0:
        if method == 'broaching':
            wave_data, x = generate_sample_broaching_data(num_teeth=measured_teeth)
        else:
            wave_data, x = generate_sample_grinding_data(num_teeth=measured_teeth)
    else:
        wave_data = np.array(all_teeth_data)
        x = np.linspace(0, measured_teeth, len(wave_data))
    
    spectrum_data = calculate_manufacturing_spectrum(wave_data, teeth_count)
    
    return wave_data, spectrum_data, x, measured_teeth


def draw_manufacturing_tooth_profile(ax, z=26, method='broaching'):
    """绘制齿形轮廓示意图（加工方法对比版本）"""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # 绘制齿形轮廓
    y_profile = np.linspace(1, 10, 100)
    
    if method == 'broaching':
        # 拉削：较光滑但有周期性波纹
        x_profile1 = 2 + 1.5 * np.sin(2 * np.pi * (y_profile - 1) / 9) + 0.05 * np.random.randn(100)
        x_profile2 = 5 + 1.5 * np.sin(2 * np.pi * (y_profile - 1) / 9 + np.pi) + 0.05 * np.random.randn(100)
    else:
        # 磨削：高频波纹
        x_profile1 = 2 + 1.5 * np.sin(2 * np.pi * (y_profile - 1) / 9) + 0.1 * np.sin(20 * np.pi * (y_profile - 1) / 9) + 0.03 * np.random.randn(100)
        x_profile2 = 5 + 1.5 * np.sin(2 * np.pi * (y_profile - 1) / 9 + np.pi) + 0.1 * np.sin(20 * np.pi * (y_profile - 1) / 9) + 0.03 * np.random.randn(100)
    
    ax.plot(x_profile1, y_profile, 'darkred', linewidth=2)
    ax.plot(x_profile2, y_profile, 'darkorange', linewidth=2)
    
    # 添加标注
    ax.text(1, 11.5, f'z = {z}', fontsize=12, fontweight='bold', color='gray')
    ax.text(0.5, 8, '1', fontsize=12, color='gray')
    ax.text(4.5, 8, 'z', fontsize=12, color='gray')
    ax.text(3, 5, '...', fontsize=14, ha='center', color='gray')


def create_manufacturing_comparison_chart(flank_data=None, gear_data=None, output_path=None):
    """
    创建齿轮加工方法对比分析图表
    
    Parameters:
    -----------
    flank_data : dict
        齿向测量数据
    gear_data : dict
        齿轮基本信息
    output_path : str
        输出文件路径
    """
    # 获取齿轮参数
    z = 26
    if gear_data and isinstance(gear_data, dict):
        z = gear_data.get('齿数', gear_data.get('teeth', 26))
    
    fig = plt.figure(figsize=(18, 12))
    
    # 使用网格布局：2行，左侧为齿形轮廓，右侧为主图表
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1], width_ratios=[0.08, 1, 0.05],
                          hspace=0.3, wspace=0.05)
    
    # ========== 上半部分：拉削加工 ==========
    # 左侧齿形轮廓
    ax_left1 = fig.add_subplot(gs[0, 0])
    draw_manufacturing_tooth_profile(ax_left1, z=z, method='broaching')
    
    # 中间主区域
    ax_main1 = fig.add_subplot(gs[0, 1])
    ax_main1.axis('off')
    
    # 标题
    ax_main1.text(0.5, 1.02, 'Internal gear made by broaching → noise stimulation',
                 ha='center', va='bottom', fontsize=14, fontweight='bold', color='darkblue',
                 transform=ax_main1.transAxes)
    
    gs_inner1 = gs[0, 1].subgridspec(3, 1, height_ratios=[0.12, 0.08, 0.8], hspace=0.02)
    
    # 处理拉削数据
    wave1, spectrum1, x1, num_teeth1 = process_manufacturing_data(
        flank_data, gear_data, method='broaching', teeth_count=z
    )
    
    # 确保有足够的齿数显示
    if num_teeth1 < 10:
        num_teeth1 = 26
    
    # 频谱图
    ax_spec1 = fig.add_subplot(gs_inner1[0])
    
    # 准备频谱数据 - 按 fz, 2fz, 3fz... 排序
    fz = z
    ordered_spectrum1 = []
    for i in range(1, 5):  # fz, 2fz, 3fz, 4fz
        order = i * fz
        if order in spectrum1:
            ordered_spectrum1.append((order, spectrum1[order]))
        else:
            # 使用默认值
            default_val = 0.97 if i == 1 else 0.5 / i
            ordered_spectrum1.append((order, default_val))
    
    orders1 = [item[0] for item in ordered_spectrum1]
    vals1 = [item[1] for item in ordered_spectrum1]
    
    colors1 = ['red' if v > 0.5 else 'lightcoral' for v in vals1]
    bars1 = ax_spec1.bar(range(len(orders1)), vals1, color=colors1, 
                        width=0.5, edgecolor='darkred', linewidth=1)
    
    # 标注数值
    for i, (bar, val) in enumerate(zip(bars1, vals1)):
        height = bar.get_height()
        ax_spec1.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                     f'{val:.2f}', ha='center', va='bottom', fontsize=8)
    
    # 设置x轴标签
    ax_spec1.set_xticks(range(len(orders1)))
    x_labels1 = [f'{order}\n{i+1}fz' if i > 0 else f'{order}\nfz' for i, order in enumerate(orders1)]
    ax_spec1.set_xticklabels(x_labels1, fontsize=8)
    
    ax_spec1.set_ylim(0, max(vals1) * 1.3 if vals1 else 1.2)
    ax_spec1.spines['top'].set_visible(False)
    ax_spec1.spines['right'].set_visible(False)
    ax_spec1.set_title('Helix right', fontsize=11, y=0.95)
    
    # 刻度标注
    ax_spec1.annotate('', xy=(1.02, 0.9), xycoords='axes fraction',
                     xytext=(1.02, 0.1), textcoords='axes fraction',
                     arrowprops=dict(arrowstyle='<->', color='darkred', lw=1.5))
    ax_spec1.text(1.06, 0.5, '0.002 mm', rotation=90, va='center', fontsize=9, color='darkred')
    
    # 分隔线
    ax_sep1 = fig.add_subplot(gs_inner1[1])
    ax_sep1.set_xlim(0, num_teeth1)
    ax_sep1.set_ylim(0, 1)
    ax_sep1.axis('off')
    ax_sep1.axhline(y=0.5, color='black', linewidth=1)
    
    # 齿位标记
    for i in range(1, num_teeth1 + 1):
        ax_sep1.plot([i, i], [0.2, 0.8], 'k-', linewidth=0.8)
        ax_sep1.text(i, 0.05, str(i), ha='center', va='top', fontsize=8, color='red')
    
    # 波形图
    ax_wave1 = fig.add_subplot(gs_inner1[2])
    
    # 绘制完整波形
    if len(wave1) > 0:
        x_wave1 = np.linspace(0, num_teeth1, len(wave1))
        # 绘制完整波形（细线）
        ax_wave1.plot(x_wave1, wave1, color='darkblue', linewidth=0.8, alpha=0.8)
        
        # 叠加显示几个代表性齿的波形（用不同颜色）
        points_per_tooth = len(wave1) // num_teeth1 if num_teeth1 > 0 else len(wave1)
        colors = ['darkred', 'darkorange', 'darkgreen']
        for i, color in enumerate(colors):
            tooth_idx = i * (num_teeth1 // 3)
            if tooth_idx < num_teeth1:
                start_idx = tooth_idx * points_per_tooth
                end_idx = (tooth_idx + 1) * points_per_tooth if tooth_idx < num_teeth1 - 1 else len(wave1)
                segment = wave1[start_idx:end_idx]
                x_segment = np.linspace(tooth_idx, tooth_idx + 1, len(segment))
                ax_wave1.plot(x_segment, segment, color=color, linewidth=1.5, alpha=0.9)
    
    # 齿分割线
    for i in range(1, num_teeth1 + 1):
        ax_wave1.axvline(x=i, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    
    ax_wave1.set_xlim(0, num_teeth1)
    y_margin1 = (np.max(np.abs(wave1)) if len(wave1) > 0 else 0.02) * 1.2
    ax_wave1.set_ylim(-y_margin1, y_margin1)
    ax_wave1.axis('off')
    
    # 左侧标注
    a1_val = vals1[0] if vals1 else 0.97
    ax_wave1.text(-0.3, y_margin1 * 0.5, f'A1  {a1_val:.2f}', fontsize=10, ha='right', va='center')
    ax_wave1.text(-0.3, -y_margin1 * 0.5, f'f 1  {z}', fontsize=10, ha='right', va='center')
    
    # 齿位数字
    for i in range(1, num_teeth1 + 1):
        ax_wave1.text(i - 0.5, y_margin1 * 0.9, str(i), ha='center', va='bottom', fontsize=8, color='red')
    
    # ========== 下半部分：展成磨削 ==========
    # 左侧齿形轮廓
    ax_left2 = fig.add_subplot(gs[1, 0])
    draw_manufacturing_tooth_profile(ax_left2, z=z, method='grinding')
    
    # 中间主区域
    ax_main2 = fig.add_subplot(gs[1, 1])
    ax_main2.axis('off')
    
    # 标题
    ax_main2.text(0.5, 1.02, 'Gear made by generation grinding → ripples of high frequency',
                 ha='center', va='bottom', fontsize=14, fontweight='bold', color='darkblue',
                 transform=ax_main2.transAxes)
    
    gs_inner2 = gs[1, 1].subgridspec(3, 1, height_ratios=[0.12, 0.08, 0.8], hspace=0.02)
    
    # 处理磨削数据
    wave2, spectrum2, x2, num_teeth2 = process_manufacturing_data(
        flank_data, gear_data, method='grinding', teeth_count=z
    )
    
    if num_teeth2 < 10:
        num_teeth2 = 26
    
    # 频谱图
    ax_spec2 = fig.add_subplot(gs_inner2[0])
    
    # 准备频谱数据
    ordered_spectrum2 = []
    for i in range(1, 5):
        order = i * fz
        if order in spectrum2:
            ordered_spectrum2.append((order, spectrum2[order]))
        else:
            default_val = 0.38 if i == 1 else 0.15 / i
            ordered_spectrum2.append((order, default_val))
    
    orders2 = [item[0] for item in ordered_spectrum2]
    vals2 = [item[1] for item in ordered_spectrum2]
    
    colors2 = ['red' if v > 0.2 else 'lightcoral' for v in vals2]
    bars2 = ax_spec2.bar(range(len(orders2)), vals2, color=colors2, 
                        width=0.5, edgecolor='darkred', linewidth=1)
    
    # 标注数值
    for i, (bar, val) in enumerate(zip(bars2, vals2)):
        height = bar.get_height()
        ax_spec2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                     f'{val:.2f}', ha='center', va='bottom', fontsize=8)
    
    # 设置x轴标签
    ax_spec2.set_xticks(range(len(orders2)))
    x_labels2 = [f'{order}\n{i+1}fz' if i > 0 else f'{order}\nfz' for i, order in enumerate(orders2)]
    ax_spec2.set_xticklabels(x_labels2, fontsize=8)
    
    ax_spec2.set_ylim(0, max(vals2) * 1.3 if vals2 else 0.5)
    ax_spec2.spines['top'].set_visible(False)
    ax_spec2.spines['right'].set_visible(False)
    ax_spec2.set_title('Helix right', fontsize=11, y=0.95)
    
    # 刻度标注
    ax_spec2.annotate('', xy=(1.02, 0.9), xycoords='axes fraction',
                     xytext=(1.02, 0.1), textcoords='axes fraction',
                     arrowprops=dict(arrowstyle='<->', color='darkred', lw=1.5))
    ax_spec2.text(1.06, 0.5, '0.001 mm', rotation=90, va='center', fontsize=9, color='darkred')
    
    # 分隔线
    ax_sep2 = fig.add_subplot(gs_inner2[1])
    ax_sep2.set_xlim(0, num_teeth2)
    ax_sep2.set_ylim(0, 1)
    ax_sep2.axis('off')
    ax_sep2.axhline(y=0.5, color='black', linewidth=1)
    
    # 齿位标记
    for i in range(1, num_teeth2 + 1):
        ax_sep2.plot([i, i], [0.2, 0.8], 'k-', linewidth=0.8)
        ax_sep2.text(i, 0.05, str(i), ha='center', va='top', fontsize=8, color='red')
    
    # 波形图
    ax_wave2 = fig.add_subplot(gs_inner2[2])
    
    # 绘制完整波形
    if len(wave2) > 0:
        x_wave2 = np.linspace(0, num_teeth2, len(wave2))
        # 绘制完整波形（细线）
        ax_wave2.plot(x_wave2, wave2, color='darkblue', linewidth=0.8, alpha=0.8)
        
        # 叠加显示几个代表性齿的波形
        points_per_tooth2 = len(wave2) // num_teeth2 if num_teeth2 > 0 else len(wave2)
        for i, color in enumerate(['darkred', 'darkorange', 'darkgreen']):
            tooth_idx = i * (num_teeth2 // 3)
            if tooth_idx < num_teeth2:
                start_idx = tooth_idx * points_per_tooth2
                end_idx = (tooth_idx + 1) * points_per_tooth2 if tooth_idx < num_teeth2 - 1 else len(wave2)
                segment = wave2[start_idx:end_idx]
                x_segment = np.linspace(tooth_idx, tooth_idx + 1, len(segment))
                ax_wave2.plot(x_segment, segment, color=color, linewidth=1.5, alpha=0.9)
    
    # 齿分割线
    for i in range(1, num_teeth2 + 1):
        ax_wave2.axvline(x=i, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    
    ax_wave2.set_xlim(0, num_teeth2)
    y_margin2 = (np.max(np.abs(wave2)) if len(wave2) > 0 else 0.01) * 1.2
    ax_wave2.set_ylim(-y_margin2, y_margin2)
    ax_wave2.axis('off')
    
    # 左侧标注
    a2_val = vals2[0] if vals2 else 0.38
    ax_wave2.text(-0.3, y_margin2 * 0.5, f'A2  {a2_val:.2f}', fontsize=10, ha='right', va='center')
    ax_wave2.text(-0.3, -y_margin2 * 0.5, f'f 2  {z}', fontsize=10, ha='right', va='center')
    
    # 齿位数字
    for i in range(1, num_teeth2 + 1):
        ax_wave2.text(i - 0.5, y_margin2 * 0.9, str(i), ha='center', va='bottom', fontsize=8, color='red')
    
    plt.subplots_adjust(left=0.05, right=0.92, top=0.95, bottom=0.03)
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"加工方法对比图表已保存至: {output_path}")
    
    return fig


if __name__ == "__main__":
    # 测试：使用示例数据生成图表
    fig = create_manufacturing_comparison_chart(
        flank_data=None,
        gear_data=None,
        output_path="manufacturing_comparison_chart.png"
    )
    
    plt.show()
